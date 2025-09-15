from fastapi import  Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_depends import get_asunc_db
from app.models import Product as ProductModel, Category as CategoryModel



async def valid_category_id(category_id: int , db: AsyncSession = Depends(get_asunc_db)):
    """ Проверяет существование category_id и что она не в "архиве"""

    result = await db.scalars(select(CategoryModel).where(CategoryModel.id == category_id,
                                    CategoryModel.is_active == True))
    db_category = result.first()
    if db_category is None:
        raise HTTPException(status_code=400, detail="Category or parent not found or inactive")
    return db_category


async def valid_product_id(product_id: int, db: AsyncSession = Depends(get_asunc_db)):
    """Проверяет, существует ли активный товар с указанным product_id и что он не в "архиве """
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id,
                                                 ProductModel.is_active == True))
    db_product = result.first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    return db_product