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
    idempotency_key: str
    created_at: datetime


class DeleteIngestionDataResponse(BaseModel):
    document_id: uuid.UUID
    deleted_jobs: int
    deleted_chunks: int
