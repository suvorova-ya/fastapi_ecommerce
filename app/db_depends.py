from sqlalchemy.orm import Session
from fastapi import Depends

from app.database import SessionLocal

def get_db() -> Session:
    """
       Зависимость для получения сессии базы данных.
       Создаёт новую сессию для каждого запроса и закрывает её после обработки.
       """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

