import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    conversation_id: uuid.UUID | None = None

    @field_validator("question")
    @classmethod
    def trim_question(cls, value: str) -> str:
        return value.strip()


class SourceResponse(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    content: str
    chunk_index: int
    similarity: float


class ChatResponse(BaseModel):
    question: str
    answer: str
    conversation_id: uuid.UUID
    sources: list[SourceResponse]


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationMessage(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[ConversationMessage]


class DailyMetric(BaseModel):
    date: date
    count: int


class AnalyticsSummary(BaseModel):
    total_documents: int
    processed_documents: int
    failed_documents: int
    active_users: int
    category_count: int
    total_questions: int
    questions_this_week: int
    average_response_ms: int
    daily_questions: list[DailyMetric]
    top_documents: list[dict]
