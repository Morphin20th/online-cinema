from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.accounts import UserGroupModel, UserGroupEnum
from src.database.session_postgres import PostgreSQLSessionLocal


def load_initial_groups(session: Session):
    for group in UserGroupEnum:
        exists = session.execute(
            select(UserGroupModel).where(UserGroupModel.name == group)
        ).scalar_one_or_none()

        if not exists:
            print(f"Creating group: {group.value}")
            session.add(UserGroupModel(name=group))

    session.commit()


if __name__ == "__main__":
    with PostgreSQLSessionLocal() as session:
        load_initial_groups(session)
    print("Group initialization complete.")
