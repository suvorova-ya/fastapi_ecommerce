from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product as ProductModel
from app.models import User as UserModel
from app.routers.router_depens import valid_category_id, valid_product_id
from app.schemas import Product as ProductShema, ProductCreate
from app.db.db_depends import get_asunc_db
from  app.auth.user import get_current_seller


# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix="/products",
    tags=["products"],
)




@router.get("/", response_model=List[ProductShema])
async def get_all_products(db: AsyncSession = Depends(get_asunc_db)):
    """
    Возвращает список всех товаров.
    """
    result = await db.scalars(select(ProductModel).where(ProductModel.is_active==True))
    return result.all()


@router.post("/", response_model=ProductShema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate,
                         db: AsyncSession = Depends(get_asunc_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
    Создаёт новый товар.
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
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_asunc_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    #Проверяет, существует ли категория с указанным category_id и она не в архиве
    await valid_category_id(category_id, db)

    #Возвращает список всех товаров
    products = await db.scalars(select(ProductModel).where(ProductModel.category_id == category_id,
                                         ProductModel.is_active == True))

    return products.all()



@router.get("/{product_id}", response_model=ProductShema, status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: AsyncSession = Depends(get_asunc_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    # Проверяем, существует ли активный товар
    product = await valid_product_id(product_id,db)

    # Проверяем, существует ли активная категория
    await valid_category_id(product.category_id, db)
    return product


@router.put("/{product_id}", response_model=ProductShema)
async def update_product(product_id: int, product: ProductCreate, db: AsyncSession = Depends(get_asunc_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
    Обновляет товар по его ID.
    """
    # Проверяет, существует ли активный товар с указанным product_id
    db_product = await valid_product_id(product_id, db, current_user)

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
async def delete_product(product_id: int,  db: AsyncSession = Depends(get_asunc_db),
                         current_user: UserModel = Depends(get_current_seller)  ):
    """
    Удаляет товар по его ID.
    """
    # Проверяет, существует ли активный товар с указанным product_id
    product = await valid_product_id(product_id, db, current_user)
    # Проверяем, существует ли активная категория
    await valid_category_id(product.category_id, db)

    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(is_active=False))
    await db.commit()
    return {"status": "success", "message": "Product marked as inactive"}