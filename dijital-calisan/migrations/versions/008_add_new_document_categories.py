from alembic import op

revision = '008_add_new_document_categories'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE document_category ADD VALUE IF NOT EXISTS 'hr'")
    op.execute("ALTER TYPE document_category ADD VALUE IF NOT EXISTS 'finance'")
    op.execute("ALTER TYPE document_category ADD VALUE IF NOT EXISTS 'legal'")
    op.execute("ALTER TYPE document_category ADD VALUE IF NOT EXISTS 'sales'")
    op.execute("ALTER TYPE document_category ADD VALUE IF NOT EXISTS 'technical'")
    op.execute("ALTER TYPE document_category ADD VALUE IF NOT EXISTS 'customer'")
    op.execute("ALTER TYPE document_category ADD VALUE IF NOT EXISTS 'training'")
    op.execute("ALTER TYPE document_category ADD VALUE IF NOT EXISTS 'faq'")


def downgrade() -> None:
    pass