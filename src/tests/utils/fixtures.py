from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database import (
    UserModel,
    UserProfileModel,
    DirectorModel,
    CertificationModel,
    StarModel,
    MovieModel,
    GenreModel,
    CartModel,
    CartItemModel,
    PurchaseModel,
)
from src.security import JWTAuthInterface
from src.tests.utils.utils import make_user_payload


def _get_access_token(user_id: int, jwt_manager: JWTAuthInterface) -> str:
    return jwt_manager.create_access_token(data={"user_id": user_id})


@pytest.fixture
def token():
    return "test.token.value"


@pytest.fixture
def client_authorized_by_user(
    client: TestClient, jwt_manager: JWTAuthInterface, db_session
) -> Tuple[TestClient, UserModel]:
    from src.tests.utils.factories import create_user

    user = create_user(db_session, jwt_manager)
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, user


@pytest.fixture
def client_authorized_by_admin(
    client: TestClient, jwt_manager: JWTAuthInterface, db_session
) -> Tuple[TestClient, UserModel]:
    from src.tests.utils.factories import create_admin

    user = create_admin(db_session, jwt_manager)
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, user


@pytest.fixture
def client_authorized_by_moderator(
    client: TestClient, jwt_manager: JWTAuthInterface, db_session
) -> Tuple[TestClient, UserModel]:
    from src.tests.utils.factories import create_moderator

    user = create_moderator(db_session, jwt_manager)
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, user


@pytest.fixture
def registered_user(client: TestClient, db_session: Session) -> Tuple[dict, UserModel]:
    payload = make_user_payload()
    client.post("accounts/register", json=payload)
    user = db_session.query(UserModel).filter_by(email=payload["email"]).first()
    return payload, user


@pytest.fixture
def registered_and_activated_user(
    client: TestClient, db_session: Session
) -> Tuple[dict, UserModel]:
    payload = make_user_payload()
    client.post("accounts/register", json=payload)
    user = db_session.query(UserModel).filter_by(email=payload["email"]).first()
    user.is_active = True
    db_session.commit()
    return payload, user


@pytest.fixture
def regular_user(db_session: Session) -> UserModel:
    user = UserModel.create(
        group_id=2, email="test1@test.com", new_password="Test1234!"
    )
    user.is_active = True
    db_session.add(user)
    db_session.commit()
    db_session.add(
        UserProfileModel(
            user_id=user.id,
            first_name="Original",
            last_name="User",
            info="Regular user profile",
        )
    )
    db_session.commit()
    return user


@pytest.fixture
def director_fixture(db_session: Session) -> DirectorModel:
    director = DirectorModel(name="director")
    db_session.add(director)
    db_session.commit()
    db_session.refresh(director)
    return director


@pytest.fixture
def certification_fixture(db_session: Session) -> CertificationModel:
    certification = CertificationModel(name="pg-13")
    db_session.add(certification)
    db_session.commit()
    db_session.refresh(certification)
    return certification


@pytest.fixture
def genre_fixture(db_session: Session) -> StarModel:
    genre = GenreModel(name="horror")
    db_session.add(genre)
    db_session.commit()
    db_session.refresh(genre)
    return genre


@pytest.fixture
def star_fixture(db_session: Session) -> StarModel:
    star = StarModel(name="Leonardo DiCaprio")
    db_session.add(star)
    db_session.commit()
    db_session.refresh(star)
    return star


@pytest.fixture
def movie_fixture(
    db_session, star_fixture, certification_fixture, director_fixture, genre_fixture
) -> MovieModel:
    movie = MovieModel(
        name="test movie",
        year=2000,
        time=100,
        imdb=8.8,
        votes=1_000_000,
        description="Test description",
        price=9.99,
        certification=certification_fixture,
        directors=[director_fixture],
        stars=[star_fixture],
        genres=[genre_fixture],
    )
    db_session.add(movie)
    db_session.commit()
    db_session.refresh(movie)
    return movie


@pytest.fixture
def cart_fixture(regular_user, db_session) -> CartModel:
    cart = CartModel(user=regular_user)
    db_session.add(cart)
    db_session.commit()
    return cart


@pytest.fixture
def cart_item_fixture(
    regular_user, movie_fixture, db_session, cart_fixture
) -> CartItemModel:
    cart_item = CartItemModel(cart_id=cart_fixture.id, movie_id=movie_fixture.id)
    db_session.add(cart_item)
    db_session.commit()
    return cart_item


@pytest.fixture
def purchased_movie_fixture(regular_user, movie_fixture, db_session) -> PurchaseModel:
    purchased_movie = PurchaseModel(
        user_id=regular_user.id,
        movie_id=movie_fixture.id,
    )
    db_session.add(purchased_movie)
    db_session.commit()
    return purchased_movie
