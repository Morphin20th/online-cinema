from sqlalchemy.exc import SQLAlchemyError

from src.database import StarModel

URL_PREFIX = "movies/stars/"


def test_create_star_success(db_session, client_moderator):
    star_name = "star"
    response = client_moderator.post(f"{URL_PREFIX}create/", json={"name": star_name})
    assert response.status_code == 201, "Expected status code 200 OK."
    data = response.json()
    assert "id" in data and "name" in data
    assert data["name"] == star_name

    star = db_session.query(StarModel).filter_by(name=star_name).first()

    assert star, "Star was not created."
    assert star.name == star_name, "Expected same name as in test."


def test_create_star_conflict(db_session, star_fixture, client_moderator):
    response = client_moderator.post(
        f"{URL_PREFIX}create/", json={"name": star_fixture.name}
    )
    assert response.status_code == 409, "Expected status code 409 Conflict."
    assert (
        response.json()["detail"]
        == f"A star with name '{star_fixture.name}' already exists."
    )


def test_create_star_internal_server_error(db_session, client_moderator, mocker):
    star_name = "star"
    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client_moderator.post(f"{URL_PREFIX}create/", json={"name": star_name})

    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred while trying to create star."


def test_update_star_success(db_session, star_fixture, client_moderator):
    star_name = "star"
    response = client_moderator.patch(
        f"{URL_PREFIX}{star_fixture.id}/", json={"name": star_name}
    )
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["name"] == star_name, "Expected same name as in test."

    star_record = db_session.get(StarModel, star_fixture.id)
    db_session.refresh(star_record)
    assert star_record.name == star_name, "Expected same name as in test."


def test_update_star_not_found(db_session, star_fixture, client_moderator):
    db_session.delete(star_fixture)
    db_session.commit()

    response = client_moderator.patch(
        f"{URL_PREFIX}{star_fixture.id}/", json={"name": star_fixture.name}
    )
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Star with the given ID was not found."


def test_update_star_internal_server_error(
    db_session, star_fixture, client_moderator, mocker
):
    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client_moderator.patch(
        f"{URL_PREFIX}{star_fixture.id}/", json={"name": star_fixture.name}
    )

    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred while trying to update star."


def test_get_stars_success(db_session, client, stars_fixture):
    stars_fixture(10)
    response = client.get(f"{URL_PREFIX}")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert len(response.json()["stars"]) == 10, "Expected 10 stars."
    stars = db_session.query(StarModel).all()
    assert len(stars) == 10, "Expected 10 stars."


def test_get_stars_with_params(db_session, client, stars_fixture):
    amount = 10
    stars_fixture(amount)

    response = client.get(f"{URL_PREFIX}?page=2&per_page=3")
    response_data = response.json()

    assert response.status_code == 200, "Expected status code 200 OK."
    assert len(response_data["stars"]) == 3, "Expected 3 stars."
    assert response_data["total_pages"] == 4
    assert response_data["total_items"] == amount, f"Expected {amount} items."

    stars = db_session.query(StarModel).all()
    assert len(stars) == amount, f"Expected {amount} stars."


def test_delete_star_success(db_session, client_moderator, star_fixture):
    response = client_moderator.delete(f"{URL_PREFIX}{star_fixture.id}/")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "Star has been deleted successfully."

    star_record = db_session.query(StarModel).filter_by(id=star_fixture.id).first()
    assert star_record is None, "Star was not deleted."


def test_delete_star_internal_server_error(
    client_moderator, star_fixture, db_session, mocker
):
    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client_moderator.delete(f"{URL_PREFIX}{star_fixture.id}/")

    assert response.status_code == 500
    assert response.json()["detail"] == "Error occurred while trying to delete star."


def test_delete_star_not_found(client_moderator, star_fixture, db_session):
    db_session.delete(star_fixture)
    db_session.commit()

    response = client_moderator.delete(f"{URL_PREFIX}{star_fixture.id}/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Star with the given ID was not found."


def test_get_star_detail_success(client_user, star_fixture):
    response = client_user.get(f"{URL_PREFIX}{star_fixture.id}/")
    assert response.status_code == 200, "Expected status code 200 OK."

    data = response.json()
    assert "id" in data and "name" in data
    assert data["id"] == star_fixture.id
    assert data["name"] == star_fixture.name


def test_get_star_detail_not_found(client_user, star_fixture, db_session):
    db_session.delete(star_fixture)
    db_session.commit()

    response = client_user.get(f"{URL_PREFIX}{star_fixture.id}/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Star with the given ID was not found."


# user cannot access tests


def test_user_create_star_forbidden(client_user, db_session):
    response = client_user.post(f"{URL_PREFIX}create/", json={"name": "star"})
    assert response.status_code == 403, "Expected status code  403 Forbidden."
    assert response.json()["detail"] == "Access denied. Moderator or admin required."
    star = db_session.query(StarModel).filter_by(name="star").first()

    assert star is None, "Star was created."


def test_user_update_star_forbidden(client_user, star_fixture, db_session):
    response = client_user.patch(
        f"{URL_PREFIX}{star_fixture.id}/", json={"name": "star"}
    )
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Moderator or admin required."

    db_session.refresh(star_fixture)
    assert star_fixture.name != "star", "Star was updated."


def test_user_delete_star_forbidden(client_user, star_fixture, db_session):
    response = client_user.delete(f"{URL_PREFIX}{star_fixture.id}/")
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Moderator or admin required."

    star = db_session.query(StarModel).filter_by(name=star_fixture.name).first()
    assert star, "Star was deleted."


def test_anon_get_star_detail_unauthorized(client, star_fixture):
    response = client.get(f"{URL_PREFIX}{star_fixture.id}/")
    assert response.status_code == 401, "Expected status code 401 Unauthorized."
    assert response.json()["detail"] == "Authorization header is missing"
