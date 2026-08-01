from huggingface_hub import InferenceClient
from sqlalchemy import text

from app.config import (
    EMBEDDING_DIMENSION, EMBEDDING_MODEL, HF_EMBEDDING_PROVIDER,
    HF_TIMEOUT_SECONDS, HF_TOKEN,
)
from app.database import SessionLocal
from app.schemas.chat_schema import SourceResponse


def _embedding(query: str) -> list[float]:
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN tanımlı değil.")
    result = InferenceClient(
        provider=HF_EMBEDDING_PROVIDER, api_key=HF_TOKEN, timeout=HF_TIMEOUT_SECONDS
    ).feature_extraction(query, model=EMBEDDING_MODEL)
    vector = result.tolist() if hasattr(result, "tolist") else result
    if vector and isinstance(vector[0], list):
        vector = vector[0]
    if len(vector) != EMBEDDING_DIMENSION:
        raise RuntimeError("Embedding boyutu yapılandırmayla uyuşmuyor.")
    return [float(value) for value in vector]


def retrieve(query: str, company_id, limit: int, min_similarity: float) -> list[SourceResponse]:
    vector = "[" + ",".join(str(value) for value in _embedding(query)) + "]"
    with SessionLocal() as db:
        rows = db.execute(
            text("""
                SELECT c.id, c.document_id, d.display_name, c.content, c.chunk_index,
                       1 - (c.embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM document_chunks c
                JOIN documents d ON d.id=c.document_id
                WHERE c.company_id=:company_id AND d.company_id=:company_id
                  AND d.status='processed' AND c.embedding IS NOT NULL
                  AND 1 - (c.embedding <=> CAST(:embedding AS vector)) >= :min_similarity
                ORDER BY c.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """),
            {"embedding": vector, "company_id": company_id, "min_similarity": min_similarity, "limit": limit},
        ).all()
    return [
        SourceResponse(
            chunk_id=row[0], document_id=row[1], document_name=row[2],
            content=row[3], chunk_index=row[4], similarity=float(row[5]),
        )
        for row in rows
    ]
