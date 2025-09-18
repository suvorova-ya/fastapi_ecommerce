import jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.config import SECRET_KEY, ALGORITHM
from app.models.users import User as UserModel
from app.db.db_depends import get_asunc_db



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

async def get_current_user(token: str = Depends(oauth2_scheme),db:AsyncSession = Depends(get_asunc_db)):
    """
    Проверяет JWT и возвращает пользователя из базы.
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

    user = await db.scalar(select(UserModel).where(UserModel.email == email, UserModel.is_active))

    if user is None:
        raise credentials_exception
    return user