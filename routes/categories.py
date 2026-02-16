from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.category import Category, CategoryCreate, CategoryUpdate
from models.users import User
from security import get_current_user
from models.services import ServiceBase
from models.category import CategoryBase

router = APIRouter(prefix="/categories", tags=["Categories"])


class ServiceInfo(ServiceBase):
  id: int
  status: bool


class CategoryWithServicesResponse(CategoryBase):
  id: int
  is_active: bool
  services: list[ServiceInfo] = []


@router.post("", response_model=Category)
def create_category(category_data: CategoryCreate, session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
  existing = session.exec(select(Category).where(Category.name == category_data.name)).first()
  if existing:
    raise HTTPException(status_code=400, detail="La categoría ya existe")

  db_category = Category.model_validate(category_data)
  session.add(db_category)
  session.commit()
  session.refresh(db_category)
  return db_category


@router.get("", response_model=list[Category])
def read_categories(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
  return session.exec(select(Category)).all()


@router.get("/{category_id}/services", response_model=CategoryWithServicesResponse)
def read_category_with_services(category_id: int, session: Session = Depends(get_session)):
  db_category = session.get(Category, category_id)
  if not db_category:
    raise HTTPException(status_code=404, detail="Categoría no encontrada")

  return db_category


@router.patch("/{category_id}", response_model=Category)
def update_category(category_id: int, category_data: CategoryUpdate, session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
  db_category = session.get(Category, category_id)
  if not db_category:
    raise HTTPException(status_code=404, detail="Categoría no encontrada")

  update_data = category_data.model_dump(exclude_unset=True)
  for key, value in update_data.items():
    setattr(db_category, key, value)

  session.add(db_category)
  session.commit()
  session.refresh(db_category)
  return db_category


@router.delete("/{category_id}")
def delete_category(category_id: int, session: Session = Depends(get_session),
                    current_user: User = Depends(get_current_user)):
  db_category = session.get(Category, category_id)
  if not db_category:
    raise HTTPException(status_code=404, detail="Categoría no encontrada")
  session.delete(db_category)
  session.commit()
  return {"message": "Categoría eliminada"}
