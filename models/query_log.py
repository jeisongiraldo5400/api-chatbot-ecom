from typing import Optional, List
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import Column, ARRAY, String


class QueryLog(SQLModel, table=True):
  __tablename__ = "queries_log"
  id: UUID = Field(default_factory=uuid4, primary_key=True)
  user_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
  service_id: int = Field(foreign_key="services.id")
  query_text: str
  answer_text: str
  context_chunks_ids: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
  response_time: Optional[float] = None
  created_at: datetime = Field(default_factory=datetime.now)
