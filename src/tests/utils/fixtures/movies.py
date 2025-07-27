import pytest
from sqlalchemy.orm import Session

from src.database import (
    MovieModel,
    CartModel,
    CartItemModel,
    PurchaseModel,
    StarModel,
    GenreModel,
    CertificationModel,
    DirectorModel,
)


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


def create_movie(
    db_session,
    star_fixture,
    certification_fixture,
    director_fixture,
    genre_fixture,
    index: int = 0,
) -> MovieModel:
    movie = MovieModel(
        name=f"Test Movie {index}",
        year=2000 + index,
        time=100 + index,
        imdb=7.0,
        votes=1000 + index,
        description=f"Description {index}",
        price=9.99 + index,
        certification=certification_fixture,
        directors=[director_fixture],
        stars=[star_fixture],
        genres=[genre_fixture],
    )
    db_session.add(movie)
    return movie


@pytest.fixture
def movie_fixture(
    db_session, star_fixture, certification_fixture, director_fixture, genre_fixture
) -> MovieModel:

    movie = create_movie(
        db_session,
        star_fixture,
        certification_fixture,
        director_fixture,
        genre_fixture,
    )
    db_session.commit()
    db_session.refresh(movie)
    return movie


@pytest.fixture
def movies_fixture(
    db_session, star_fixture, certification_fixture, director_fixture, genre_fixture
):
    def _create_movies(amount: int):
        movies = [
            create_movie(
                db_session,
                star_fixture,
                certification_fixture,
                director_fixture,
                genre_fixture,
                index=i,
            )
            for i in range(amount)
        ]
        db_session.commit()
        for movie in movies:
            print(movie.genres)
            print(movie.certification)
            db_session.refresh(movie)
        return movies

    return _create_movies


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
