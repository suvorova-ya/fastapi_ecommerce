import jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils import SECRET_KEY, ALGORITHM
from app.models.users import User as UserModel
from app.db.db_depends import get_async_db



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db:AsyncSession = Depends(get_async_db)):
    """
    Описание: Проверяет JWT токен и возвращает пользователя из базы данных.
              Выполняет проверку валидности токена, его срока действия и активного статуса пользователя.
    Аргументы:
        token: JWT токен из заголовка Authorization
        db: асинхронная сессия SQLAlchemy для работы с базой данных PostgreSQL
    Зависимости:
        oauth2_scheme: схема OAuth2 для извлечения токена из заголовка
        get_async_db: зависимость для получения асинхронной сессии БД
    Возвращает:
        UserModel: Объект аутентифицированного пользователя
    Исключения:
        401 Unauthorized: Если токен невалиден, просрочен или пользователь не найден/неактивен
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get('sub')
        if email is None:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    user = await db.scalar(select(UserModel).where(UserModel.email == email, UserModel.is_active == True))

    if user is None:
        raise credentials_exception
    return user


async def get_current_seller(current_user: UserModel = Depends(get_current_user)):
    """
    Описание: Проверяет, что аутентифицированный пользователь имеет роль продавца.
              Используется как зависимость для защиты эндпоинтов, доступных только продавцам.
    Аргументы:
        current_user: аутентифицированный пользователь из зависимости get_current_user
    Зависимости:
        get_current_user: зависимость для получения текущего пользователя
    Возвращает:
        UserModel: Объект пользователя с ролью "seller"
    Исключения:
        403 Forbidden: Если пользователь не имеет роли "seller"
        401 Unauthorized: Если пользователь не аутентифицирован (наследуется от get_current_user)
    """
    if current_user.role != "seller":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only sellers can perform this action")
    return current_user

async def get_current_buyer(current_user: UserModel = Depends(get_current_user)):
    """
    Описание: Проверяет, что аутентифицированный пользователь имеет роль покупателя.
              Используется как зависимость для защиты эндпоинтов, доступных только покупателям.
    Аргументы:
        current_user: аутентифицированный пользователь из зависимости get_current_user
    Зависимости:
        get_current_user: зависимость для получения текущего пользователя
    Возвращает:
        UserModel: Объект пользователя с ролью "buyer"
    Исключения:
        403 Forbidden: Если пользователь не имеет роли "buyer"
        401 Unauthorized: Если пользователь не аутентифицирован (наследуется от get_current_user)
     """
    if current_user.role != "buyer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only buyer can perform this action")
    return current_user


async def get_current_admin(current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can perform this action")
    return current_user
