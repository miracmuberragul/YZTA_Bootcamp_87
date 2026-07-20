# Auth schemas placeholder
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


# ─── Register ────────────────────────────────────────────────────────────────

class CompanyRegisterRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=150)
    company_slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9\-]+$")
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    full_name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Login ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    company_slug: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: RegisterResponse


# ─── Me ──────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}