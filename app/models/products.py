from typing import Optional

from sqlalchemy import String, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.database import Base



class Product(Base):
    __tablename__ = 'products'
    id : Mapped[int] = mapped_column(primary_key=True)
    name : Mapped[str] = mapped_column(String(100),nullable=False)
    description:Mapped[Optional[str]] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Float,nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(200))
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active : Mapped[bool] = mapped_column(Boolean,default=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    category: Mapped["Category"] = relationship(back_populates="products")









