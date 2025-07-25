from .models import *
from .session_postgres import get_postgres_db_contextmanager


def get_db():
    from .session_postgres import get_postgres_db

    yield from get_postgres_db()


def reset_database():
    from .session_postgres import reset_postgres_database

    return reset_postgres_database()
