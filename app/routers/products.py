from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Product as ProductModel, Category as CategoryModel
from app.routers.router_depens import valid_category_id, valid_product_id
from app.schemas import Product as ProductShema, ProductCreate
from app.db_depends import get_db


# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix="/products",
    tags=["products"],
)




@router.get("/", response_model=List[ProductShema], status_code=status.HTTP_200_OK)
async def get_all_products(db: Session = Depends(get_db)):
    """
    Возвращает список всех товаров.
    """
    stmt = select(ProductModel).where(ProductModel.is_active==True)
    products = db.scalars(stmt).all()
    return products


@router.post("/", response_model=ProductShema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создаёт новый товар.
    """
    # Проверяет существование category_id и что она не в "архиве"
    valid_category_id(product.category_id,db)

    #Создаёт товар с полями из ProductCreate
    db_products = ProductModel(**product.model_dump())
    db.add(db_products)
    db.commit()
    db.refresh(db_products)
    return db_products


@router.get("/category/{category_id}", response_model=list[ProductShema] ,status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    #Проверяет, существует ли категория с указанным category_id и она не в архиве
    valid_category_id(category_id, db)

    #Возвращает список всех товаров
    stmt_pr = select(ProductModel).where(ProductModel.category_id == category_id,
                                         ProductModel.is_active == True)
    db_products = db.scalars(stmt_pr).all()
    return db_products



@router.get("/{product_id}", response_model=ProductShema, status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    return valid_product_id(product_id,db)


@router.put("/{product_id}", response_model=ProductShema)
async def update_product(product_id: int, product: ProductCreate,  db: Session =Depends(get_db)):
    """
    Обновляет товар по его ID.
    """
    # Проверяет, существует ли активный товар с указанным product_id
    db_product = valid_product_id(product_id, db)

    #Проверяет, существует ли категория с указанным category_id и она не в архиве
    valid_category_id(product.category_id, db)

    #Обновляем товар
    db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump())
    )
    db.commit()
    db.refresh(db_product)
    return db_product



@router.delete("/{product_id}",status_code=status.HTTP_200_OK)
async def delete_product(product_id: int,  db: Session = Depends(get_db)):
    """
    Удаляет товар по его ID.
    """
    # Проверяет, существует ли активный товар с указанным product_id
    valid_product_id(product_id, db)
    db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(is_active=False))
    db.commit()
    return {"status": "success", "message": "Product marked as inactive"}