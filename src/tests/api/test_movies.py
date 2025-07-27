from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import src.tests.examples.movie_examples as examples
from schemas import MovieDetailSchema
from src.database import (
    MovieModel,
    CertificationModel,
    GenreModel,
    DirectorModel,
    StarModel,
)

URL_PREFIX = "movies/"


def assert_movie_response_matches_input(expected: dict, actual: dict):
    assert "uuid" in actual, "Missing 'uuid' in response"
    assert expected["name"] == actual["name"]
    assert expected["year"] == actual["year"]
    assert expected["time"] == actual["time"]
    assert expected["imdb"] == actual["imdb"]
    assert expected.get("votes", 0) == actual["votes"]

    assert str(expected["price"]) == actual["price"], "Price mismatch"
    assert expected["certification"] == actual["certification"]["name"]

    for i, genre in enumerate(expected["genres"]):
        assert genre in actual["genres"][i]["name"]

    for i, director in enumerate(expected["directors"]):
        assert director in actual["directors"][i]["name"]

    for i, star in enumerate(expected["stars"]):
        assert star in actual["stars"][i]["name"]


def assert_movie_entities_created(movie_data: dict, db_session: Session):
    movie_record = (
        db_session.query(MovieModel).filter_by(name=movie_data["name"]).first()
    )
    assert movie_record, "Movie was not created."

    certification_record = (
        db_session.query(CertificationModel)
        .filter_by(name=movie_data["certification"])
        .first()
    )
    assert certification_record, "Certification was not created."

    for genre_name in movie_data.get("genres", []):
        genre_record = db_session.query(GenreModel).filter_by(name=genre_name).first()
        assert genre_record, f"Genre '{genre_name}' was not created."

    for director_name in movie_data.get("directors", []):
        director_record = (
            db_session.query(DirectorModel).filter_by(name=director_name).first()
        )
        assert director_record, f"Director '{director_name}' was not created."

    for star_name in movie_data.get("stars", []):
        star_record = db_session.query(StarModel).filter_by(name=star_name).first()
        assert star_record, f"Star '{star_name}' was not created."


def test_create_movie_success_minimal_data(client_authorized_by_moderator, db_session):
    client, _ = client_authorized_by_moderator

    movie = examples.minimal_movie_example

    response = client.post(f"{URL_PREFIX}create/", json=movie)
    response_data = response.json()
    assert response.status_code == 201, "Expected status code 201 Created."

    assert_movie_entities_created(movie, db_session)
    assert_movie_response_matches_input(movie, response_data)


def test_create_movie_success_full_data(client_authorized_by_moderator, db_session):
    client, _ = client_authorized_by_moderator

    movie = examples.full_movie_example

    response = client.post(f"{URL_PREFIX}create/", json=movie)
    response_data = response.json()
    assert response.status_code == 201, "Expected status code 201 Created."

    assert_movie_entities_created(movie, db_session)
    assert_movie_response_matches_input(movie, response_data)

    assert movie["meta_score"] == response_data["meta_score"]
    assert movie["gross"] == response_data["gross"]


def test_create_movie_conflict(client_authorized_by_moderator, db_session):
    client, _ = client_authorized_by_moderator

    movie = examples.minimal_movie_example

    first_response = client.post(f"{URL_PREFIX}create/", json=movie)
    assert first_response.status_code == 201, "Expected status code 201 Created."

    movie_record = db_session.query(MovieModel).filter_by(name=movie["name"]).first()
    assert movie_record, "Movie was not created."

    second_response = client.post(f"{URL_PREFIX}create/", json=movie)
    assert second_response.status_code == 409, "Expected status code 409 Conflict."
    assert second_response.json()["detail"] == (
        f"A movie with name '{movie_record.name}' and release year '{movie_record.year}' "
        f"and duration '{movie_record.time}' already exists."
    )


def test_create_movie_by_user(client_authorized_by_user, db_session):
    client, _ = client_authorized_by_user

    movie = examples.minimal_movie_example

    response = client.post(f"{URL_PREFIX}create/", json=movie)
    assert response.status_code == 403, "Expected status code 403 Forbidden."


def test_create_movie_invalid_data(client_authorized_by_moderator, db_session):
    client, _ = client_authorized_by_moderator

    movie = examples.invalid_movie_example

    response = client.post(f"{URL_PREFIX}create/", json=movie)
    assert response.status_code == 422, "Expected status code 422 Unprocessable Entity."

    movie_record = db_session.query(MovieModel).filter_by(name=movie["name"]).first()
    assert movie_record is None, "Movie was created."


def test_create_movie_internal_server_error(client_authorized_by_moderator):
    client, _ = client_authorized_by_moderator

    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError):
        response = client.post(
            f"{URL_PREFIX}create/", json=examples.minimal_movie_example
        )
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred during movie creation."


def test_update_movie_success(
    client_authorized_by_moderator, movie_fixture, db_session
):
    client, _ = client_authorized_by_moderator

    update_data = examples.minimal_movie_example
    response = client.patch(f"{URL_PREFIX}{movie_fixture.uuid}", json=update_data)
    assert response.status_code == 200, "Expected status code 200 OK."

    response_data = response.json()
    assert_movie_entities_created(update_data, db_session)
    assert_movie_response_matches_input(update_data, response_data)


