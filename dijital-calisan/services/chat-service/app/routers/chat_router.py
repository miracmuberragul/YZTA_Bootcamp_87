import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.auth import AuthContext, get_auth_context, require_admin
from app.database import SessionLocal
from app.schemas.chat_schema import (
    AnalyticsSummary, ChatRequest, ChatResponse, ConversationDetail,
    ConversationMessage, ConversationSummary,
)
from app.services.chat_service import answer_question

router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post("/chat/ask", response_model=ChatResponse)
def ask(payload: ChatRequest, auth: AuthContext = Depends(get_auth_context)):
    try:
        return answer_question(
            payload.question, auth.company_id, auth.user_id, payload.conversation_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/chat/conversations", response_model=list[ConversationSummary])
def conversations(auth: AuthContext = Depends(get_auth_context)):
    with SessionLocal() as db:
        rows = db.execute(text("""
            SELECT id,title,created_at,updated_at FROM conversations
            WHERE company_id=:company AND user_id=:user
            ORDER BY updated_at DESC LIMIT 50
        """), {"company": auth.company_id, "user": auth.user_id}).all()
    return [ConversationSummary(id=r[0], title=r[1], created_at=r[2], updated_at=r[3]) for r in rows]


@router.get("/chat/conversations/{conversation_id}", response_model=ConversationDetail)
def conversation(conversation_id: uuid.UUID, auth: AuthContext = Depends(get_auth_context)):
    with SessionLocal() as db:
        row = db.execute(text("""
            SELECT id,title,created_at,updated_at FROM conversations
            WHERE id=:id AND company_id=:company AND user_id=:user
        """), {"id": conversation_id, "company": auth.company_id, "user": auth.user_id}).first()
        if row is None:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı.")
        messages = db.execute(text("""
            SELECT id,role::text,content,created_at FROM messages
            WHERE conversation_id=:id ORDER BY created_at
        """), {"id": conversation_id}).all()
    return ConversationDetail(
        id=row[0], title=row[1], created_at=row[2], updated_at=row[3],
        messages=[ConversationMessage(id=m[0], role=m[1], content=m[2], created_at=m[3]) for m in messages],
    )


@router.delete("/chat/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: uuid.UUID, auth: AuthContext = Depends(get_auth_context)):
    with SessionLocal.begin() as db:
        result = db.execute(text("""
            DELETE FROM conversations WHERE id=:id AND company_id=:company AND user_id=:user
        """), {"id": conversation_id, "company": auth.company_id, "user": auth.user_id})
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Konuşma bulunamadı.")


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics(auth: AuthContext = Depends(require_admin)):
    with SessionLocal() as db:
        documents = db.execute(text("""
            SELECT count(*), count(*) FILTER(WHERE status='processed'),
                   count(*) FILTER(WHERE status='failed')
            FROM documents WHERE company_id=:company AND status<>'deleted'
        """), {"company": auth.company_id}).one()
        active_users = db.execute(text(
            "SELECT count(*) FROM users WHERE company_id=:company AND is_active=true"
        ), {"company": auth.company_id}).scalar_one()
        categories = db.execute(text(
            "SELECT count(*) FROM categories WHERE company_id=:company"
        ), {"company": auth.company_id}).scalar_one()
        questions = db.execute(text("""
            SELECT count(*), count(*) FILTER(WHERE created_at>=date_trunc('week',now())),
                   coalesce(avg(duration_ms),0)
            FROM usage_events WHERE company_id=:company AND event_type='question_answered'
        """), {"company": auth.company_id}).one()
        daily = db.execute(text("""
            SELECT day::date, count(e.id)
            FROM generate_series(current_date-6,current_date,interval '1 day') day
            LEFT JOIN usage_events e ON e.company_id=:company
              AND e.event_type='question_answered' AND e.created_at>=day
              AND e.created_at<day+interval '1 day'
            GROUP BY day ORDER BY day
        """), {"company": auth.company_id}).all()
        top = db.execute(text("""
            SELECT metadata->>'top_document',count(*) FROM usage_events
            WHERE company_id=:company AND metadata->>'top_document' IS NOT NULL
            GROUP BY metadata->>'top_document' ORDER BY count(*) DESC LIMIT 5
        """), {"company": auth.company_id}).all()
    return AnalyticsSummary(
        total_documents=documents[0], processed_documents=documents[1],
        failed_documents=documents[2], active_users=active_users,
        category_count=categories, total_questions=questions[0],
        questions_this_week=questions[1], average_response_ms=round(questions[2]),
        daily_questions=[{"date": row[0], "count": row[1]} for row in daily],
        top_documents=[{"name": row[0], "count": row[1]} for row in top],
    )
