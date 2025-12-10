from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product as ProductModel, User as UserModel
from app.routers.router_depens import valid_category_id, valid_product_id
from app.schemas.products import ProductCreate, Product as ProductShema, ProductList
from app.db.db_depends import get_async_db
from app.auth.user import get_current_seller


# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=ProductList)
async def get_all_products(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        category_id: int | None = Query(
            None, description="ID категории для фильтрации"),
        search: str | None = Query(None, min_length=1, description="Поиск по названию товара"),
        min_price: float | None = Query(
            None, ge=0, description="Минимальная цена товара"),
        max_price: float | None = Query(
            None, ge=0, description="Максимальная цена товара"),
        in_stock: bool | None = Query(
            None, description="true — только товары в наличии, false — только без остатка"),
        seller_id: int | None = Query(
            None, description="ID продавца для фильтрации"),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Доступ: Разрешён всем (аутентификация не требуется).
    Описание: Возвращает список всех активных товаров с поддержкой фильтров.
    """
    # Проверка логики min_price <= max_price
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price не может быть больше max_price",
        )

    # Формируем список фильтров
    filters = [ProductModel.is_active.is_(True)]

    if category_id is not None:
        filters.append(ProductModel.category_id == category_id)
    if min_price is not None:
        filters.append(ProductModel.price >= min_price)
    if max_price is not None:
        filters.append(ProductModel.price <= max_price)
    if in_stock is not None:
        filters.append(ProductModel.stock > 0 if in_stock else ProductModel.stock == 0)
    if seller_id is not None:
        filters.append(ProductModel.seller_id == seller_id)

    # Базовый запрос total
    total_stmt = select(func.count()).select_from(ProductModel).where(*filters)

    rank_col = None
    if search:
        search_value = search.strip()
        if search_value:
            ts_query = func.websearch_to_tsquery('english', search_value)
            filters.append(ProductModel.tsv.op('@@')(ts_query))
            rank_col = func.ts_rank_cd(ProductModel.tsv, ts_query).label("rank")
            total_stmt = select(func.count()).select_from(ProductModel).where(*filters)

    total = await db.scalar(total_stmt) or 0

    # Основной запрос (если есть поиск — добавим ранг в выборку и сортировку)
    if rank_col is not None:
        products_stmt = (select(ProductModel, rank_col).where(*filters)
                         .order_by(desc(rank_col), ProductModel.id).offset((page - 1) * page_size).limit(page_size)
                         )
        result = await db.execute(products_stmt)
        rows = result.all()
        items = [row[0] for row in rows]
    else:
        products_stmt = (select(ProductModel).where(*filters)
                         .order_by(ProductModel.id).offset((page - 1) * page_size).limit(page_size)
                         )
        items = (await db.scalars(products_stmt)).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


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
    await valid_category_id(product.category_id, db)

    # Создаёт товар с полями из ProductCreate
    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductShema], status_code=status.HTTP_200_OK)
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
    # Проверяет, существует ли категория с указанным category_id и она не в архиве
    await valid_category_id(category_id, db)

    # Возвращает список всех товаров
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
    product = await valid_product_id(product_id, db)

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

    # Проверяет, существует ли категория с указанным category_id и она не в архиве
    await valid_category_id(product.category_id, db)

    # Обновляем товар
    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump())
    )
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
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
