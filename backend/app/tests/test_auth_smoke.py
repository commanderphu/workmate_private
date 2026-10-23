"""
Smoke tests for the auth flow: register, login, /me, refresh, API key
"""

from app.models import User

from .conftest import TEST_USER


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestLogin:
    def test_login_returns_access_and_refresh_token(self, tokens):
        assert tokens["access_token"]
        assert tokens["refresh_token"]
        assert tokens["token_type"] == "bearer"

    def test_login_with_wrong_password_is_rejected(self, client, registered_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": TEST_USER["username"], "password": "falsch-falsch"},
        )
        assert response.status_code == 401

    def test_register_duplicate_username_is_rejected(self, client, registered_user):
        response = client.post("/api/v1/auth/register", json=TEST_USER)
        assert response.status_code == 400


class TestMe:
    def test_me_with_access_token(self, client, tokens):
        response = client.get("/api/v1/auth/me", headers=bearer(tokens["access_token"]))
        assert response.status_code == 200
        assert response.json()["username"] == TEST_USER["username"]

    def test_me_without_token_is_rejected(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_with_refresh_token_is_rejected(self, client, tokens):
        response = client.get("/api/v1/auth/me", headers=bearer(tokens["refresh_token"]))
        assert response.status_code == 401


class TestRefresh:
    def test_refresh_returns_working_access_token(self, client, tokens):
        response = client.post("/api/v1/auth/refresh", headers=bearer(tokens["refresh_token"]))
        assert response.status_code == 200, response.text
        new_tokens = response.json()
        assert new_tokens["refresh_token"]

        me = client.get("/api/v1/auth/me", headers=bearer(new_tokens["access_token"]))
        assert me.status_code == 200

    def test_refresh_with_access_token_is_rejected(self, client, tokens):
        response = client.post("/api/v1/auth/refresh", headers=bearer(tokens["access_token"]))
        assert response.status_code == 401

    def test_refresh_with_invalid_token_is_rejected(self, client):
        response = client.post("/api/v1/auth/refresh", headers=bearer("kein-jwt"))
        assert response.status_code == 401

    def test_refresh_without_header_is_rejected(self, client):
        assert client.post("/api/v1/auth/refresh").status_code == 401

    def test_refresh_for_inactive_user_is_rejected(self, client, db, tokens):
        user = db.query(User).filter(User.username == TEST_USER["username"]).one()
        user.is_active = False
        db.commit()

        response = client.post("/api/v1/auth/refresh", headers=bearer(tokens["refresh_token"]))
        assert response.status_code == 401


class TestApiKey:
    def test_me_with_valid_api_key(self, client, db, registered_user):
        user = db.query(User).filter(User.username == TEST_USER["username"]).one()
        user.api_key = "test-api-key"
        db.commit()

        response = client.get("/api/v1/auth/me", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        assert response.json()["username"] == TEST_USER["username"]

    def test_me_with_invalid_api_key_is_rejected(self, client, registered_user):
        response = client.get("/api/v1/auth/me", headers={"X-API-Key": "falsch"})
        assert response.status_code == 401
