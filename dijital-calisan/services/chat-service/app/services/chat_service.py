import time
import uuid

from sqlalchemy import text

from app.config import RETRIEVAL_DEFAULT_LIMIT
from app.database import SessionLocal
from app.schemas.chat_schema import ChatResponse
from app.services.llm_service import answer
from app.services.retrieval_service import retrieve


def answer_question(question: str, company_id, user_id, conversation_id=None) -> ChatResponse:
    started = time.perf_counter()
    with SessionLocal() as db:
        if conversation_id is not None:
            owned = db.execute(
                text("SELECT 1 FROM conversations WHERE id=:id AND company_id=:company AND user_id=:user"),
                {"id": conversation_id, "company": company_id, "user": user_id},
            ).first()
            if owned is None:
                raise ValueError("Konuşma bulunamadı.")
        else:
            conversation_id = uuid.uuid4()
            db.execute(
                text("INSERT INTO conversations(id,company_id,user_id,title) VALUES(:id,:company,:user,:title)"),
                {"id": conversation_id, "company": company_id, "user": user_id, "title": question[:80]},
            )
            db.commit()
        history = [
            {"role": row[0], "content": row[1]}
            for row in reversed(db.execute(
                text("SELECT role::text,content FROM messages WHERE conversation_id=:id ORDER BY created_at DESC LIMIT 6"),
                {"id": conversation_id},
            ).all())
        ]
        setting = db.execute(
            text("SELECT retrieval_limit,min_similarity,system_prompt FROM company_settings WHERE company_id=:id"),
            {"id": company_id},
        ).first()
    limit, threshold, system_prompt = setting if setting else (RETRIEVAL_DEFAULT_LIMIT, 0.25, None)
    sources = retrieve(question, company_id, limit, threshold)
    response_text = answer(question, sources, history, system_prompt)
    with SessionLocal.begin() as db:
        user_message_id, assistant_message_id = uuid.uuid4(), uuid.uuid4()
        db.execute(text("""
            INSERT INTO messages(id,conversation_id,company_id,role,content)
            VALUES(:id,:conversation,:company,'user',:content)
        """), {"id": user_message_id, "conversation": conversation_id, "company": company_id, "content": question})
        db.execute(text("""
            INSERT INTO messages(id,conversation_id,company_id,role,content,response_time_ms)
            VALUES(:id,:conversation,:company,'assistant',:content,:duration)
        """), {
            "id": assistant_message_id, "conversation": conversation_id, "company": company_id,
            "content": response_text, "duration": round((time.perf_counter() - started) * 1000),
        })
        for source in sources:
            db.execute(text("""
                INSERT INTO message_sources
                    (id,message_id,chunk_id,document_id,similarity_score,excerpt_text)
                VALUES(:id,:message,:chunk,:document,:similarity,:excerpt)
            """), {
                "id": uuid.uuid4(), "message": assistant_message_id, "chunk": source.chunk_id,
                "document": source.document_id, "similarity": source.similarity,
                "excerpt": source.content[:1000],
            })
        db.execute(text("UPDATE conversations SET updated_at=now() WHERE id=:id"), {"id": conversation_id})
        db.execute(text("""
            INSERT INTO usage_events(company_id,user_id,event_type,metadata,duration_ms)
            VALUES(:company,:user,'question_answered',CAST(:metadata AS jsonb),:duration)
        """), {
            "company": company_id, "user": user_id,
            "metadata": '{"top_document":' + (
                '"' + sources[0].document_name.replace('"', '\\"') + '"' if sources else "null"
            ) + "}",
            "duration": round((time.perf_counter() - started) * 1000),
        })
    return ChatResponse(
        question=question, answer=response_text,
        conversation_id=conversation_id, sources=sources,
    )
