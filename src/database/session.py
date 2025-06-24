from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import Settings

settings = Settings()
database_url = str(settings.DATABASE_URL)
engine = create_engine(database_url)
PostgreSQLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, Any, None]:
    db = PostgreSQLSessionLocal()
    try:
        yield db
    finally:
        db.close()
