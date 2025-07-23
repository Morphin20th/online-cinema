from .models import *


def get_db():
    from .session_postgres import get_postgres_db

    yield from get_postgres_db()
