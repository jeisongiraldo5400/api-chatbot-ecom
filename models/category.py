from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class CategoryBase(SQLModel):
  name: str = Field(unique=True, index=True)
  description: Optional[str] = None


class Category(CategoryBase, table=True):
  __tablename__ = "categories"
  id: Optional[int] = Field(default=None, primary_key=True)
  is_active: bool = Field(default=True)
  deleted_at: Optional[datetime] = Field(default=None)

  services: List["Service"] = Relationship(back_populates="category")


class CategoryCreate(CategoryBase):
  pass


class CategoryUpdate(SQLModel):
  name: Optional[str] = None
  description: Optional[str] = None
  is_active: Optional[bool] = None
