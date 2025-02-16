import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

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
