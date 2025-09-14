from typing import List

from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy import update, select, and_
from sqlalchemy.orm import Session

from app.models.categories import Category as CategoryModel
from app.schemas import Category as CategoryShema, CategoryCreate
from app.db.db_depends import get_db


# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/",response_model=List[CategoryShema])
async def get_all_categories(db: Session = Depends(get_db)):
    """
    Возвращает список всех категорий товаров.
    """
    stmt = select(CategoryModel).where(CategoryModel.is_active == True)
    categories = db.scalars(stmt).all()
    return categories


@router.post("/", response_model=CategoryShema, status_code=status.HTTP_201_CREATED)
async def create_category(category:CategoryCreate, db: Session = Depends(get_db)):
    """
    Создаёт новую категорию.
    """
    # Проверка существования parent_id и что он не в "архиве", если указан
    if category.parent_id is not None:
        stmt = select(CategoryModel).where(and_(CategoryModel.id == category.parent_id,CategoryModel.parent_id == True))
        parent = db.scalars(stmt).first()
        if parent is None:
            raise HTTPException(status_code=400,detail='Parent category not found')

    # Создание новой категории
    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/{category_id}",response_model=CategoryShema)
async def update_category(category_id: int, category: CategoryCreate, db: Session = Depends(get_db)):
    """
    Обновляет категорию по её ID.
    """
    #Проверка существования категории
    stmt = select(CategoryModel).where(and_(CategoryModel.id == category_id, CategoryModel.parent_id == True))
    db_category = db.scalars(stmt).first()
    if db_category is None:
        raise HTTPException(status_code=400, detail="Category not found")

    #Проверка существование parent_id если указан
    parent_stmt = select(CategoryModel).where(CategoryModel.id == category.parent_id)
    parent = db.scalars(parent_stmt).first()
    if parent is None:
        raise HTTPException(status_code=400, detail="Parent not found")

    #Обновление категории
    db.execute(
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(**category.model_dump())
    )
    db.commit()
    db.refresh(db_category)
    return db_category



@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    Удаляет категорию по её ID, устанавливая is_active=False.
    """
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True)
    category = db.scalars(stmt).first()
    if category is None:
        raise HTTPException(status_code=404, detail='Category not found')
    db.execute(update(CategoryModel).where(CategoryModel.id == category_id).values(is_active = False))
    db.commit()

    return {"status": "success", "message": "Category marked as inactive"}