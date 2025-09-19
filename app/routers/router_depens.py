from fastapi import  Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user import get_current_seller
from app.db.db_depends import get_asunc_db
from app.models import Product as ProductModel, Category as CategoryModel
from app.models import User as UserModel



async def valid_category_id(category_id: int , db: AsyncSession = Depends(get_asunc_db)):
    """ Проверяет существование category_id и что она не в "архиве"""

    result = await db.scalars(select(CategoryModel).where(CategoryModel.id == category_id,
                                    CategoryModel.is_active == True))
    db_category = result.first()
    if db_category is None:
        raise HTTPException(status_code=400, detail="Category or parent not found or inactive")
    return db_category


async def valid_product_id(product_id: int, db: AsyncSession = Depends(get_asunc_db),
                           current_user: UserModel = Depends(get_current_seller)):
    """
    Проверяет, существует ли активный товар с указанным product_id
    и что текущий пользователь имеет к нему доступ
    """
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id,
                                                 ProductModel.is_active == True))
    db_product = result.first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")
    return db_product