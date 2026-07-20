from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any
from datetime import datetime, timezone
import uuid

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str          # makine-okunur, sabit liste (aşağıda)
    message: str        # kullanıcıya gösterilecek Türkçe mesaj

class ResponseMeta(BaseModel):
    request_id: str
    timestamp: str

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    meta: ResponseMeta

def success_response(data: Any) -> dict:
    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": {"request_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat()}
    }

def error_response(code: str, message: str) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message},
        "meta": {"request_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat()}
    }