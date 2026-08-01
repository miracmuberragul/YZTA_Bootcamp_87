"""Add deterministic ingestion and chunk provenance fields."""
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("ALTER TABLE documents ADD COLUMN language VARCHAR(16)")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN max_attempts INT NOT NULL DEFAULT 3 CHECK (max_attempts > 0)")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN storage_key TEXT")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN checksum_sha256 CHAR(64)")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN parser_version VARCHAR(50)")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN chunker_version VARCHAR(50)")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN error_code VARCHAR(100)")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now()")
    op.execute("""
        UPDATE ingestion_jobs j
        SET storage_key = d.storage_path,
            checksum_sha256 = d.checksum_sha256
        FROM documents d
        WHERE d.id = j.document_id
    """)
    op.execute("ALTER TABLE ingestion_jobs ALTER COLUMN storage_key SET NOT NULL")
    op.execute("ALTER TABLE ingestion_jobs ALTER COLUMN checksum_sha256 SET NOT NULL")

    op.execute("ALTER TABLE document_chunks ADD COLUMN ingestion_job_id UUID REFERENCES ingestion_jobs(id) ON DELETE CASCADE")
    op.execute("ALTER TABLE document_chunks ADD COLUMN content_hash CHAR(64)")
    op.execute("ALTER TABLE document_chunks ADD COLUMN char_start INT")
    op.execute("ALTER TABLE document_chunks ADD COLUMN char_end INT")
    op.execute("""
        UPDATE document_chunks c
        SET ingestion_job_id = (
            SELECT j.id FROM ingestion_jobs j
            WHERE j.document_id = c.document_id
            ORDER BY j.created_at DESC
            LIMIT 1
        ),
        content_hash = encode(digest(c.content, 'sha256'), 'hex')
    """)
    op.execute("DELETE FROM document_chunks WHERE ingestion_job_id IS NULL")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN ingestion_job_id SET NOT NULL")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN content_hash SET NOT NULL")
    op.execute("ALTER TABLE document_chunks DROP CONSTRAINT uq_document_chunks_document_index")
    op.execute(
        "ALTER TABLE document_chunks ADD CONSTRAINT uq_document_chunks_job_index "
        "UNIQUE(document_id, ingestion_job_id, chunk_index)"
    )
    op.execute("ALTER TABLE document_chunks ADD CONSTRAINT ck_document_chunks_char_range CHECK (char_start IS NULL OR char_end IS NULL OR char_end >= char_start)")
    op.execute("CREATE INDEX idx_chunks_ingestion_job ON document_chunks(ingestion_job_id)")


def downgrade() -> None:
    op.execute("DROP INDEX idx_chunks_ingestion_job")
    op.execute("ALTER TABLE document_chunks DROP CONSTRAINT ck_document_chunks_char_range")
    op.execute("ALTER TABLE document_chunks DROP CONSTRAINT uq_document_chunks_job_index")
    op.execute("ALTER TABLE document_chunks ADD CONSTRAINT uq_document_chunks_document_index UNIQUE(document_id, chunk_index)")
    op.execute("ALTER TABLE document_chunks DROP COLUMN char_end")
    op.execute("ALTER TABLE document_chunks DROP COLUMN char_start")
    op.execute("ALTER TABLE document_chunks DROP COLUMN content_hash")
    op.execute("ALTER TABLE document_chunks DROP COLUMN ingestion_job_id")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN updated_at")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN error_code")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN chunker_version")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN parser_version")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN checksum_sha256")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN storage_key")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN max_attempts")
    op.execute("ALTER TABLE documents DROP COLUMN language")
