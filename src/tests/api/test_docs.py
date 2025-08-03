def test_admin_get_swagger_ui_success(client_admin, settings):
    response = client_admin.get(settings.DOCS_URL)
    assert response.status_code == 200, "Expected status code 200 OK."


def test_admin_get_redoc_ui_success(client_admin, settings):
    response = client_admin.get(settings.REDOC_URL)
    assert response.status_code == 200, "Expected status code 200 OK."


def test_admin_get_openapi_json(client_admin, settings):
    response = client_admin.get(settings.OPENAPI_URL)
    assert response.status_code == 200, "Expected status code 200 OK."


def test_user_get_swagger_ui_forbidden(client_user, settings):
    response = client_user.get(settings.DOCS_URL)
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Admin privileges required."


def test_user_get_redoc_ui_forbidden(client_user, settings):
    response = client_user.get(settings.REDOC_URL)
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Admin privileges required."


def test_user_get_openapi_json_forbidden(client_user, settings):
    response = client_user.get(settings.OPENAPI_URL)
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Admin privileges required."
