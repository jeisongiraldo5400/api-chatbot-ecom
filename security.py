from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from jwt.exceptions import InvalidTokenError
from database import get_session
from models.users import User

import jwt
from datetime import datetime, timedelta
import os

pwd_context = CryptContext(schemes=["sha256_crypt", "md5_crypt"])

SECRET_KEY = os.getenv("SECRET_KEY", "mi_super_clave_secreta_mvp")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # El token dura 1 día (24 horas)

token_auth_scheme = HTTPBearer()


def get_password_hash(password: str) -> str:
  return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
  return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
  """Genera un token JWT firmado"""
  to_encode = data.copy()
  expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  to_encode.update({"exp": expire})

  # Creamos y firmamos el token
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt


def get_current_user(
  token: HTTPAuthorizationCredentials = Depends(token_auth_scheme),
  session: Session = Depends(get_session)
) -> User:
  """Dependencia para validar el JWT y obtener el usuario actual"""

  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
  )

  try:
    # 1. Decodificar el token usando la misma llave secreta
    payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    user_id: str = payload.get("sub")

    if user_id is None:
      raise credentials_exception

  except InvalidTokenError:
    # Si el token expiró o fue alterado, cae aquí
    raise credentials_exception

  # 2. Buscar al usuario en la base de datos
  user = session.get(User, user_id)
  if user is None:
    raise credentials_exception

  # 3. Retornar el objeto de base de datos del usuario
  return user
