from io import BytesIO

import pytest
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

import src.tests.examples.profile_examples as examples
from src.database import UserProfileModel, GenderEnum
from src.tests.examples.profile_examples import invalid_name_example

URL_PREFIX = "profiles/users/"


def test_profile_create_success_with_no_data(client_user, db_session):
    client, user = client_user

    assert user.profile is None, "Profile already exists."

    response = client.post(f"{URL_PREFIX}{user.id}/", json={})
    assert response.status_code == 201, "Expected status code 201 Created."

    profile = db_session.query(UserProfileModel).filter_by(user_id=user.id).first()
    assert profile, "Profile was not created."


def test_profile_create_success_with_data(client_user, db_session):
    client, user = client_user

    assert user.profile is None, "Profile already exists."

    response = client.post(f"{URL_PREFIX}{user.id}/", data=examples.profile_example)
    assert response.status_code == 201, "Expected status code 201 Created."

    profile = db_session.query(UserProfileModel).filter_by(user_id=user.id).first()
    assert profile, "Profile was not created."

    assert profile.first_name == examples.profile_example["first_name"]
    assert profile.last_name == examples.profile_example["last_name"]
    assert profile.gender.value == examples.profile_example["gender"]
    assert str(profile.date_of_birth) == examples.profile_example["date_of_birth"]
    assert profile.info == examples.profile_example["info"]


def test_create_profile_with_avatar(client_user, db_session, mocker):
    client, user = client_user

    mocker.patch("src.routes.profiles.save_avatar", return_value="/uploads/avatar.jpg")
    img = Image.new("RGB", (100, 100), color="blue")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    response = client.post(
        f"{URL_PREFIX}{user.id}/",
        data={},
        files={"avatar": ("avatar.jpg", img_byte_arr.getvalue(), "image/jpeg")},
    )

    assert response.status_code == 201, "Expected status code 201 Created."
    result = response.json()

    assert result["avatar"] == "/uploads/avatar.jpg"


def test_profile_create_conflict(client_user, db_session):
    client, user = client_user

    assert user.profile is None, "Profile already exists."

    client.post(f"{URL_PREFIX}{user.id}/", data=examples.profile_example)

    profile = db_session.query(UserProfileModel).filter_by(user_id=user.id).first()
    assert profile, "Profile was not created."

    response = client.post(f"{URL_PREFIX}{user.id}/", data=examples.profile_example)
    assert response.status_code == 409, "Expected status code 409 Conflict."
    assert response.json()["detail"] == "Profile already exists."


@pytest.mark.parametrize(
    "request_data, error_message",
    [
        (
            examples.invalid_name_example,
            f"{invalid_name_example['first_name']} contains non-english letters",
        ),
        (examples.invalid_gender_example, "Gender must be one of: man, woman"),
        (
            examples.future_birth_date_example,
            "You must be at least 18 years old to register.",
        ),
        (
            examples.past_birth_date_example,
            "Invalid birth date - year must be greater than 1900.",
        ),
    ],
)
def test_profile_create_invalid_data(request_data, error_message, client_user):
    client, user = client_user

    response = client.post(f"{URL_PREFIX}{user.id}/", data=request_data)
    assert response.status_code == 422, "Expected status code 422 Unprocessable Entity."
    assert response.json()["detail"] == error_message


@pytest.mark.parametrize(
    "request_data, error_message",
    [
        (examples.invalid_large_image, "Image size exceeds 1 MB"),
        (examples.invalid_file_format, "Unsupported image format: BMP"),
        (examples.invalid_byte, "Invalid image format"),
    ],
)
def test_profile_create_invalid_images(request_data, error_message, client_user):
    client, user = client_user

    response = client.post(
        f"{URL_PREFIX}{user.id}/", data={}, files={"avatar": request_data["avatar"]}
    )

    assert response.status_code == 422
    assert error_message in response.json()["detail"]


