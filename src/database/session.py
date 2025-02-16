import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from database.models.base import Base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'cinema.db')}"

sqlite_engine = create_engine(
    SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
)
sqlite_connection = sqlite_engine.connect()
SqliteSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sqlite_connection
)


def get_db() -> Session:
    db = SqliteSessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_sqlite_database():
    with sqlite_connection.begin():
        Base.metadata.drop_all(bind=sqlite_connection)
        Base.metadata.create_all(bind=sqlite_connection)
