from typing import List

from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy import update, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categories import Category as CategoryModel
from app.schemas import Category as CategoryShema, CategoryCreate
from app.db.db_depends import get_asunc_db
from app.routers.router_depens  import valid_category_id


# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/",response_model=List[CategoryShema])
async def get_all_categories(db: AsyncSession = Depends(get_asunc_db)):
    """
    Возвращает список всех категорий товаров.
    """
    result = await db.scalars(select(CategoryModel).where(CategoryModel.is_active == True))
    categories = result.all()
    return categories


@router.post("/", response_model=CategoryShema, status_code=status.HTTP_201_CREATED)
async def create_category(category:CategoryCreate, db: AsyncSession = Depends(get_asunc_db)):
    """
    Создаёт новую категорию.
    """
    # Проверка существования parent_id и что он не в "архиве", если указан
    if category.parent_id is not None:
        await valid_category_id(category.parent_id,db)

    # Создание новой категории
    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.put("/{category_id}",response_model=CategoryShema)
async def update_category(category_id: int, category: CategoryCreate, db: AsyncSession = Depends(get_asunc_db)):
    """
    Обновляет категорию по её ID.
    """
    #Проверка существования категории
    db_category = await valid_category_id(category_id, db)

    #Проверка существование parent_id если указан

    parent = await valid_category_id(category.parent_id, db)
    if parent is None:
        raise HTTPException(status_code=400, detail="Parent not found")

    #Обновление категории
    await db.execute(
        update(CategoryModel)
        .where(CategoryModel.id == category_id)
        .values(**category.model_dump())
    )
    await db.commit()
    await db.refresh(db_category)
    return db_category



@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_asunc_db)):
    """
    Удаляет категорию по её ID, устанавливая is_active=False.
    """
    await valid_category_id(category_id,db)
    await db.execute(update(CategoryModel).where(CategoryModel.id == category_id).values(is_active = False))
    await db.commit()
    return {"status": "success", "message": f"Category {category_id} marked as inactive"}