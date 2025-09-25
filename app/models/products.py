from typing import Optional

from sqlalchemy import String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base




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
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating :Mapped[float] = mapped_column(Float, default=0.0) # Средний рейтинг товара

    category: Mapped["Category"] = relationship(back_populates="products")
    seller = relationship("User", back_populates="products")  # New















