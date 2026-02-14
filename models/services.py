from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime


class ServiceBase(SQLModel):
  name: str = Field(unique=True, index=True)
  description: Optional[str] = None

  # Category
  category_id: int = Field(foreign_key="categories.id")


class Service(ServiceBase, table=True):
  __tablename__ = "services"
  id: Optional[int] = Field(default=None, primary_key=True)
  status: bool = Field(default=True)


class ServiceCreate(ServiceBase):
  pass

class ServiceUpdate(SQLModel):
  name: Optional[str] = None
  description: Optional[str] = None
  category_id: Optional[int] = None
  status: Optional[bool] = None