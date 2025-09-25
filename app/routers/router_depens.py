from fastapi import  Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user import get_current_seller, get_current_buyer, get_current_user
from app.db.db_depends import get_async_db
from app.models import Product as ProductModel, Category as CategoryModel
from app.models import User as UserModel
from app.models import Review as ReviewModel



async def valid_category_id(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Описание:Проверяет существование category_id и что она не в "архиве
    Аргументы:
        category_id: ID категории для фильтрации
    Зависимости:
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
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
    Зависимости:
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
    Возвращает: товар
    """
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id,
                                                 ProductModel.is_active == True))
    db_product = result.first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")
    return db_product


async def product_owner_access(product:int = Depends(valid_product_id),
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



async def recalculate_rating(product_id:int, db: AsyncSession = Depends(get_async_db)):
    """
     Описание:После добавления отзыва пересчитывает средний рейтинг товара (rating в таблице products)
            на основе всех активных оценок (grade) для этого товара.
     Аргументы:
            product_id: ID продукта по которому фильтруются колонка grade
     Зависимости:
            db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
     Возвращает: средний рейтинг товара
    """
    rating = await db.scalar(select(func.avg(ReviewModel.grade)).where(ReviewModel.product_id == product_id,
                                                                       ReviewModel.is_active == True))
    avg_grades = round(rating,2) or 0.0
    return avg_grades



