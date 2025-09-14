from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker,AsyncSession
from sqlalchemy.orm import  DeclarativeBase


from app.db.config import settings


DATABASE_URL = settings.db_url


# Создаём Engine
async_engine = create_async_engine(DATABASE_URL, echo=True)

#Настраиваем фабрику сессий
async_session_maker = async_sessionmaker(bind=async_engine, expire_on_commit=False,class_=AsyncSession)

class Base(DeclarativeBase):
    pass


