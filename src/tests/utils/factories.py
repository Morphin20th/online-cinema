from sqlalchemy.orm import Session

from src.database import UserModel, RefreshTokenModel
from src.security import JWTAuthInterface


def _create_user(
    db: Session, jwt_manager: JWTAuthInterface, email: str, password: str, group_id: int
) -> UserModel:
    user = UserModel.create(email, password, group_id)
    user.is_active = True
    db.add(user)
    db.flush()

    token = jwt_manager.create_refresh_token(data={"user_id": user.id})
    refresh_token = RefreshTokenModel.create(user_id=user.id, token=token, days=1)
    db.add(refresh_token)

    db.commit()
    db.refresh(user)
    return user


def create_user(
    db: Session,
    jwt_manager: JWTAuthInterface,
    email="test@user.com",
    password="Test1234!",
) -> UserModel:
    return _create_user(db, jwt_manager, email, password, 2)


def create_admin(
    db: Session,
    jwt_manager: JWTAuthInterface,
    email="test@admin.com",
    password="Test1234!",
) -> UserModel:
    return _create_user(db, jwt_manager, email, password, 1)


def create_moderator(
    db: Session,
    jwt_manager: JWTAuthInterface,
    email="test@moder.com",
    password="Test1234!",
) -> UserModel:
    return _create_user(db, jwt_manager, email, password, 3)
