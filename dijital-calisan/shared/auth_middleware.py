# Shared auth middleware placeholder
"""
shared/auth_middleware.py
Tüm servisler bu middleware'i kullanarak JWT doğrular.
Her servise kopyalanır veya shared volume ile paylaşılır.
"""
import os
import uuid
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()


class TokenData:
    def __init__(self, user_id: uuid.UUID, company_id: uuid.UUID, role: str):
        self.user_id = user_id
        self.company_id = company_id
        self.role = role


def get_token_data(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenData:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload["sub"])
        company_id = uuid.UUID(payload["company_id"])
        role = payload["role"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenData(user_id=user_id, company_id=company_id, role=role)


def require_admin(token_data: TokenData = Depends(get_token_data)) -> TokenData:
    if token_data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gereklidir."
        )
    return token_data