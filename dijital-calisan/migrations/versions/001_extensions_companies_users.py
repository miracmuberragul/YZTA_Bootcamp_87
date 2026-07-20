"""Create extensions, companies and users."""
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'employee')")
    op.execute("""
        CREATE TABLE companies (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(150) NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            company_id UUID NOT NULL REFERENCES companies(id),
            full_name VARCHAR(150) NOT NULL,
            email CITEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role user_role NOT NULL DEFAULT 'employee',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            last_login_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_users_company_email UNIQUE (company_id, email)
        )
    """)
    op.execute("CREATE INDEX idx_users_company_role ON users(company_id, role)")


def downgrade() -> None:
    op.execute("DROP TABLE users")
    op.execute("DROP TABLE companies")
    op.execute("DROP TYPE user_role")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
    op.execute("DROP EXTENSION IF EXISTS citext")
    op.execute("DROP EXTENSION IF EXISTS vector")
