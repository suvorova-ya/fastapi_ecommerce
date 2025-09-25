from datetime import datetime
from typing import Optional

from app.db.database import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey, Text, DateTime, Boolean, Integer


class Review(Base):
    __tablename__ = "reviews"
    id:Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    comment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    grade: Mapped[int] = mapped_column(Integer,nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean,default=True)
