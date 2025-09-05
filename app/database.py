from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Строка подключения для SQLite
DATABASE_URL = "sqlite:///ecommerce.db"

# Создаём Engine
engine = create_engine(DATABASE_URL, echo=True)

#Настраиваем фабрику сессий
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

