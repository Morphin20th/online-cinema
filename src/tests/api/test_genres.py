import math
from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError

from src.database import GenreModel, MovieModel
from src.tests.utils.fixtures.movies import create_genre

URL_PREFIX = "movies/genres/"


def test_create_genre_success(db_session, client_moderator):
    client, _ = client_moderator

    genre_name = "genre"
    response = client.post(f"{URL_PREFIX}create/", json={"name": genre_name})
    assert response.status_code == 201, "Expected status code 200 OK."
    data = response.json()
    assert "id" in data and "name" in data

    genre = db_session.query(GenreModel).filter_by(name=genre_name).first()

    assert genre, "Genre was not created."
    assert genre.name == genre_name, "Expected same name as in test."


def test_create_genre_conflict(db_session, genre_fixture, client_moderator):
    client, _ = client_moderator

    response = client.post(f"{URL_PREFIX}create/", json={"name": genre_fixture.name})
    assert response.status_code == 409, "Expected status code 409 Conflict."
    assert (
        response.json()["detail"]
        == f"A genre with name '{genre_fixture.name}' already exists."
    )


def test_create_genre_internal_server_error(db_session, client_moderator):
    client, _ = client_moderator

    genre_name = "genre"
    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError):
        response = client.post(f"{URL_PREFIX}create/", json={"name": genre_name})

    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred while trying to create genre."


def test_update_genre_success(db_session, genre_fixture, client_moderator):
    client, _ = client_moderator

    genre_name = "genre"
    response = client.patch(
        f"{URL_PREFIX}{genre_fixture.id}/", json={"name": genre_name}
    )
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["name"] == genre_name, "Expected same name as in test."

    genre_record = db_session.get(GenreModel, genre_fixture.id)
    db_session.refresh(genre_record)
    assert genre_record.name == genre_name, "Expected same name as in test."


def test_update_genre_not_found(db_session, genre_fixture, client_moderator):
    client, _ = client_moderator

    db_session.delete(genre_fixture)
    db_session.commit()

    response = client.patch(
        f"{URL_PREFIX}{genre_fixture.id}/", json={"name": genre_fixture.name}
    )
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Genre with the given ID was not found."


def test_update_genre_internal_server_error(
    db_session, genre_fixture, client_moderator
):
    client, _ = client_moderator

    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError):
        response = client.patch(
            f"{URL_PREFIX}{genre_fixture.id}/", json={"name": genre_fixture.name}
        )

    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred while trying to update genre."


def test_get_genres_success(db_session, client, genres_fixture):
    genres_fixture(10)
    response = client.get(f"{URL_PREFIX}")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert len(response.json()["genres"]) == 10, "Expected 10 genres."
    genres = db_session.query(GenreModel).all()
    assert len(genres) == 10, "Expected 10 genres."


def test_get_genres_with_params(db_session, client, genres_fixture):
    amount = 10
    genres_fixture(amount)

    response = client.get(f"{URL_PREFIX}?page=2&per_page=3")
    response_data = response.json()

    assert response.status_code == 200, "Expected status code 200 OK."
    assert len(response_data["genres"]) == 3, "Expected 3 genres."
    assert response_data["total_pages"] == math.ceil(10 / 3)
    assert response_data["total_items"] == amount, f"Expected {amount} items."

    genres = db_session.query(GenreModel).all()
    assert len(genres) == amount, f"Expected {amount} genres."


def test_delete_genre_success(db_session, client_moderator, genre_fixture):
    client, _ = client_moderator

    response = client.delete(f"{URL_PREFIX}{genre_fixture.id}/")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "Genre deleted successfully"

    genre_record = db_session.query(GenreModel).filter_by(id=genre_fixture.id).first()
    assert genre_record is None, "Genre was not deleted."


def test_delete_genre_internal_server_error(
    client_moderator, genre_fixture, db_session
):
    client, _ = client_moderator

    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError):
        response = client.delete(f"{URL_PREFIX}{genre_fixture.id}/")

    assert response.status_code == 500
    assert response.json()["detail"] == "Error occurred while trying to delete genre."

    db_session.rollback()  # do not remove

    genre_record = db_session.query(GenreModel).filter_by(id=genre_fixture.id).first()
    assert genre_record, "Genre was deleted."


def test_delete_genre_not_found(client_moderator, genre_fixture, db_session):
    client, _ = client_moderator

    db_session.delete(genre_fixture)
    db_session.commit()

    response = client.delete(f"{URL_PREFIX}{genre_fixture.id}/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Genre with the given ID was not found."


def test_get_movies_by_genre_success(
    client_user,
    genre_fixture,
    genres_fixture,
    db_session,
    star_fixture,
    certification_fixture,
    director_fixture,
    movies_fixture,
):
    movies_fixture(5)
    client, _ = client_user

    another_genre = create_genre(db_session, name="comedy")
    db_session.commit()
    db_session.refresh(another_genre)

    other_movie = MovieModel(
        name="other movie",
        year=2023,
        time=120,
        imdb=8.0,
        votes=2000,
        description="Should not appear in horror genre response",
        price=12.99,
        certification=certification_fixture,
        directors=[director_fixture],
        stars=[star_fixture],
        genres=[another_genre],
    )
    db_session.add(other_movie)
    db_session.commit()
    db_session.refresh(other_movie)

    response = client.get(f"{URL_PREFIX}{another_genre.id}/")
    assert response.status_code == 200, "Expected status code 200 OK."
    response_data = response.json()
    assert "movies" in response_data
    assert len(response_data["movies"]) == 1, "Expected 1 movie."

    movies_count = db_session.query(MovieModel).count()
    assert movies_count > 1, "Expected more than 1 movie."


# user cannot access tests


def test_user_create_genre_forbidden(client_user, db_session):
    client, _ = client_user

    response = client.post(f"{URL_PREFIX}create/", json={"name": "genre"})
    assert response.status_code == 403, "Expected status code  403 Forbidden."
    assert response.json()["detail"] == "Access denied. Moderator or admin required."
    genre = db_session.query(GenreModel).filter_by(name="genre").first()

    assert genre is None, "Genre was created."


def test_user_update_genre_forbidden(client_user, genre_fixture, db_session):
    client, _ = client_user

    response = client.patch(f"{URL_PREFIX}{genre_fixture.id}/", json={"name": "genre"})
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Moderator or admin required."

    db_session.refresh(genre_fixture)
    assert genre_fixture.name != "genre", "Genre was updated."


def test_user_delete_genre_forbidden(client_user, genre_fixture, db_session):
    client, _ = client_user
    response = client.delete(f"{URL_PREFIX}{genre_fixture.id}/")
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Moderator or admin required."

    genre = db_session.query(GenreModel).filter_by(name=genre_fixture.name).first()
    assert genre, "Genre was deleted."


def test_anon_get_movies_by_genre_unauthorized(client, genre_fixture):
    response = client.get(f"{URL_PREFIX}{genre_fixture.id}/")
    assert response.status_code == 401, "Expected status code 401 Unauthorized."
    assert response.json()["detail"] == "Authorization header is missing"
