import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import AuthContext, require_admin
from app.database import get_db
from app.models.document import Category, Document, DocumentStatus
from app.schemas.document_schema import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


def _response(db: Session, category: Category) -> CategoryResponse:
    count = db.scalar(
        select(func.count()).select_from(Document).where(
            Document.company_id == category.company_id,
            Document.category_id == category.id,
            Document.status != DocumentStatus.deleted,
        )
    ) or 0
    return CategoryResponse(
        id=category.id, name=category.name, color=category.color,
        document_count=count, created_at=category.created_at,
    )


@router.get("", response_model=list[CategoryResponse])
def list_categories(auth: AuthContext = Depends(require_admin), db: Session = Depends(get_db)):
    categories = list(db.scalars(
        select(Category).where(Category.company_id == auth.company_id).order_by(Category.name)
    ))
    return [_response(db, category) for category in categories]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
):
    category = Category(
        id=uuid.uuid4(), company_id=auth.company_id,
        name=payload.name.strip(), color=payload.color,
    )
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bu kategori zaten mevcut.") from exc
    db.refresh(category)
    return _response(db, category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
):
    category = db.scalar(select(Category).where(
        Category.id == category_id, Category.company_id == auth.company_id
    ))
    if category is None:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı.")
    db.delete(category)
    db.commit()
