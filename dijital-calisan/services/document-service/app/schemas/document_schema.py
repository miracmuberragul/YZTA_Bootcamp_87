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
    category_id: uuid.UUID | None = None
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


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    color: str = Field(default="#E85D04", pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryResponse(CategoryCreate):
    id: uuid.UUID
    document_count: int = 0
    created_at: datetime


class DocumentCategoryUpdate(BaseModel):
    category_id: uuid.UUID | None = None
