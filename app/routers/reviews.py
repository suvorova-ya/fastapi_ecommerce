from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.router_depens import valid_product_id, recalculate_rating
from app.schemas.reviews import ReviewsCreate, Reviews as ReviewsShema
from app.models.reviews import Review as ReviewModel
from app.models.products import Product as ProductModel
from app.models.users import User as UserModel
from app.db.db_depends import get_async_db
from app.auth.user import get_current_buyer, get_current_user, get_current_admin

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)


@router.get("/", response_model=List[ReviewsShema])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Доступ: Разрешён всем (аутентификация не требуется).
    Описание: Возвращает список всех активных отзывов (is_active = True) о товарах.
    Возвращает:
        List[ReviewSchema]: Список всех активных отзывов
    """
    reviews = await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    return reviews.all()


@router.get("/products/{product_id}", response_model=List[ReviewsShema])
async def get_product_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Доступ: Разрешён всем (аутентификация не требуется).
    Описание: Получение отзывов о конкретном товаре.
    Аргументы:
        product_id: ID товара для фильтрации отзывов
    Возвращает:
        List[ReviewSchema]: Список активных отзывов для данного товара
    Исключения:
        404 Not Found: Если товар не существует или неактивен.
    """
    # проверяем что товар существует и активен
    await db.scalar(select(ProductModel).where(ProductModel.id == product_id,
                                               ProductModel.is_active == True))

    reviews = await db.scalars(select(ReviewModel).where(ReviewModel.product_id == product_id,
                                                         ReviewModel.is_active == True))
    return reviews.all()


@router.post("/", response_model=ReviewsShema, status_code=status.HTTP_201_CREATED)
async def create_review(review: ReviewsCreate, db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_buyer)):
    """
    Доступ: Только аутентифицированные пользователи с ролью "buyer".
    Описание: Создаёт новый отзыв для указанного товара.
              После добавления отзыва пересчитывает средний рейтинг товара.
    Аргументы:
        review: Модель для создания отзыва
        current_user: Текущий аутентифицированный пользователь с ролью "buyer"
    Возвращает:
        ReviewSchema: Созданный отзыв
    Исключения:
        400 Bad Request: Если пользователь уже оставил отзыв на этот товар
        403 Forbidden: Если пользователь не аутентифицирован или не имеет роли "buyer"
        404 Not Found: Если товар не существует или неактивен
        422 Unprocessable Entity: Если grade вне диапазона 1–5
    """
    # проверяем что товар существует и активен
    await valid_product_id(review.product_id, db)

    # проверяем что отзыва еще нет
    existing_review = await db.scalar(select(ReviewModel).where(ReviewModel.product_id == review.product_id,
                                                                ReviewModel.user_id == current_user.id))
    if existing_review:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The review already exists")

    #  сохраняем отзыв
    review_db = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(review_db)
    await db.commit()
    await db.refresh(review_db)

    #  пересчитываем и обновляем рейтинг
    avg_rating = await recalculate_rating(review.product_id, db)
    await db.execute(update(ProductModel).where(ProductModel.id == review.product_id).values(rating=avg_rating))
    await db.commit()

    return review_db


@router.delete("/{review_id}")
async def delete_review(review_id: int, db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_admin)):
    """
        Доступ: Только пользователи с ролью "admin".
        Описание: Выполняет мягкое удаление отзыва по review_id, устанавливая is_active = False.
                  После удаления пересчитывает рейтинг товара на основе оставшихся активных отзывов.
        Аргументы:
            review_id: ID отзыва для удаления
        Зависимости:
            current_user: Текущий аутентифицированный пользователь
        Возвращает:
            dict: Сообщение об успешном удалении
        Исключения:
            403 Forbidden: Если пользователь не имеет роли "admin"
            404 Not Found: Если отзыв не существует или уже неактивен
    """

    review = await db.scalar(select(ReviewModel).where(ReviewModel.id == review_id,
                                                       ReviewModel.is_active == True))
    # проверяем что отзыв существует и активен
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or already inactive")

    # сохраняем id продукта до удаления
    product_id = review.product_id

    # обновляем отзыв со статусом is_active=False
    await db.execute(update(ReviewModel).where(ReviewModel.id == review_id).values(is_active=False))
    await db.commit()

    #  пересчитываем и обновляем рейтинг
    avg_rating = await recalculate_rating(product_id, db)
    await db.execute(update(ProductModel).where(ProductModel.id == product_id).values(rating=avg_rating))
    await db.commit()

    return {"message": "Review deleted"}