def test_update_movie_by_user(client_authorized_by_user, movie_fixture):
    client, _ = client_authorized_by_user

    update_data = examples.minimal_movie_example
    response = client.patch(f"{URL_PREFIX}{movie_fixture.uuid}", json=update_data)
    assert response.status_code == 403, "Expected status code 200 Forbidden."
    response_data = response.json()
    assert response_data["detail"] == "Access denied. Moderator or admin required."


def test_update_movie_not_found(
    client_authorized_by_moderator, movie_fixture, db_session
):
    client, _ = client_authorized_by_moderator

    movie_uuid = movie_fixture.uuid

    db_session.delete(movie_fixture)
    db_session.commit()

    response = client.patch(
        f"{URL_PREFIX}{movie_uuid}", json=examples.minimal_movie_example
    )
    assert response.status_code == 404, "Expected status code 404 Forbidden."
    assert response.json()["detail"] == "Movie with the given ID was not found."


def test_update_movie_internal_server_error(
    client_authorized_by_moderator, movie_fixture
):
    client, _ = client_authorized_by_moderator

    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError):
        response = client.patch(
            f"{URL_PREFIX}{movie_fixture.uuid}/", json=examples.minimal_movie_example
        )
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred while trying to update movie."


def test_get_movie_success(client_authorized_by_user, movie_fixture, db_session):
    client, _ = client_authorized_by_user

    response = client.get(f"{URL_PREFIX}{movie_fixture.uuid}/")
    assert response.status_code == 200, "Expected status code 200 OK."

    validated_response = MovieDetailSchema.model_validate(response.json())

    assert validated_response.uuid == movie_fixture.uuid
    assert validated_response.name == movie_fixture.name
    assert validated_response.year == movie_fixture.year


def test_delete_movie_success(
    client_authorized_by_moderator, movie_fixture, db_session
):
    client, _ = client_authorized_by_moderator

    response = client.delete(f"{URL_PREFIX}{movie_fixture.uuid}/")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "Movie deleted successfully"

    movie = db_session.query(MovieModel).filter_by(uuid=movie_fixture.uuid).first()
    assert movie is None, "Movie was not deleted."


def test_delete_movie_not_found(
    client_authorized_by_moderator, movie_fixture, db_session
):
    client, _ = client_authorized_by_moderator

    db_session.delete(movie_fixture)
    db_session.commit()

    response = client.delete(f"{URL_PREFIX}{movie_fixture.uuid}/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Movie with the given ID was not found."


def test_delete_movie_internal_server_error(
    client_authorized_by_moderator, movie_fixture
):
    client, _ = client_authorized_by_moderator

    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError):
        response = client.delete(f"{URL_PREFIX}{movie_fixture.uuid}/")

    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred while trying to remove movie."


def test_delete_movie_bad_request_carts(
    client_authorized_by_moderator, db_session, movie_fixture, cart_item_fixture
):
    client, _ = client_authorized_by_moderator

    response = client.delete(f"{URL_PREFIX}{movie_fixture.uuid}/")
    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert (
        response.json()["detail"] == "Movie is in users' carts and cannot be deleted."
    )


def test_delete_movie_bad_request_purchased(
    client_authorized_by_moderator, db_session, movie_fixture, purchased_movie_fixture
):
    client, _ = client_authorized_by_moderator

    response = client.delete(f"{URL_PREFIX}{movie_fixture.uuid}/")
    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert (
        response.json()["detail"]
        == "Movie purchased by some user and cannot be deleted."
    )


@pytest.mark.parametrize(
    "filter_key, filter_value, expected_count",
    [
        ("year", 2001, 1),
        ("imdb", 7.0, 3),
        ("genre", "horror", 3),
        ("certification", "pg-13", 3),
    ],
)
def test_get_movies_with_filters(
    filter_key,
    filter_value,
    expected_count,
    db_session,
    movies_fixture,
    client,
):
    movies_fixture(3)
    response = client.get(f"{URL_PREFIX}?{filter_key}={filter_value}")
    assert response.status_code == 200, "Expected status code 200 OK."
    data = response.json()
    print(data["movies"])
    assert "movies" in data
    assert len(data["movies"]) == expected_count


def test_get_movies_with_multiple_filters(db_session, movies_fixture, client):
    movies_fixture(3)
    response = client.get(
        f"{URL_PREFIX}?year=2002&imdb=7&genre=horror&certification=pg-13"
    )
    assert response.status_code == 200, "Expected status code 200 OK."
    data = response.json()
    print(data["movies"])
    assert "movies" in data
    assert len(data["movies"]) == 1


def test_get_movies_with_sorting(db_session, movies_fixture, client):
    movies_fixture(3)
    response = client.get(f"{URL_PREFIX}?sort=-year")
    assert response.status_code == 200, "Expected status code 200 OK."
    data = response.json()
    years = [movie["year"] for movie in data["movies"]]
    assert years == sorted(years, reverse=True)


def test_get_movies_with_invalid_filter_does_not_crash(
    db_session, movies_fixture, client
):
    movies_fixture(3)
    response = client.get(f"{URL_PREFIX}?genre=nogenre")
    assert response.status_code == 200, "Expected status code 200 OK."
    data = response.json()
    assert "movies" in data
    assert len(data["movies"]) == 0
