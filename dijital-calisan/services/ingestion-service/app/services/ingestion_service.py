from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from sqlalchemy import delete, select

from app.config import (
    CHUNKER_VERSION,
    DOCUMENT_SERVICE_URL,
    INTERNAL_API_KEY,
    PARSER_VERSION,
)
from app.database import SessionLocal
from app.models.chunk import DocumentChunk, IngestionJob, IngestionStatus
from app.services.chunking_service import chunk_document
from app.services.parser_service import ParserError, parse_document, resolve_storage_key

logger = logging.getLogger(__name__)

def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _update_document_status(
    document_id: uuid.UUID,
    company_id: uuid.UUID,
    status: str,
    *,
    page_count: int | None = None,
    language: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    response = httpx.patch(
        f"{DOCUMENT_SERVICE_URL}/internal/v1/documents/{document_id}/processing-status",
        headers={"X-Internal-API-Key": INTERNAL_API_KEY},
        json={
            "company_id": str(company_id),
            "status": status,
            "page_count": page_count,
            "language": language,
            "error_code": error_code,
            "error_message": error_message,
        },
        timeout=5.0,
    )
    response.raise_for_status()


def _fail_job(job_id: uuid.UUID, code: str, message: str) -> None:
    with SessionLocal() as db:
        job = db.get(IngestionJob, job_id)
        if job is None:
            return
        job.status = IngestionStatus.failed
        job.error_code = code
        job.error_message = message[:2000]
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        try:
            _update_document_status(
                job.document_id,
                job.company_id,
                "failed",
                error_code=code,
                error_message=message[:1000],
            )
        except httpx.HTTPError:
            pass


def process_job(job_id: uuid.UUID) -> None:
    with SessionLocal() as db:
        job = db.scalar(select(IngestionJob).where(IngestionJob.id == job_id).with_for_update())
        if job is None or job.status not in {IngestionStatus.queued, IngestionStatus.failed}:
            return
        if job.attempt_count >= job.max_attempts:
            return
        job.status = IngestionStatus.processing
        job.attempt_count += 1
        job.parser_version = PARSER_VERSION
        job.chunker_version = CHUNKER_VERSION
        job.error_code = None
        job.error_message = None
        job.started_at = datetime.now(timezone.utc)
        job.finished_at = None
        document_id = job.document_id
        company_id = job.company_id
        storage_key = job.storage_key
        expected_checksum = job.checksum_sha256
        db.commit()

    try:
        _update_document_status(document_id, company_id, "processing")
        path = resolve_storage_key(storage_key)
        if _checksum(path) != expected_checksum:
            raise ParserError("CHECKSUM_MISMATCH", "Doküman dosyasının checksum değeri yükleme kaydıyla uyuşmuyor.")
        parsed = parse_document(storage_key)
        chunks = chunk_document(parsed)
        if not chunks:
            raise ParserError("EMPTY_DOCUMENT", "Dokümandan aranabilir chunk üretilemedi.")

        with SessionLocal.begin() as db:
            db.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.company_id == company_id,
                    DocumentChunk.document_id == document_id,
                )
            )
            db.add_all(
                [
                    DocumentChunk(
                        company_id=company_id,
                        document_id=document_id,
                        ingestion_job_id=job_id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        content_hash=chunk.content_hash,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        section_title=chunk.section_title,
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                        token_count=chunk.token_count,
                        embedding=None,
                    )
                    for chunk in chunks
                ]
            )

        _update_document_status(
            document_id,
            company_id,
            "processed",
            page_count=parsed.page_count,
            language=parsed.language,
        )
        with SessionLocal() as db:
            job = db.get(IngestionJob, job_id)
            if job is not None:
                job.status = IngestionStatus.succeeded
                job.finished_at = datetime.now(timezone.utc)
                db.commit()
    except ParserError as exc:
        _fail_job(job_id, exc.code, exc.message)
    except httpx.HTTPError:
        _fail_job(job_id, "DEPENDENCY_UNAVAILABLE", "Doküman durum servisine ulaşılamadı.")
    except Exception:
        logger.exception("Unexpected ingestion failure", extra={"job_id": str(job_id)})
        _fail_job(job_id, "INGESTION_FAILED", "Doküman işlenirken beklenmeyen bir hata oluştu.")


def process_pending_jobs(limit: int = 5) -> int:
    with SessionLocal() as db:
        job_ids = list(
            db.scalars(
                select(IngestionJob.id)
                .where(
                    IngestionJob.status == IngestionStatus.queued,
                    IngestionJob.created_at <= datetime.now(timezone.utc) - timedelta(seconds=2),
                )
                .order_by(IngestionJob.created_at)
                .limit(limit)
            )
        )
    for job_id in job_ids:
        process_job(job_id)
    return len(job_ids)
