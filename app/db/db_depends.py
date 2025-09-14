from sqlalchemy.orm import Session

from app.db.database import SessionLocal

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

