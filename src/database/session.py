from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config.config import Settings

settings = Settings()
engine = create_engine(settings.DATABASE_URL)
PostgreSQLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = PostgreSQLSessionLocal()
    try:
        yield db
    finally:
        db.close()
