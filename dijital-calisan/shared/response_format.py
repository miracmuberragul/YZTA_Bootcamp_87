# Shared response format placeholder
from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ResponseFormat(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None


# ─── Yardımcı fonksiyonlar ───────────────────────────────────────────────────

def success_response(data: Any = None) -> dict:
    return ResponseFormat(success=True, data=data, error=None).model_dump()


def error_response(code: str, message: str, details: Any = None) -> dict:
    return ResponseFormat(
        success=False,
        data=None,
        error=ErrorDetail(code=code, message=message, details=details)
    ).model_dump()


# ─── Yaygın hata kodları ─────────────────────────────────────────────────────

class ErrorCode:
    # Auth
    UNAUTHORIZED        = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED       = "TOKEN_EXPIRED"

    # Doküman
    DOCUMENT_NOT_FOUND  = "DOCUMENT_NOT_FOUND"
    INVALID_FILE_TYPE   = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE      = "FILE_TOO_LARGE"

    # Ingestion
    INGESTION_FAILED    = "INGESTION_FAILED"
    PARSING_ERROR       = "PARSING_ERROR"

    # Chat / LLM
    LLM_API_ERROR       = "LLM_API_ERROR"
    NO_RELEVANT_DOCS    = "NO_RELEVANT_DOCS"

    # Genel
    VALIDATION_ERROR    = "VALIDATION_ERROR"
    INTERNAL_ERROR      = "INTERNAL_ERROR"