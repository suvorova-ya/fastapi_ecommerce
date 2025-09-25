from datetime import datetime

from pydantic import BaseModel, Field


class ReviewsCreate(BaseModel):
    product_id: int
    comment: str
    grade: int = Field(ge=1,le=5)


class Reviews(ReviewsCreate):
    id: int
    user_id: int
    comment_date: datetime
    is_active: bool