from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class CategoryCreate(BaseModel):
    """
    Модель для создания и обновления категории.
    Используется в POST и PUT запросах.
    """
    name: str = Field(min_length=3, max_length=50,
                      description="Название категории (3-50 символов)")
    parent_id: Optional[int] = Field(None, description="ID родительской категории, если есть")


class Category(CategoryCreate):
    """
    Модель для ответа с данными категории.
    Используется в GET-запросах.
    """
    id: int = Field(description="Уникальный идентификатор категории")
    is_active: bool = Field(description="Активность категории")

    model_config = ConfigDict(from_attributes=True)
