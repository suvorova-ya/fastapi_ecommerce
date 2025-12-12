import jwt
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User as UserModel
from app.schemas.users import UserCreate, User as UserSchema
from app.db.db_depends import get_async_db
from app.auth.password import hash_password, verify_password, create_access_token, create_refresh_token
from app.utils import COOKIE_NAME, COOKIE_PATH, COOKIE_HTTPONLY, COOKIE_SAMESITE, COOKIE_MAX_AGE, COOKIE_SECURE, \
    SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/create-admin", status_code=status.HTTP_201_CREATED)
async def create_admin(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
        Доступ: публичный (однократное использование)
        Описание: Регистрирует первого пользователя с ролью "admin" в системе.
                  Может быть использован только один раз для создания первоначального администратора.
        Аргументы:
            user: Данные для создания администратора (email и password)
        Возвращает:
            UserModel: Созданный объект администратора
        Исключения:
            403 Forbidden: Если администратор уже существует в системе
            400 Bad Request: Если email уже зарегистрирован
        """
    # проверяем что администратова еще нет в системе
    existing_admin = await db.scalar(select(UserModel).where(UserModel.role == "admin"))
    if existing_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator already exists")

    user_email = await db.scalar(select(UserModel).where(UserModel.email == user.email))
    if user_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Создание объекта пользователя с хешированным паролем
    db_user = UserModel(
        email=user.email,
        hashed_password=hash_password(user.password),
        role="admin"
    )
    # Добавление в сессию и сохранение в базе
    db.add(db_user)
    await db.commit()
    return db_user


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Доступ: публичный
    Описание: Регистрирует нового пользователя с ролью 'buyer' или 'seller'.
              Выполняет проверку уникальности email перед созданием пользователя.
    Аргументы:
        user: Данные для создания пользователя (email, password и role)
    Возвращает:
        UserSchema: Созданный объект пользователя
    Исключения:
        400 Bad Request: Если email уже зарегистрирован
    """
    user_email = await db.scalar(select(UserModel).where(UserModel.email == user.email))

    if user_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Создание объекта пользователя с хешированным паролем
    db_user = UserModel(
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role
    )
    # Добавление в сессию и сохранение в базе
    db.add(db_user)
    await db.commit()
    return db_user


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_db)):
    """
    Доступ: публичный
    Описание: Аутентифицирует пользователя и возвращает access_token и refresh_token.
              Refresh_token сохраняется в HTTP-only cookie для безопасности.
    Аргументы:
        form_data: Данные формы аутентификации (username=email, password)
    Возвращает:
        JSONResponse: Access token в теле ответа и refresh token в cookie
    Исключения:
        401 Unauthorized: Если email или пароль неверны
    """
    # SQL-запрос, который ищет запись в таблице users, где поле email совпадает с переданным form_data.username
    user = await db.scalar(select(UserModel).where(UserModel.email == form_data.username))
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role, "id": user.id})
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key=COOKIE_NAME,
        value=refresh_token,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
        max_age=COOKIE_MAX_AGE
    )

    return response


@router.post("/refresh-token")
async def refresh_access_token(request: Request, db: AsyncSession = Depends(get_async_db)):
    """
    Доступ: аутентифицированные пользователи (через refresh token)
    Описание: Обновляет access_token с помощью валидного refresh_token из cookie.
              Выполняет проверку валидности refresh token и активного статуса пользователя.
    Аргументы:
        request: HTTP запрос для извлечения refresh token из cookie
    Возвращает:
        dict: Новый access token
    Исключения:
        401 Unauthorized: Если refresh token отсутствует, невалиден или пользователь неактивен
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    refresh_token = request.cookies.get(COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.exceptions:
        raise jwt.exceptions
    user = await db.scalar(select(UserModel).where(UserModel.email == email, UserModel.is_active == True
                                                   ))
    if not user:
        raise credentials_exception

    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}
