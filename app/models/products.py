from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base



class Product(Base):
    __tablename__ = 'products'
    id : Mapped[int] = mapped_column(primary_key=True)
    name : Mapped[str] = mapped_column(String(100),nullable=False)
    description: Optional[Mapped[str|None]] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Float,nullable=False)
    image_url: Mapped[Optional[str|None]] = mapped_column(String(200))
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active : Mapped[bool] = mapped_column(Boolean,default=True)



class Movie(Base):
    __tablename__ = "movies"

    id : Mapped[int] = mapped_column(primary_key=True)
    title : Mapped[str] = mapped_column(String(200), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    release_date : Mapped[Optional[datetime]] = mapped_column(DateTime,nullable=True)






