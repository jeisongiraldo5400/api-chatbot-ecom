from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.services import Service, ServiceCreate, ServiceUpdate, ServiceBase
from models.users import User
from security import get_current_user
from models.category import CategoryBase

router = APIRouter(prefix="/services", tags=['Services'])


class CategoryInfo(CategoryBase):
  id: int


class ServiceWithCategoryResponse(ServiceBase):
  id: int
  status: bool
  category: Optional[CategoryInfo] = None


@router.post('/', response_model=Service)
def create_service(service_data: ServiceCreate, session: Session = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
  """Create a new service"""
  existing = session.exec(select(Service).where(Service.name == service_data.name)).first()
  if existing:
    raise HTTPException(status_code=400, detail="Service already exists")

  db_service = Service.model_validate(service_data)
  session.add(db_service)
  session.commit()
  session.refresh(db_service)
  return db_service


@router.get('/', response_model=list[ServiceWithCategoryResponse])
def get_all_services(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
  return session.exec(select(Service)).all()


@router.get('/{service_id}', response_model=ServiceWithCategoryResponse)
def get_service(service_id: int, session: Service = Depends(get_session)):
  db_service = session.get(Service, service_id)
  if not db_service:
    raise HTTPException(status_code=400, detail="Service not found")

  return db_service


@router.patch('/{service_id}', response_model=Service)
def update_service(service_id: int, service_data: ServiceUpdate, session: Session = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
  db_service = session.get(Service, service_id)
  if not db_service:
    raise HTTPException(status_code=404, detail="Service not found")

  update_data = service_data.model_dump(exclude_unset=True)

  for key, value in update_data.items():
    setattr(db_service, key, value)

  session.add(db_service)
  session.commit()
  session.refresh(db_service)
  return db_service


@router.delete('/{service_id}')
def delete_service(service_id: int, session: Session = Depends(get_session),
                   current_user: User = Depends(get_current_user)):
  db_service = session.get(Service, service_id)

  if not db_service:
    raise HTTPException(status_code=404, detail="Service not found")

  session.delete(db_service)
  session.commit()
  return {
    "message": f"Service '{db_service.name}'delete"
  }
