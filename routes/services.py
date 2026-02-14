from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.sevices import Service, ServiceCreate

router = APIRouter(prefix="/services", tags=['Services'])


@router.post('/', response_model=Service)
def create_service(service_data: ServiceCreate, session: Session = Depends(get_session)):
  """Create a new service"""
  existing = session.exec(select(Service).where(Service.name == service_data.name)).first()
  if existing:
    raise HTTPException(status_code=400, detail="Service already exists")

  db_service = Service.model_validate(service_data)
  session.add(db_service)
  session.commit()
  session.refresh(db_service)
  return db_service


@router.get('/', response_model=list[Service])
def get_all_services(session: Session = Depends(get_session)):
  return session.exec(select(Service)).all()


@router.get('/{service_id}')
def get_service(service_id: int, session: Service = Depends(get_session)):
  db_service = session.get(Service, service_id)
  if not db_service:
    raise HTTPException(status_code=400, detail="Service not found")

  return db_service


@router.patch('/{service_id}', response_model=Service)
def update_service(service_id: int, service_data: ServiceCreate, session: Session = Depends(get_session)):
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
def delete_service(service_id: int, session: Session = Depends(get_session)):
  db_service = session.get(Service, service_id)

  if not db_service:
    raise HTTPException(status_code=404, detail="Service not found")

  session.delete(db_service)
  session.commit()
  return {
    "message": f"Service '{db_service.name}'delete"
  }
