# Auth service placeholder
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import Company, User, UserRole
from app.schemas.auth_schema import CompanyRegisterRequest, LoginRequest
from app.utils.security import hash_password, verify_password, create_access_token


def register_company(db: Session, req: CompanyRegisterRequest) -> User:
    # Slug kontrolü
    existing_company = db.query(Company).filter(Company.slug == req.company_slug).first()
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu şirket slug'ı zaten kullanılıyor."
        )

    # Şirketi oluştur
    company = Company(
        id=uuid.uuid4(),
        name=req.company_name,
        slug=req.company_slug,
    )
    db.add(company)
    db.flush()  # company.id'yi almak için

    # Admin kullanıcıyı oluştur
    existing_user = db.query(User).filter(
        User.company_id == company.id,
        User.email == req.email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu e-posta bu şirkette zaten kayıtlı."
        )

    user = User(
        id=uuid.uuid4(),
        company_id=company.id,
        full_name=req.full_name,
        email=req.email,
        password_hash=hash_password(req.password),
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, req: LoginRequest) -> tuple[User, str]:
    # Şirket kontrolü
    company = db.query(Company).filter(
        Company.slug == req.company_slug,
        Company.is_active == True
    ).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Şirket bulunamadı."
        )

    # Kullanıcı kontrolü
    user = db.query(User).filter(
        User.company_id == company.id,
        User.email == req.email,
        User.is_active == True
    ).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı."
        )

    # last_login_at güncelle
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    # Token oluştur
    token = create_access_token({
        "sub": str(user.id),
        "company_id": str(user.company_id),
        "role": user.role.value,
    })

    return user, token