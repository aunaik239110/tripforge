import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.destination import Destination


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://tripforge:tripforge_dev@localhost:5432/tripforge_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_destination():
    db = TestingSessionLocal()

    destination = Destination(
        name="Test Paris",
        country="France",
    )

    db.add(destination)
    db.commit()
    db.refresh(destination)

    yield destination

    db.delete(destination)
    db.commit()
    db.close()


def test_get_destination(test_destination):
    response = client.get(f"/api/destinations/{test_destination.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Test Paris"
    assert response.json()["country"] == "France"


def test_get_destination_not_found():
    response = client.get("/api/destinations/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Destination not found"


def test_create_destination():
    response = client.post(
        "/api/destinations",
        json={
            "name": "Test Tokyo",
            "country": "Japan",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Tokyo"
    assert response.json()["country"] == "Japan"

    db = TestingSessionLocal()
    destination = (
        db.query(Destination)
        .filter(Destination.id == response.json()["id"])
        .first()
    )

    assert destination is not None

    db.delete(destination)
    db.commit()
    db.close()


def test_create_duplicate_destination(test_destination):
    response = client.post(
        "/api/destinations",
        json={
            "name": "Test Paris",
            "country": "France",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Destination already exists"


def test_update_destination(test_destination):
    response = client.put(
        f"/api/destinations/{test_destination.id}",
        json={
            "name": "Updated Paris",
            "country": "France",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Paris"


def test_update_destination_not_found():
    response = client.put(
        "/api/destinations/999999",
        json={
            "name": "Unknown",
            "country": "Unknown",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Destination not found"


def test_delete_destination(test_destination):
    response = client.delete(
        f"/api/destinations/{test_destination.id}"
    )

    assert response.status_code == 204


def test_delete_destination_not_found():
    response = client.delete("/api/destinations/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Destination not found"