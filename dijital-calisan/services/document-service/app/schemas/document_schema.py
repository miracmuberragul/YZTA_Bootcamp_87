import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentCategory, DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    display_name: str
    mime_type: str
    file_size_bytes: int
    category: DocumentCategory
    status: DocumentStatus
    page_count: int | None
    language: str | None
    processing_error_code: str | None
    processing_error_message: str | None
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UploadResponse(BaseModel):
    document_id: uuid.UUID
    status: DocumentStatus
    status_url: str
    duplicate: bool = False


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class DeleteResponse(BaseModel):
    document_id: uuid.UUID
    status: DocumentStatus


class RetryResponse(BaseModel):
    document_id: uuid.UUID
    status: DocumentStatus


class ProcessingStatusUpdate(BaseModel):
    company_id: uuid.UUID
    status: Literal["processing", "processed", "failed"]
    page_count: int | None = Field(default=None, ge=0)
    language: str | None = Field(default=None, max_length=16)
    error_code: str | None = Field(default=None, max_length=100)
    error_message: str | None = Field(default=None, max_length=1000)
