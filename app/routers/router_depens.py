from fastapi import Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.user import get_current_seller
from app.db.db_depends import get_async_db
from app.models import Product as ProductModel, Category as CategoryModel
from app.models import User as UserModel
from app.models import Review as ReviewModel
from app.models import CartItem as CartItemModel


async def valid_category_id(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Описание:Проверяет существование category_id и что она не в "архиве
    Аргументы:
        category_id: ID категории для фильтрации
    Возвращает: ID категории
    """

    db_category = await db.scalar(select(CategoryModel).where(CategoryModel.id == category_id,
                                                              CategoryModel.is_active == True))
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return db_category


async def valid_product_id(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Описание: Проверяет, существует ли активный товар с указанным product_id
            и что текущий пользователь имеет к нему доступ
     Аргументы:
        product_id: ID товара для фильтрации
    Возвращает: товар
    """
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id,
                                                         ProductModel.is_active == True))
    db_product = result.first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")
    return db_product


async def product_owner_access(product: int = Depends(valid_product_id),
                               current_user: UserModel = Depends(get_current_seller)):
    """
   Описание: Проверяет, что текущий пользователь-продавец является владельцем товара
    Аргументы:
        product_id: ID товара для фильтрации
    Зависимости:
        current_user: Текущий аутентифицированный пользователь с ролью "seller"
    Возвращает: товар продавца
    """
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")
    return product


async def recalculate_rating(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
     Описание:После добавления отзыва пересчитывает средний рейтинг товара (rating в таблице products)
            на основе всех активных оценок (grade) для этого товара.
     Аргументы:
            product_id: ID продукта по которому фильтруются колонка grade
     Возвращает: средний рейтинг товара
    """
    rating = await db.scalar(select(func.avg(ReviewModel.grade)).where(ReviewModel.product_id == product_id,
                                                                       ReviewModel.is_active == True))
    avg_grades = round(rating, 2) or 0.0
    return avg_grades



async def _get_cart_item(
        db: AsyncSession, user_id: int, product_id: int
) -> CartItemModel | None:
    """
        Описание:
            Получает элемент корзины пользователя для конкретного товара.
            Выполняет поиск записи в корзине по идентификаторам пользователя и товара,
            с предварительной загрузкой связанных данных о товаре.
        Аргументы:
            user_id: ID пользователя, владельца корзины
            product_id: ID товара для поиска в корзине
        Возвращает:
            CartItemModel | None:
                - Объект CartItemModel с предзагруженным продуктом, если элемент найден
                - None, если элемент корзины не найден
    """
    result = await db.scalars(
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(
            CartItemModel.user_id == user_id,
            CartItemModel.product_id == product_id,
        )
    )
    return result.first()
