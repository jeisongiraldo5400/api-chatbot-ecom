from passlib.context import CryptContext

import jwt
from datetime import datetime, timedelta
import os

pwd_context = CryptContext(schemes=["sha256_crypt", "md5_crypt"])

SECRET_KEY = os.getenv("SECRET_KEY", "mi_super_clave_secreta_mvp")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # El token dura 1 día (24 horas)


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
