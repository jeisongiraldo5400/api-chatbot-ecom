from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from security import get_password_hash
from uuid import UUID
from models.users import User, UserCreate
from security import get_current_user

router = APIRouter(prefix='/users', tags=['Users'])


@router.get('/', response_model=list[User])
def get_all_users(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
  """Get all users"""
  users = session.exec(select(User)).all()
  return users


@router.post('/', response_model=User)
def create_user(user_data: UserCreate, session: Session = Depends(get_session),
                current_user: User = Depends(get_current_user)):
  """Create a new user"""
  hashed_pwd = get_password_hash(user_data.password)

  new_user = User(
    full_name=user_data.full_name,
    email=user_data.email,
    password_hash=hashed_pwd
  )

  session.add(new_user)
  session.commit()
  session.refresh(new_user)
  return new_user


@router.patch('/{user_id}', response_model=User)
def update_user(user_id: UUID, user_data: UserCreate, session: Session = Depends(get_session),
                current_user: User = Depends(get_current_user)):
  db_user = session.get(User, user_id)

  if not db_user:
    raise HTTPException(status_code=404, detail="User not found")

  update_data = user_data.model_dump(exclude_unset=True)

  if "password" in update_data:
    update_data["password_hash"] = get_password_hash(update_data.pop("password"))

  for key, value in update_data.items():
    setattr(db_user, key, value)

  session.add(db_user)
  session.commit()
  session.refresh(db_user)

  return db_user


@router.delete('/{user_id}')
def delete_user(user_id: UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
  db_user = session.get(User, user_id)

  if not db_user:
    raise HTTPException(status_code=404, detail="User not found")

  session.delete(db_user)
  session.commit()

  return {
    "message": "User deleted successfully"
  }
