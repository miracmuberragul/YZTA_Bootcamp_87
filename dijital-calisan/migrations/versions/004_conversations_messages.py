"""Create conversations, messages and message sources."""
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE message_role AS ENUM ('user', 'assistant')")
    op.execute("""
        CREATE TABLE conversations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            company_id UUID NOT NULL REFERENCES companies(id),
            user_id UUID NOT NULL REFERENCES users(id),
            title VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE messages (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            company_id UUID NOT NULL REFERENCES companies(id),
            role message_role NOT NULL,
            content TEXT NOT NULL,
            response_time_ms INT CHECK (response_time_ms IS NULL OR response_time_ms >= 0),
            confidence_level VARCHAR(20) CHECK (confidence_level IS NULL OR confidence_level IN ('high', 'medium', 'low')),
            feedback SMALLINT CHECK (feedback IN (-1, 1)),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE message_sources (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
            chunk_id UUID NOT NULL REFERENCES document_chunks(id),
            document_id UUID NOT NULL REFERENCES documents(id),
            similarity_score NUMERIC CHECK (similarity_score IS NULL OR similarity_score BETWEEN 0 AND 1),
            excerpt_text TEXT,
            page_start INT,
            page_end INT,
            section_title VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_message_sources_message_chunk UNIQUE (message_id, chunk_id),
            CONSTRAINT ck_message_sources_page_range CHECK (page_start IS NULL OR page_end IS NULL OR page_end >= page_start)
        )
    """)
    op.execute("CREATE INDEX idx_conversations_company_user ON conversations(company_id, user_id, updated_at DESC)")
    op.execute("CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at)")
    op.execute("CREATE INDEX idx_message_sources_message ON message_sources(message_id)")


def downgrade() -> None:
    op.execute("DROP TABLE message_sources")
    op.execute("DROP TABLE messages")
    op.execute("DROP TABLE conversations")
    op.execute("DROP TYPE message_role")
