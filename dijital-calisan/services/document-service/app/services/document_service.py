import math
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import AuthContext
from app.config import INGESTION_SERVICE_URL, INTERNAL_API_KEY
from app.models.document import Document, DocumentCategory, DocumentStatus
from app.schemas.document_schema import DocumentListResponse, UploadResponse
from app.services.storage_service import delete_file, store_upload


def _tenant_document(db: Session, document_id: uuid.UUID, company_id: uuid.UUID, include_deleted: bool = False) -> Document:
    query = select(Document).where(Document.id == document_id, Document.company_id == company_id)
    if not include_deleted:
        query = query.where(Document.status != DocumentStatus.deleted)
    document = db.scalar(query)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doküman bulunamadı.")
    return document


async def _create_ingestion_job(document: Document) -> uuid.UUID:
    payload = {
        "document_id": str(document.id),
        "company_id": str(document.company_id),
        "storage_key": document.storage_path,
        "checksum_sha256": document.checksum_sha256,
        "idempotency_key": f"upload:{document.id}",
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{INGESTION_SERVICE_URL}/internal/v1/ingestion/jobs",
                json=payload,
                headers={"X-Internal-API-Key": INTERNAL_API_KEY},
            )
            response.raise_for_status()
            return uuid.UUID(response.json()["id"])
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Doküman kaydedildi ancak işleme kuyruğuna alınamadı. Tekrar deneyin.") from exc


async def _trigger_ingestion_job(job_id: uuid.UUID) -> None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{INGESTION_SERVICE_URL}/internal/v1/ingestion/jobs/{job_id}/process",
                headers={"X-Internal-API-Key": INTERNAL_API_KEY},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Doküman kuyruğa alındı ancak işleme başlatılamadı.") from exc


async def upload_document(
    db: Session,
    auth: AuthContext,
    upload: UploadFile,
    category: DocumentCategory,
    display_name: str | None,
) -> UploadResponse:
    document_id = uuid.uuid4()
    stored = await store_upload(upload, auth.company_id, document_id)
    existing = db.scalar(
        select(Document).where(
            Document.company_id == auth.company_id,
            Document.checksum_sha256 == stored.checksum_sha256,
            Document.status != DocumentStatus.deleted,
        )
    )
    if existing is not None:
        delete_file(stored.storage_key)
        if existing.status == DocumentStatus.uploaded:
            try:
                job_id = await _create_ingestion_job(existing)
                existing.status = DocumentStatus.queued
                existing.processing_error_code = None
                existing.processing_error_message = None
                db.commit()
                await _trigger_ingestion_job(job_id)
            except HTTPException:
                pass
        return UploadResponse(
            document_id=existing.id,
            status=existing.status,
            status_url=f"/api/v1/documents/{existing.id}",
            duplicate=True,
        )

    document = Document(
        id=document_id,
        company_id=auth.company_id,
        uploaded_by=auth.user_id,
        original_filename=stored.original_filename,
        display_name=((display_name or "").strip() or stored.original_filename)[:255],
        storage_path=stored.storage_key,
        mime_type=stored.mime_type,
        file_size_bytes=stored.file_size_bytes,
        checksum_sha256=stored.checksum_sha256,
        category=category,
        status=DocumentStatus.uploaded,
    )
    db.add(document)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        delete_file(stored.storage_key)
        existing = db.scalar(select(Document).where(
            Document.company_id == auth.company_id,
            Document.checksum_sha256 == stored.checksum_sha256,
            Document.status != DocumentStatus.deleted,
        ))
        if existing is None:
            raise
        return UploadResponse(document_id=existing.id, status=existing.status, status_url=f"/api/v1/documents/{existing.id}", duplicate=True)

    try:
        job_id = await _create_ingestion_job(document)
        document.status = DocumentStatus.queued
        document.processing_error_code = None
        document.processing_error_message = None
        db.commit()
        await _trigger_ingestion_job(job_id)
    except HTTPException:
        document.status = DocumentStatus.failed
        document.processing_error_code = "INGESTION_UNAVAILABLE"
        document.processing_error_message = "İşleme servisine ulaşılamadı veya iş başlatılamadı. Tekrar deneyebilirsiniz."
        db.commit()

    return UploadResponse(document_id=document.id, status=document.status, status_url=f"/api/v1/documents/{document.id}")


def list_documents(
    db: Session,
    company_id: uuid.UUID,
    page: int,
    page_size: int,
    document_status: DocumentStatus | None,
    category: DocumentCategory | None,
) -> DocumentListResponse:
    filters = [Document.company_id == company_id, Document.status != DocumentStatus.deleted]
    if document_status is not None:
        filters.append(Document.status == document_status)
    if category is not None:
        filters.append(Document.category == category)
    total = db.scalar(select(func.count()).select_from(Document).where(*filters)) or 0
    items = list(db.scalars(
        select(Document).where(*filters).order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ))
    return DocumentListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size),
    )


def retry_ingestion(db: Session, auth: AuthContext, document_id: uuid.UUID) -> Document:
    document = _tenant_document(db, document_id, auth.company_id)
    if document.status not in {DocumentStatus.uploaded, DocumentStatus.failed}:
        raise HTTPException(status_code=409, detail="Yalnızca başarısız veya kuyruğa alınamamış doküman tekrar denenebilir.")
    # A retry gets a new idempotency key while repeated initial uploads keep the stable upload key.
    payload = {
        "document_id": str(document.id), "company_id": str(document.company_id),
        "storage_key": document.storage_path, "checksum_sha256": document.checksum_sha256,
        "idempotency_key": f"retry:{document.id}:{uuid.uuid4()}",
    }
    try:
        response = httpx.post(f"{INGESTION_SERVICE_URL}/internal/v1/ingestion/jobs", json=payload, headers={"X-Internal-API-Key": INTERNAL_API_KEY}, timeout=5.0)
        response.raise_for_status()
        job_id = uuid.UUID(response.json()["id"])
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="İşleme servisine ulaşılamadı.") from exc
    document.status = DocumentStatus.queued
    document.processing_error_code = None
    document.processing_error_message = None
    db.commit()
    try:
        response = httpx.post(
            f"{INGESTION_SERVICE_URL}/internal/v1/ingestion/jobs/{job_id}/process",
            headers={"X-Internal-API-Key": INTERNAL_API_KEY},
            timeout=5.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        document.status = DocumentStatus.failed
        document.processing_error_code = "INGESTION_UNAVAILABLE"
        document.processing_error_message = "İşleme işi başlatılamadı. Tekrar deneyebilirsiniz."
        db.commit()
        raise HTTPException(status_code=503, detail="İşleme işi başlatılamadı.") from exc
    return document


def delete_document(db: Session, auth: AuthContext, document_id: uuid.UUID) -> Document:
    document = _tenant_document(db, document_id, auth.company_id, include_deleted=True)
    if document.status == DocumentStatus.deleted:
        return document
    document.status = DocumentStatus.deleting
    db.commit()
    try:
        response = httpx.delete(
            f"{INGESTION_SERVICE_URL}/internal/v1/ingestion/documents/{document.id}",
            params={"company_id": str(auth.company_id)},
            headers={"X-Internal-API-Key": INTERNAL_API_KEY},
            timeout=5.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Doküman silme işlemi tamamlanamadı; tekrar deneyin.") from exc
    delete_file(document.storage_path)
    document.status = DocumentStatus.deleted
    document.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return document


get_document = _tenant_document
