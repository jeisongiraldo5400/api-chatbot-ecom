from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
from database import get_session
from models.users import User
from security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginCredentials(BaseModel):
  email: str
  password: str


class UserResponse(BaseModel):
  id: str
  name: str
  email: str


class AuthResponse(BaseModel):
  token: str
  user: UserResponse


@router.post("/login", response_model=AuthResponse)
def login(credentials: LoginCredentials, session: Session = Depends(get_session)):
  user = session.exec(select(User).where(User.email == credentials.email, User.deleted_at == None)).first()

  if not user or not verify_password(credentials.password, user.password_hash):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Correo o contraseña incorrectos"
    )

  access_token = create_access_token(data={"sub": str(user.id)})

  return AuthResponse(
    token=access_token,
    user=UserResponse(
      id=str(user.id),
      name=user.full_name,
      email=user.email
    )
  )
