import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentCategory(str, enum.Enum):
    procedure = "procedure"
    contract = "contract"
    onboarding = "onboarding"
    meeting_note = "meeting_note"
    other = "other"


class DocumentStatus(str, enum.Enum):
    uploading = "uploading"
    uploaded = "uploaded"
    queued = "queued"
    processing = "processing"
    processed = "processed"
    failed = "failed"
    deleted = "deleted"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("company_id", "checksum_sha256", name="uq_documents_company_checksum"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[DocumentCategory] = mapped_column(Enum(DocumentCategory, name="document_category"), default=DocumentCategory.other)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus, name="document_status"), default=DocumentStatus.uploading)
    page_count: Mapped[int | None] = mapped_column(Integer)
    processing_error_message: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
