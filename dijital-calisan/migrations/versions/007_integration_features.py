"""Add integration features for RAG, categories, analytics and company settings."""
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE categories (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            color VARCHAR(7) NOT NULL DEFAULT '#E85D04',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_categories_company_name UNIQUE(company_id, name),
            CONSTRAINT ck_categories_color CHECK (color ~ '^#[0-9A-Fa-f]{6}$')
        )
    """)
    op.execute("ALTER TABLE documents ADD COLUMN category_id UUID REFERENCES categories(id) ON DELETE SET NULL")
    op.execute("CREATE INDEX idx_documents_category ON documents(company_id, category_id)")
    op.execute("""
        CREATE TABLE company_settings (
            company_id UUID PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
            max_upload_mb INT NOT NULL DEFAULT 15 CHECK (max_upload_mb BETWEEN 1 AND 100),
            retrieval_limit INT NOT NULL DEFAULT 3 CHECK (retrieval_limit BETWEEN 1 AND 10),
            min_similarity DOUBLE PRECISION NOT NULL DEFAULT 0.25 CHECK (min_similarity BETWEEN -1 AND 1),
            system_prompt TEXT,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        INSERT INTO company_settings(company_id)
        SELECT id FROM companies
        ON CONFLICT (company_id) DO NOTHING
    """)
    op.execute("""
        CREATE TABLE usage_events (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            event_type VARCHAR(80) NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            duration_ms INT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX idx_usage_events_company_created ON usage_events(company_id, created_at DESC)")
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
    op.execute("DELETE FROM document_chunks")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1024)")
    op.execute(
        "CREATE INDEX idx_chunks_embedding ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL"
    )
    op.execute("""
        UPDATE documents
        SET status = 'queued', processed_at = NULL
        WHERE status = 'processed'
    """)
    op.execute("""
        UPDATE ingestion_jobs
        SET status = 'queued', attempt_count = 0, embedding_model = NULL,
            embedding_dimension = NULL, error_code = NULL, error_message = NULL,
            started_at = NULL, finished_at = NULL
        WHERE document_id IN (SELECT id FROM documents WHERE status = 'queued')
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
    op.execute("DELETE FROM document_chunks")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("CREATE INDEX idx_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops)")
    op.execute("DROP INDEX idx_usage_events_company_created")
    op.execute("DROP TABLE usage_events")
    op.execute("DROP TABLE company_settings")
    op.execute("DROP INDEX idx_documents_category")
    op.execute("ALTER TABLE documents DROP COLUMN category_id")
    op.execute("DROP TABLE categories")
