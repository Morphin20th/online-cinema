from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.dependencies import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL)
PostgreSQLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = PostgreSQLSessionLocal()
    try:
        yield db
    finally:
        db.close()
