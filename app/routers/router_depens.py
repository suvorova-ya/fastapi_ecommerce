from fastapi import Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_depends import get_db
from app.models import Product as ProductModel, Category as CategoryModel



def valid_category_id(category_id: int , db: Session = Depends(get_db)):
    """ Проверяет существование category_id и что она не в "архиве"""
    stmt = select(CategoryModel).where(CategoryModel.id == category_id,
                                       CategoryModel.is_active == True)
    db_category = db.scalars(stmt).first()
    if db_category is None:
        raise HTTPException(status_code=400, detail="Category_id not found")
    return db_category


def valid_product_id(product_id: int, db: Session = Depends(get_db)):
    """Проверяет, существует ли активный товар с указанным product_id и что он не в "архиве """
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    db_product = db.scalars(stmt).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product