"""
Test fixtures: FastAPI app against an in-memory SQLite database
"""

import os

# Must be set before app modules are imported (settings + engine are created at import time).
# Environment variables take precedence over backend/.env.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-only-for-pytest-000000"
os.environ["DEBUG"] = "false"
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app import models  # noqa: F401  (registers all tables on Base.metadata)
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


TEST_USER = {
    "username": "smoketest",
    "email": "smoketest@example.com",
    "password": "smoke-test-pw-123",
}


@pytest.fixture()
def registered_user(client):
    response = client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def tokens(client, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_USER["username"], "password": TEST_USER["password"]},
    )
    assert response.status_code == 200, response.text
    return response.json()
