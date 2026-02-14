from typing import Optional

from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
  PENDING = "PENDING"
  PROCESSING = "PROCESSING"
  READY = "READY"
  ERROR = "ERROR"


class DocumentBase(SQLModel):
  title: str
  service_id: int = Field(foreign_key="services.id")
  s3_key: str
  hash_md5: Optional[str] = None


class Document(DocumentBase, table=True):
  __tablename__ = "documents"
  id: UUID = Field(default_factory=uuid4, primary_key=True)
  upload_date: datetime = Field(default_factory=datetime.now)
  status: DocumentStatus = Field(default=DocumentStatus.PENDING)


class DocumentCreate(DocumentBase):
  pass
