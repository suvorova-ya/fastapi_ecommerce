from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User as UserModel
from app.schemas import UserCreate,User as UserShema
from app.db.db_depends import get_asunc_db
from app.auth.password import hash_password, verify_password, create_access_token


router = APIRouter(prefix="/users", tags=["users"])



@router.post("/", response_model=UserShema, status_code=status.HTTP_201_CREATED)
async def create_user(user:UserCreate,db: AsyncSession = Depends(get_asunc_db)):
    """
    Регистрирует нового пользователя с ролью 'buyer' или 'seller'.
    """
    user_email = await db.scalar(select(UserModel).where(UserModel.email == user.email))

    if user_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Создание объекта пользователя с хешированным паролем
    db_user = UserModel(
        email = user.email,
        hashed_password = hash_password(user.password),
        role = user.role
    )
    # Добавление в сессию и сохранение в базе
    db.add(db_user)
    await db.commit()
    return db_user


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_asunc_db)):
    """
       Аутентифицирует пользователя и возвращает JWT с email, role и id.
    """
    #SQL-запрос, который ищет запись в таблице users, где поле email совпадает с переданным form_data.username
    user = await db.scalar(select(UserModel).where(UserModel.email == form_data.username))
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub" : user.email, "role": user.role, "id": user.id} )
    return {"access_token": access_token, "token_type": "bearer"}