"""Integration tests for administrator authentication."""

from fastapi.testclient import TestClient

from app.core.config import get_settings


def login(client: TestClient) -> None:
    settings = get_settings()
    response = client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password,
        },
    )

    assert response.status_code == 200


def test_valid_login_returns_200(client: TestClient) -> None:
    settings = get_settings()

    response = client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"username": settings.admin_username}


def test_invalid_password_returns_401(client: TestClient) -> None:
    settings = get_settings()

    response = client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": "invalid-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password."}


def test_get_current_admin_without_login_returns_401(
    client: TestClient,
) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Admin authentication required."}


def test_get_current_admin_after_login_returns_200(
    client: TestClient,
) -> None:
    settings = get_settings()
    login(client)

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json() == {"username": settings.admin_username}


def test_admin_route_without_login_returns_401(client: TestClient) -> None:
    response = client.get("/api/admin/elections")

    assert response.status_code == 401
    assert response.json() == {"detail": "Admin authentication required."}


def test_logout_returns_204(client: TestClient) -> None:
    login(client)

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert response.content == b""


def test_get_current_admin_after_logout_returns_401(
    client: TestClient,
) -> None:
    login(client)
    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 204

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Admin authentication required."}
