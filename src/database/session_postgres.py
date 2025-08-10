from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text, Connection
from sqlalchemy.orm import sessionmaker, Session

from src.config import get_settings
from src.database import Base

settings = get_settings()

POSTGRES_DATABASE_URL = str(settings.DATABASE_URL)
engine = create_engine(POSTGRES_DATABASE_URL)
postgres_connection = engine.connect()
PostgreSQLSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=postgres_connection
)


def get_postgres_db() -> Generator[Session, None, None]:
    db = PostgreSQLSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_postgres_db_contextmanager() -> Generator[Session, None, None]:
    db = PostgreSQLSessionLocal()
    try:
        yield db
    finally:
        db.close()


def load_user_groups(conn: Connection) -> None:
    conn.execute(
        text(
            "INSERT INTO user_groups(id, name) "
            "VALUES (1, 'ADMIN'), (2, 'USER'), (3, 'MODERATOR')"
            "ON CONFLICT(id) DO NOTHING"
        )
    )


def reset_postgres_database() -> None:
    with engine.connect() as connection:
        with connection.begin():
            Base.metadata.drop_all(bind=connection)
            Base.metadata.create_all(connection)
            load_user_groups(connection)
