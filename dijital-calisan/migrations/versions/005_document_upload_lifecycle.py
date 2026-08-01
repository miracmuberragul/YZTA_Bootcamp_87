"""Complete document upload lifecycle fields and active checksum uniqueness."""
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'deleting' BEFORE 'deleted'")
    op.execute("ALTER TABLE documents ADD COLUMN processing_error_code VARCHAR(100)")
    op.execute("ALTER TABLE documents ADD COLUMN deleted_at TIMESTAMPTZ")
    op.execute("ALTER TABLE documents DROP CONSTRAINT uq_documents_company_checksum")
    op.execute(
        "CREATE UNIQUE INDEX uq_documents_company_active_checksum "
        "ON documents(company_id, checksum_sha256) WHERE status <> 'deleted'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_documents_company_active_checksum")
    op.execute("ALTER TABLE documents ADD CONSTRAINT uq_documents_company_checksum UNIQUE (company_id, checksum_sha256)")
    op.execute("ALTER TABLE documents DROP COLUMN deleted_at")
    op.execute("ALTER TABLE documents DROP COLUMN processing_error_code")
    # PostgreSQL enum values cannot be removed safely in-place. The value remains unused.
