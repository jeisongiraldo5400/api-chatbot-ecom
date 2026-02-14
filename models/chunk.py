from typing import Optional, List
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column


class DocumentChunk(SQLModel, table=True):
  __tablename__ = "document_chunks"

  id: UUID = Field(default_factory=uuid4, primary_key=True)
  document_id: UUID = Field(foreign_key="documents.id", ondelete="CASCADE")

  content: str
  page_number: Optional[int] = None

  embedding: List[float] = Field(sa_column=Column(Vector(768)))
