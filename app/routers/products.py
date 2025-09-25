from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product as ProductModel
from app.models import User as UserModel
from app.routers.router_depens import valid_category_id, valid_product_id
from app.schemas.products import ProductCreate, Product as ProductShema
from app.db.db_depends import get_async_db
from  app.auth.user import get_current_seller


# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix="/products",
    tags=["products"],
)



@router.get("/", response_model=List[ProductShema])
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """
    Доступ: Разрешён всем (аутентификация не требуется).
    Описание: Возвращает список всех активных товаров.
    Зависимости:
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
    Возвращает:
        List[ProductSchema]: Список всех активных товаров
    """
    result = await db.scalars(select(ProductModel).where(ProductModel.is_active==True))
    return result.all()


@router.post("/", response_model=ProductShema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate,
                         db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
    Доступ: Только аутентифицированные пользователи с ролью "seller".
    Описание: Создаёт новый товар, привязанный к текущему продавцу.
    Аргументы:
        product: Модель для создания товара
    Зависимости:
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
        current_user: Текущий аутентифицированный пользователь с ролью "seller"
    Возвращает:
        ProductSchema: Созданный товар
    Исключения:
        403 Forbidden: Если пользователь не аутентифицирован или не имеет роли "seller"
        404 Not Found: Если категория не существует или неактивна
    """
    # Проверяет существование category_id и что она не в "архиве"
    await valid_category_id(product.category_id,db)

    #Создаёт товар с полями из ProductCreate
    db_product = ProductModel(**product.model_dump(), seller_id = current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductShema] ,status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Доступ: Разрешён всем (аутентификация не требуется).
    Описание: Возвращает список товаров в указанной категории по её ID.
    Аргументы:
        category_id: ID категории для фильтрации товаров
    Зависимости:
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
    Возвращает:
        List[ProductSchema]: Список активных товаров в указанной категории
    Исключения:
        404 Not Found: Если категория не существует или неактивна
    """
    #Проверяет, существует ли категория с указанным category_id и она не в архиве
    await valid_category_id(category_id, db)

    #Возвращает список всех товаров
    products = await db.scalars(select(ProductModel).where(ProductModel.category_id == category_id,
                                         ProductModel.is_active == True))

    return products.all()



@router.get("/{product_id}", response_model=ProductShema, status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Доступ: Разрешён всем (аутентификация не требуется).
    Описание: Возвращает детальную информацию о товаре по его ID.
    Аргументы:
        product_id: ID товара для получения информа
    Зависимости:
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
    Возвращает:
        ProductSchema: Детальная информация о товаре
    Исключения:
        404 Not Found: Если товар не существует или неактивен
    """
    # Проверяем, существует ли активный товар
    product = await valid_product_id(product_id,db)

    # Проверяем, существует ли активная категория
    await valid_category_id(product.category_id, db)
    return product


@router.put("/{product_id}", response_model=ProductShema)
async def update_product(product_id: int, product: ProductCreate, db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
    Доступ: Только аутентифицированные пользователи с ролью "seller".
    Описание: Обновляет товар, если он принадлежит текущему продавцу.
    Аргументы:
        product_id: ID товара для обновления
        product: Модель с данными для обновления товара
    Зависимости:
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
        current_user: Текущий аутентифицированный пользователь с ролью "seller"
    Возвращает:
        ProductSchema: Обновленный товар
    Исключения:
        403 Forbidden: Если товар не принадлежит текущему пользователю
        404 Not Found: Если товар или категория не существуют или неактивны
    """
    # Проверяет, существует ли активный товар с указанным product_id
    db_product = await valid_product_id(product_id, db)

    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")

    #Проверяет, существует ли категория с указанным category_id и она не в архиве
    await valid_category_id(product.category_id, db)

    #Обновляем товар
    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump())
    )
    await db.commit()
    await db.refresh(db_product)
    return db_product



@router.delete("/{product_id}",status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
    Доступ: Только аутентифицированные пользователи с ролью "seller".
    Описание: Выполняет мягкое удаление товара, если он принадлежит текущему продавцу.
    Аргументы:
        product_id: ID товара для удаления
    Зависимости:
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
        current_user: Текущий аутентифицированный пользователь с ролью "seller"
    Возвращает:
        dict: Сообщение об успешном удалении
    Исключения:
        403 Forbidden: Если товар не принадлежит текущему пользователю
        404 Not Found: Если товар не существует или неактивен
    """
    # Проверяет, существует ли активный товар с указанным product_id
    product = await valid_product_id(product_id, db)
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")

    # Проверяем, существует ли активная категория
    await valid_category_id(product.category_id, db)

    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(is_active=False))
    await db.commit()

    return {"status": "success", "message": "Product marked as inactive"}