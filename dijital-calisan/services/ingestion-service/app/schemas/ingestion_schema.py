import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.chunk import IngestionStatus


class CreateIngestionJob(BaseModel):
    document_id: uuid.UUID
    company_id: uuid.UUID
    storage_key: str = Field(min_length=1, max_length=500)
    checksum_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    idempotency_key: str = Field(min_length=1, max_length=100)


class IngestionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    company_id: uuid.UUID
    status: IngestionStatus
    attempt_count: int
    max_attempts: int
    idempotency_key: str
    parser_version: str | None
    chunker_version: str | None
    error_code: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class DeleteIngestionDataResponse(BaseModel):
    document_id: uuid.UUID
    deleted_jobs: int
    deleted_chunks: int


class ProcessJobResponse(BaseModel):
    job_id: uuid.UUID
    status: IngestionStatus
