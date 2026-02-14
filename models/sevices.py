from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime


class ServiceBase(SQLModel):
  name: str = Field(unique=True, index=True)
  description: Optional[str] = None


class Service(ServiceBase, table=True):
  __tablename__ = "services"
  id: Optional[int] = Field(default=None, primary_key=True)
  status: bool = Field(default=True)


class ServiceCreate(ServiceBase):
  pass
