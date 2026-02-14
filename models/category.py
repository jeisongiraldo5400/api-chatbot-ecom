from typing import Optional
from sqlmodel import SQLModel, Field


class CategoryBase(SQLModel):
  name: str = Field(unique=True, index=True)
  description: Optional[str] = None


class Category(CategoryBase, table=True):
  __tablename__ = "categories"
  id: Optional[int] = Field(default=None, primary_key=True)
  is_active: bool = Field(default=True)


class CategoryCreate(CategoryBase):
  pass


class CategoryUpdate(SQLModel):
  name: Optional[str] = None
  description: Optional[str] = None
  is_active: Optional[bool] = None
