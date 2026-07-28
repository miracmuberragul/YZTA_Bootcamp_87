from __future__ import annotations

import time

from huggingface_hub import InferenceClient

from app.config import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    HF_EMBEDDING_PROVIDER,
    HF_MAX_RETRIES,
    HF_TIMEOUT_SECONDS,
    HF_TOKEN,
)


class EmbeddingError(RuntimeError):
    pass


def _normalize_vector(value) -> list[float]:
    vector = value.tolist() if hasattr(value, "tolist") else value
    if vector and isinstance(vector[0], list):
        vector = vector[0]
    vector = [float(item) for item in vector]
    if len(vector) != EMBEDDING_DIMENSION:
        raise EmbeddingError(
            f"Embedding boyutu uyuşmuyor: beklenen={EMBEDDING_DIMENSION}, gelen={len(vector)}"
        )
    return vector


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not HF_TOKEN:
        raise EmbeddingError("HF_TOKEN tanımlı değil.")
    client = InferenceClient(
        provider=HF_EMBEDDING_PROVIDER,
        api_key=HF_TOKEN,
        timeout=HF_TIMEOUT_SECONDS,
    )
    embeddings: list[list[float]] = []
    for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[start : start + EMBEDDING_BATCH_SIZE]
        last_error: Exception | None = None
        for attempt in range(HF_MAX_RETRIES):
            try:
                result = client.feature_extraction(batch, model=EMBEDDING_MODEL)
                values = result.tolist() if hasattr(result, "tolist") else result
                if len(batch) == 1 and values and not isinstance(values[0], list):
                    values = [values]
                embeddings.extend(_normalize_vector(value) for value in values)
                break
            except Exception as exc:
                last_error = exc
                if attempt + 1 < HF_MAX_RETRIES:
                    time.sleep(attempt + 1)
        else:
            raise EmbeddingError(f"Embedding üretilemedi: {last_error}") from last_error
    return embeddings
