"""Create documents."""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE document_category AS ENUM ('procedure', 'contract', 'onboarding', 'meeting_note', 'other')")
    op.execute("CREATE TYPE document_status AS ENUM ('uploading', 'uploaded', 'queued', 'processing', 'processed', 'failed', 'deleted')")
    op.execute("""
        CREATE TABLE documents (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            company_id UUID NOT NULL REFERENCES companies(id),
            uploaded_by UUID NOT NULL REFERENCES users(id),
            original_filename VARCHAR(255) NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            storage_path TEXT NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes >= 0),
            checksum_sha256 CHAR(64) NOT NULL,
            category document_category NOT NULL DEFAULT 'other',
            status document_status NOT NULL DEFAULT 'uploading',
            page_count INT CHECK (page_count IS NULL OR page_count >= 0),
            processing_error_message TEXT,
            processed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_documents_company_checksum UNIQUE (company_id, checksum_sha256)
        )
    """)
    op.execute("CREATE INDEX idx_documents_company_status ON documents(company_id, status, created_at DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE documents")
    op.execute("DROP TYPE document_status")
    op.execute("DROP TYPE document_category")
