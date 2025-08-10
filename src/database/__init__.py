from typing import Generator

from sqlalchemy.orm import Session

from .models import *  # noqa
from .session_postgres import get_postgres_db_contextmanager


def get_db() -> Generator[Session, None, None]:
    from .session_postgres import get_postgres_db

    yield from get_postgres_db()


def reset_database() -> None:
    from .session_postgres import reset_postgres_database

    return reset_postgres_database()
