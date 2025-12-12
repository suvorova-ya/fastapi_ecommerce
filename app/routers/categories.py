from email.policy import default
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categories import Category as CategoryModel
from app.models.users import User as UserModel
from app.schemas.categories import CategoryCreate, Category as CategoryShema
from app.db.db_depends import get_async_db
from app.routers.router_depens import valid_category_id
from app.auth.user import get_current_admin

# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/", response_model=List[CategoryShema])
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Доступ: Разрешён всем (аутентификация не требуется).
    Описание: Возвращает список всех активных категорий товаров.
    Зависимости:
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
    Возвращает:
        List[CategorySchema]: Список всех активных категорий
    """
    result = await db.scalars(select(CategoryModel).where(CategoryModel.is_active == True))
    categories = result.all()
    return categories


@router.post("/", response_model=CategoryShema, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_async_db),
                          current_user: UserModel = Depends(get_current_admin)):
    """
    Доступ: только для администраторов
    Описание: Создаёт новую категорию товаров.
    Аргументы:
        category: Модель для создания категории
    Возвращает:
        CategorySchema: Созданная категория
    Исключения:
        400 Bad Request: Если родительская категория не существует или неактивна

    """
    # Проверка существования parent_id и что он не в "архиве", если указан
    if category.parent_id is not None:
        await valid_category_id(category.parent_id, db)

    # Создание новой категории
    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=CategoryShema)
async def update_category(category_id: int, category: CategoryCreate, db: AsyncSession = Depends(get_async_db),
                          current_user: UserModel = Depends(get_current_admin)):
    """
    Доступ: только для администраторов
    Описание: Обновляет категорию по её ID.
    Аргументы:
        category_id: ID категории для обновления
        category: Модель с данными для обновления категории
    Возвращает:
        CategorySchema: Обновленная категория
    Исключения:
        400 Bad Request: Если родительская категория не существует или категория ссылается сама на себя
        403 Forbidden: Если пользователь не имеет роли "admin"
        404 Not Found: Если категория не существует или неактивна
    """
    # Проверка существования категории
    db_category = await valid_category_id(category_id, db)

    # Проверка существование parent_id если указан
    if category.parent_id is not None:
        try:
            parent = await valid_category_id(category.parent_id, db)

            if parent.id == category_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Category cannot be its own parent")
        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent category not found")
            raise e

    # Обновление категории
    await db.execute(
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(**category.model_dump())
    )
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_async_db),
                          current_user: UserModel = Depends(get_current_admin)):
    """
    Доступ: только для администраторов
    Описание: Выполняет мягкое удаление категории по её ID, устанавливая is_active=False.
    Аргументы:
        category_id: ID категории для удаления
    Возвращает:
        dict: Сообщение об успешном удалении
    Исключения:
        404 Not Found: Если категория не существует или уже неактивна
    """
    await valid_category_id(category_id, db)
    await db.execute(update(CategoryModel).where(CategoryModel.id == category_id).values(is_active=False))
    await db.commit()
    return {"status": "success", "message": f"Category {category_id} marked as inactive"}
