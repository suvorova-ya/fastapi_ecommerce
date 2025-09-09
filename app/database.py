from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os


# Абсолютный путь к корню проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILENAME = "ecommerce.db"

# Строка подключения для SQLite
DB_PATH = os.path.join(BASE_DIR, DB_FILENAME)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Создаём Engine
engine = create_engine(DATABASE_URL, echo=True)

#Настраиваем фабрику сессий
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass


