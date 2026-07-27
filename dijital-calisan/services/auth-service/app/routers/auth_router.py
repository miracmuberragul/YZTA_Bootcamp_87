# Auth router placeholder
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.models.user import User
from app.schemas.auth_schema import (
    CompanyRegisterRequest,
    RegisterResponse,
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    CompanySettingsResponse,
    CompanySettingsUpdate,
)
from app.services.auth_service import register_company, login_user
from app.utils.security import decode_access_token, hash_password

router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı."
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için admin yetkisi gerekiyor.")
    return current_user


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(req: CompanyRegisterRequest, db: Session = Depends(get_db)):
    user = register_company(db, req)
    return user


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user, token = login_user(db, req)
    return TokenResponse(
        access_token=token,
        user=RegisterResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserResponse])
def users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return (
        db.query(User)
        .filter(User.company_id == current_user.company_id)
        .order_by(User.created_at.desc())
        .all()
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    req: UserCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = User(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        full_name=req.full_name.strip(),
        email=req.email,
        password_hash=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bu e-posta şirkette zaten kayıtlı.") from exc
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    req: UserUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id, User.company_id == current_user.company_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    changes = req.model_dump(exclude_none=True)
    if user.id == current_user.id and changes.get("is_active") is False:
        raise HTTPException(status_code=409, detail="Kendi hesabınızı pasifleştiremezsiniz.")
    for key, value in changes.items():
        setattr(user, key, value.strip() if isinstance(value, str) else value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bu e-posta şirkette zaten kayıtlı.") from exc
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=409, detail="Kendi hesabınızı silemezsiniz.")
    user = db.query(User).filter(User.id == user_id, User.company_id == current_user.company_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if user.role.value == "admin" and user.is_active:
        active_admins = db.query(User).filter(
            User.company_id == current_user.company_id,
            User.role == "admin",
            User.is_active == True,
        ).count()
        if active_admins <= 1:
            raise HTTPException(status_code=409, detail="Şirketin son aktif yöneticisi silinemez.")
    db.delete(user)
    db.commit()


@router.get("/settings", response_model=CompanySettingsResponse)
def settings(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT c.name, coalesce(s.max_upload_mb, 15), coalesce(s.retrieval_limit, 3),
                   coalesce(s.min_similarity, 0.25), s.system_prompt
            FROM companies c
            LEFT JOIN company_settings s ON s.company_id = c.id
            WHERE c.id = :company_id
        """),
        {"company_id": current_user.company_id},
    ).one()
    return CompanySettingsResponse(
        company_name=row[0], max_upload_mb=row[1], retrieval_limit=row[2],
        min_similarity=row[3], system_prompt=row[4],
    )


@router.put("/settings", response_model=CompanySettingsResponse)
def update_settings(
    req: CompanySettingsUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    db.execute(
        text("UPDATE companies SET name=:name, updated_at=now() WHERE id=:company_id"),
        {"name": req.company_name.strip(), "company_id": current_user.company_id},
    )
    db.execute(
        text("""
            INSERT INTO company_settings
                (company_id, max_upload_mb, retrieval_limit, min_similarity, system_prompt)
            VALUES (:company_id, :max_upload_mb, :retrieval_limit, :min_similarity, :system_prompt)
            ON CONFLICT (company_id) DO UPDATE SET
                max_upload_mb=excluded.max_upload_mb,
                retrieval_limit=excluded.retrieval_limit,
                min_similarity=excluded.min_similarity,
                system_prompt=excluded.system_prompt,
                updated_at=now()
        """),
        {"company_id": current_user.company_id, **req.model_dump(exclude={"company_name"})},
    )
    db.commit()
    return CompanySettingsResponse(**req.model_dump())
