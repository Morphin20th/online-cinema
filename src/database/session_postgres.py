from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import Settings, settings


def create_postgres_session(project_settings: Settings):
    database_url = str(project_settings.DATABASE_URL)
    engine = create_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


PostgreSQLSessionLocal = create_postgres_session(settings)


def get_postgres_db() -> Generator[Session, Any, None]:
    db = PostgreSQLSessionLocal()
    try:
        yield db
    finally:
        db.close()
