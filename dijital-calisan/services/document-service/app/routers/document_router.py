import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_auth_context, require_admin
from app.database import get_db
from app.models.document import DocumentCategory, DocumentStatus
from app.schemas.document_schema import DeleteResponse, DocumentListResponse, DocumentResponse, RetryResponse, UploadResponse
from app.services.document_service import delete_document, get_document, list_documents, retry_ingestion, upload_document
from app.services.storage_service import resolve_storage_key

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload(
    file: UploadFile = File(...),
    category: DocumentCategory = Form(DocumentCategory.other),
    display_name: str | None = Form(None, max_length=255),
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return await upload_document(db, auth, file, category, display_name)


@router.get("", response_model=DocumentListResponse)
def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    document_status: DocumentStatus | None = Query(None, alias="status"),
    category: DocumentCategory | None = Query(None),
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    return list_documents(db, auth.company_id, page, page_size, document_status, category)


@router.get("/{document_id}", response_model=DocumentResponse)
def detail(document_id: uuid.UUID, auth: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    return get_document(db, document_id, auth.company_id)


@router.get("/{document_id}/content")
def content(document_id: uuid.UUID, auth: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)):
    document = get_document(db, document_id, auth.company_id)
    path = resolve_storage_key(document.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Doküman dosyası bulunamadı.")
    return FileResponse(
        path,
        media_type=document.mime_type,
        filename=document.original_filename,
        content_disposition_type="attachment",
    )


@router.post("/{document_id}/retry-ingestion", response_model=RetryResponse, status_code=status.HTTP_202_ACCEPTED)
def retry(document_id: uuid.UUID, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)):
    document = retry_ingestion(db, auth, document_id)
    return RetryResponse(document_id=document.id, status=document.status)


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete(document_id: uuid.UUID, auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)):
    document = delete_document(db, auth, document_id)
    return DeleteResponse(document_id=document.id, status=document.status)
