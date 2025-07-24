from src.database import get_db, UserModel


def _create_user(email: str, password: str, group_id: int) -> UserModel:
    db = get_db()
    user = UserModel.create(email, password, group_id)
    db.add(user)
    db.commit()
    db.refresh()
    return user


def create_user(email="test@user.com", password="Test1234!") -> UserModel:
    return _create_user(email, password, 2)


def create_admin(email="test@admin.com", password="Test1234!") -> UserModel:
    return _create_user(email, password, 1)


def create_moderator(email="test@moder.com", password="Test1234!") -> UserModel:
    return _create_user(email, password, 3)
