import hmac
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import INTERNAL_API_KEY
from app.database import get_db
from app.models.chunk import DocumentChunk, IngestionJob, IngestionStatus
from app.schemas.ingestion_schema import (
    CreateIngestionJob,
    DeleteIngestionDataResponse,
    IngestionJobResponse,
    ProcessJobResponse,
)
from app.services.ingestion_service import process_job

router = APIRouter(prefix="/internal/v1/ingestion", tags=["Internal ingestion"])


def verify_internal_api_key(x_internal_api_key: str = Header(default="")) -> None:
    if not INTERNAL_API_KEY or not hmac.compare_digest(x_internal_api_key, INTERNAL_API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz internal servis anahtarı.")


@router.post("/jobs", response_model=IngestionJobResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(verify_internal_api_key)])
def create_job(request: CreateIngestionJob, db: Session = Depends(get_db)):
    existing = db.scalar(select(IngestionJob).where(IngestionJob.idempotency_key == request.idempotency_key))
    if existing is not None:
        if existing.document_id != request.document_id or existing.company_id != request.company_id:
            raise HTTPException(status_code=409, detail="Idempotency anahtarı başka bir iş için kullanılmış.")
        return existing
    job = IngestionJob(
        company_id=request.company_id,
        document_id=request.document_id,
        status=IngestionStatus.queued,
        idempotency_key=request.idempotency_key,
        storage_key=request.storage_key,
        checksum_sha256=request.checksum_sha256,
    )
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(IngestionJob).where(IngestionJob.idempotency_key == request.idempotency_key))
        if existing is None:
            raise
        if existing.document_id != request.document_id or existing.company_id != request.company_id:
            raise HTTPException(status_code=409, detail="Idempotency anahtarı başka bir iş için kullanılmış.")
        return existing
    db.refresh(job)
    return job


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse, dependencies=[Depends(verify_internal_api_key)])
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.get(IngestionJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Ingestion işi bulunamadı.")
    return job


@router.post(
    "/jobs/{job_id}/process",
    response_model=ProcessJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_internal_api_key)],
)
def start_job(job_id: uuid.UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = db.get(IngestionJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Ingestion işi bulunamadı.")
    if job.status not in {IngestionStatus.queued, IngestionStatus.failed}:
        raise HTTPException(status_code=409, detail="Bu ingestion işi başlatılabilir durumda değil.")
    if job.attempt_count >= job.max_attempts:
        raise HTTPException(status_code=409, detail="Ingestion işi maksimum deneme sayısına ulaştı.")
    background_tasks.add_task(process_job, job.id)
    return ProcessJobResponse(job_id=job.id, status=job.status)


@router.delete("/documents/{document_id}", response_model=DeleteIngestionDataResponse, dependencies=[Depends(verify_internal_api_key)])
def delete_document_data(document_id: uuid.UUID, company_id: uuid.UUID, db: Session = Depends(get_db)):
    chunks = db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id, DocumentChunk.company_id == company_id))
    jobs = db.execute(delete(IngestionJob).where(IngestionJob.document_id == document_id, IngestionJob.company_id == company_id))
    db.commit()
    return DeleteIngestionDataResponse(document_id=document_id, deleted_jobs=jobs.rowcount or 0, deleted_chunks=chunks.rowcount or 0)
