from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара.
    Используется в POST и PUT запросах.
    """
    name: str = Field(min_length=3, max_length=100,
                      description="Название товара (3-100 символов)")
    description: Optional[str] = Field(None, max_length=500,
                                       description="Описание товара (до 500 символов)")
    price: float = Field(gt=0, description="Цена товара (больше 0)")
    image_url: Optional[str] = Field(None, max_length=200, description="URL изображения товара")
    stock: int = Field(ge=0, description="Количество товара на складе (0 или больше)")
    category_id: int = Field(description="ID категории, к которой относится товар")


class Product(ProductCreate):
    """
    Модель для ответа с данными товара.
    Используется в GET-запросах.
    """
    id: int = Field(description="Уникальный идентификатор товара")
    is_active: bool = Field(description="Активность товара")

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    """
    Список товаров для пагинации
    """
    items: List[Product] = Field(description="Товары для текущей стрваницы")
    total: int = Field(ge=0, description="Общее количество товаров")
    page: int = Field(ge=1, description="Номер текущей страницы")
    page_size: int = Field(ge=1, description="Количество элементов на странице")

    model_config = ConfigDict(from_attributes=True)  # Для чтения из ORM-объектов




