import os

os.environ["DATABASE_URL"] = "sqlite:///./data/test_support_assistant.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./data/test_support_assistant.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_customer(client):
    payload = {
        "email": "customer@example.com",
        "full_name": "Test Customer",
        "password": "SecurePass123!",
        "is_agent": False,
    }
    client.post("/api/v1/auth/register", json=payload)
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    token = login_resp.json()["access_token"]
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}, "email": payload["email"]}


@pytest.fixture
def registered_agent(client):
    payload = {
        "email": "agent@example.com",
        "full_name": "Test Agent",
        "password": "SecurePass123!",
        "is_agent": True,
    }
    client.post("/api/v1/auth/register", json=payload)
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    token = login_resp.json()["access_token"]
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}, "email": payload["email"]}