def test_update_profile_success_partial(client_user, db_session):
    client, user = client_user

    db_session.add(
        UserProfileModel(
            user_id=user.id,
            first_name="Old",
            last_name="Name",
            gender=GenderEnum.MAN,
        )
    )
    db_session.commit()

    update_data = {"first_name": "new"}
    response = client.patch(f"{URL_PREFIX}{user.id}/", data=update_data)

    assert response.status_code == 200, "Expected status code 200 OK."

    profile = response.json()
    assert profile["first_name"] == "new", "'first_name' is expected to be updated."
    assert (
        profile["last_name"] == "Name",
    ), "'last_name' is not expected to be updated."
    assert (
        profile["gender"] == GenderEnum.MAN.value
    ), "'gender' is not expected to be updated."


def test_profile_update_success_full(client_user, db_session):
    client, user = client_user

    db_session.add(UserProfileModel(user_id=user.id))
    db_session.commit()

    update_data = examples.profile_example
    response = client.patch(f"{URL_PREFIX}{user.id}/", data=update_data)

    assert response.status_code == 200, "Expected status code 200 OK."
    profile = response.json()
    assert (
        profile["first_name"] == update_data["first_name"]
    ), "'first_name' is expected to be updated."
    assert (
        profile["last_name"] == update_data["last_name"]
    ), "'last_name' is expected to be updated."


def test_profile_update_avatar(client_user, db_session, mocker):
    client, user = client_user

    db_session.add(
        UserProfileModel(
            user_id=user.id, first_name="Old", last_name="Name", avatar="/old/path.jpg"
        )
    )
    db_session.commit()

    mocker.patch("src.routes.profiles.save_avatar", return_value="/new/path.jpg")
    img = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    response = client.patch(
        f"{URL_PREFIX}{user.id}/",
        data={"first_name": "Old"},
        files={"avatar": ("new.jpg", img_byte_arr.getvalue(), "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["avatar"] == "/new/path.jpg"


def test_profile_update_forbidden_for_other_users(
    client_user, db_session, regular_user
):
    client, _ = client_user

    response = client.patch(
        f"{URL_PREFIX}{regular_user.id}/", data={"first_name": "Updated"}
    )

    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert (
        response.json()["detail"] == "Only admin or profile owner can update profile."
    )

    profile = (
        db_session.query(UserProfileModel).filter_by(user_id=regular_user.id).first()
    )
    assert profile.first_name == "Original"


def test_profile_update_db_error(client_user, db_session, mocker):
    client, user = client_user

    db_session.add(UserProfileModel(user_id=user.id))
    db_session.commit()

    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client.patch(f"{URL_PREFIX}{user.id}/", data={"first_name": "New"})

    assert response.status_code == 500
    assert "Error occurred during profile update" in response.json()["detail"]


def test_admin_can_update_other_user_profile(client_admin, db_session, regular_user):
    client, _ = client_admin

    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "gender": "man",
        "info": "Updated by admin",
    }

    response = client.patch(f"{URL_PREFIX}{regular_user.id}/", data=update_data)

    assert response.status_code == 200

    updated_profile = response.json()
    assert updated_profile["first_name"] == "updated"
    assert updated_profile["last_name"] == "name"
    assert updated_profile["gender"] == "man"
    assert updated_profile["info"] == "Updated by admin"


def test_admin_can_view_other_user_profile(client_admin, db_session, regular_user):
    client, _ = client_admin

    response = client.get(f"{URL_PREFIX}{regular_user.id}/")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert "first_name", "last_name" in response.json()


def test_user_cant_view_other_user_profile(client_user, db_session, regular_user):
    client, _ = client_user

    response = client.get(f"{URL_PREFIX}{regular_user.id}/")
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Only admin or profile owner can view profile."


def test_get_profile_not_found(client_admin, db_session):
    client, _ = client_admin

    response = client.get(f"{URL_PREFIX}999/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Profile with given user ID was not found."
