from .models import *
from .session_postgres import create_postgres_session
from .startup_data import load_initial_groups


def get_db():
    from .session_postgres import get_postgres_db

    yield from get_postgres_db()
