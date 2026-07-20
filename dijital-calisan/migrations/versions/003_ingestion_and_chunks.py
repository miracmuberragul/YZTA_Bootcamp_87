"""Create ingestion jobs and document chunks."""
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE ingestion_status AS ENUM ('queued', 'processing', 'succeeded', 'failed')")
    op.execute("""
        CREATE TABLE ingestion_jobs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            company_id UUID NOT NULL REFERENCES companies(id),
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            status ingestion_status NOT NULL DEFAULT 'queued',
            attempt_count INT NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
            idempotency_key VARCHAR(100) UNIQUE NOT NULL,
            embedding_model VARCHAR(100),
            embedding_dimension INT CHECK (embedding_dimension IS NULL OR embedding_dimension > 0),
            error_message TEXT,
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE document_chunks (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            company_id UUID NOT NULL REFERENCES companies(id),
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INT NOT NULL CHECK (chunk_index >= 0),
            content TEXT NOT NULL,
            page_start INT,
            page_end INT,
            section_title VARCHAR(255),
            token_count INT CHECK (token_count IS NULL OR token_count >= 0),
            embedding vector(1536),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_document_chunks_document_index UNIQUE (document_id, chunk_index),
            CONSTRAINT ck_document_chunks_page_range CHECK (page_start IS NULL OR page_end IS NULL OR page_end >= page_start)
        )
    """)
    op.execute("CREATE INDEX idx_ingestion_jobs_document ON ingestion_jobs(company_id, document_id, status)")
    op.execute("CREATE INDEX idx_chunks_company_document ON document_chunks(company_id, document_id)")
    op.execute("CREATE INDEX idx_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP TABLE document_chunks")
    op.execute("DROP TABLE ingestion_jobs")
    op.execute("DROP TYPE ingestion_status")
