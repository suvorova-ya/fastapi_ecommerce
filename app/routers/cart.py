from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.user import get_current_user
from app.db.db_depends import get_async_db
from app.models.cart_items import CartItem as CartItemModel
from app.models.products import Product as ProductModel
from app.models.users import User as UserModel
from app.routers.router_depens import _ensure_product_available, _get_cart_item
from app.schemas.cart_items import (
    Cart as CartSchema,
    CartItem as CartItemSchema,
    CartItemCreate,
    CartItemUpdate,
)

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartSchema)
async def get_cart(
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
     Описание: Получает содержимое корзины текущего аутентифицированного пользователя
               с расчетом общей стоимости и количества товаров
     Аргументы:
             db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
             current_user: текущий аутентифицированный пользователь
     Зависимости:
             get_current_user: проверка аутентификации и получение текущего пользователя
     Возвращает: объект CartSchema с данными корзины
     """
    result = await db.scalars(
        select(CartItemModel)
        .options(selectinload(CartItemModel.product))
        .where(CartItemModel.user_id == current_user.id)
        .order_by(CartItemModel.id)
    )
    items = result.all()

    total_quantity = sum(item.quantity for item in items)
    price_items = (
        Decimal(item.quantity) *
        (item.product.price if item.product.price is not None else Decimal("0"))
        for item in items
    )
    total_price_decimal = sum(price_items, Decimal("0"))

    return CartSchema(
        user_id=current_user.id,
        items=items,
        total_quantity=total_quantity,
        total_price=total_price_decimal
    )


@router.post("/items", response_model=CartItemSchema, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
        payload: CartItemCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
        Описание: Добавляет товар в корзину текущего пользователя или увеличивает его количество,
                  если товар уже присутствует в корзине
        Аргументы:
                payload: данные для добавления товара (product_id и quantity)
                db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
                current_user: текущий аутентифицированный пользователь
        Зависимости:
               get_current_user: проверка аутентификации и получение текущего пользователя
        Возвращает: объект CartItemSchema с данными добавленного/обновленного элемента корзины
        """
    # Проверка на то что, продавец не может покупать свои товары.
    product = await db.get(ProductModel, payload.product_id)

    if product.seller_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы не можете купить собственный товар."
        )

    await _ensure_product_available(db, payload.product_id)

    cart_item = await _get_cart_item(db, current_user.id, payload.product_id)
    if cart_item:
        cart_item.quantity += payload.quantity
    else:
        cart_item = CartItemModel(
            user_id=current_user.id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
        db.add(cart_item)

    await db.commit()
    updated_item = await _get_cart_item(db, current_user.id, payload.product_id)
    return updated_item


@router.put("/items/{product_id}", response_model=CartItemSchema)
async def update_cart_item(
        product_id: int,
        payload: CartItemUpdate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
       Описание: Обновляет количество указанного товара в корзине текущего пользователя
       Аргументы:
               product_id: ID товара для обновления в корзине
               payload: новые данные с обновленным количеством товара (quantity)
               db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
               current_user: текущий аутентифицированный пользователь
       Зависимости:
               get_current_user: проверка аутентификации и получение текущего пользователя
       Возвращает: объект CartItemSchema с обновленными данными элемента корзины
       """
    await _ensure_product_available(db, product_id)

    cart_item = await _get_cart_item(db, current_user.id, product_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    cart_item.quantity = payload.quantity
    await db.commit()
    updated_item = await _get_cart_item(db, current_user.id, product_id)
    return updated_item


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(
        product_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
        Описание: Удаляет указанный товар из корзины текущего пользователя
        Аргументы:
                product_id: ID товара для удаления из корзины
                current_user: текущий аутентифицированный пользователь
        Зависимости:
               get_current_user: проверка аутентификации и получение текущего пользователя
        Возвращает: HTTP-статус 204 (No Content) при успешном удалении
        """
    cart_item = await _get_cart_item(db, current_user.id, product_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    await db.delete(cart_item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
        Описание: Полностью очищает корзину текущего пользователя
        Аргументы:
                db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
                current_user: текущий аутентифицированный пользователь
        Зависимости:
                get_async_db: получение асинхронной сессии БД
                get_current_user: проверка аутентификации и получение текущего пользователя
        Возвращает: HTTP-статус 204 (No Content) при успешной очистке корзины
        """

    await db.execute(delete(CartItemModel).where(CartItemModel.user_id == current_user.id))
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
