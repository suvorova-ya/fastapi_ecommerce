from typing import List, Optional
from app.models.products import Product
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base



class Category(Base):
    __tablename__ = "categories"
    id : Mapped[int] = mapped_column(primary_key=True)
    name : Mapped[str] = mapped_column(String(50),nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    is_active : Mapped[bool] = mapped_column(Boolean, default=True)

    products: Mapped[List["Product"]] = relationship(back_populates="category")
    parent: Mapped[Optional["Category"]] = relationship(back_populates="children",remote_side="Category.id")
    children: Mapped[List["Category"]] = relationship(back_populates="parent")








