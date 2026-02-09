from typing import Optional, Annotated
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import StringConstraints


class UserBase(SQLModel):
  full_name: str
  email: str = Field(unique=True, index=True)


class UserCreate(UserBase):
  password: Annotated[str, StringConstraints(max_length=72)]


class User(UserBase, table=True):
  __tablename__ = "users"

  id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
  password_hash: str
  created_at: datetime = Field(default_factory=datetime.utcnow)
