from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.booking_routes import get_database_path
from app.database import initialize_database
from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    database_path = tmp_path / "roomtour.sqlite3"
    monkeypatch.setattr("app.main.initialize_database", lambda: initialize_database(database_path))
    app.dependency_overrides[get_database_path] = lambda: database_path
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_database_path, None)


def test_list_users(client: TestClient) -> None:
    response = client.get("/api/users")
    assert response.status_code == 200
    assert response.json() == [
        {"user_id": f"U{i:03}", "display_name": f"Demo Traveler {i}"} for i in range(1, 7)
    ]


def test_booking_crud_lifecycle(client: TestClient) -> None:
    assert client.get("/api/bookings", params={"user_id": "U006"}).json() == []
    response = client.post("/api/bookings", json={"user_id": "U006", "trip_id": "T001"})
    assert response.status_code == 201
    booking = response.json()
    assert booking["status"] == "confirmed"
    assert booking["user_id"] == "U006"
    assert booking["trip_id"] == "T001"
    assert booking["booking_id"].startswith("B-")
    history = client.get("/api/bookings", params={"user_id": "U006"})
    assert history.status_code == 200
    assert len(history.json()) == 1
    item = history.json()[0]
    assert item["booking_id"] == booking["booking_id"]
    assert item["hotel_name"] == "Harbor Lantern Hotel"
    assert item["trip_name"] == "Boston Harbor Weekend"
    assert item["nightly_rate_usd"] == 150.0
    url = f"/api/bookings/{booking['booking_id']}"
    for _ in range(2):
        cancelled = client.patch(url, json={"status": "cancelled"})
        assert cancelled.status_code == 200
        assert cancelled.json() == {**booking, "status": "cancelled"}
    history = client.get("/api/bookings", params={"user_id": "U006"}).json()
    assert len(history) == 1
    assert history[0]["status"] == "cancelled"
    deleted = client.delete(url)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get("/api/bookings", params={"user_id": "U006"}).json() == []
    assert client.delete(url).status_code == 404


def test_history_includes_confirmed_and_cancelled(client: TestClient) -> None:
    response = client.get("/api/bookings", params={"user_id": "U001"})
    assert response.status_code == 200
    assert {row["booking_id"]: row["status"] for row in response.json()} == {
        "B001": "confirmed", "B002": "cancelled",
    }
    assert all(row["user_id"] == "U001" for row in response.json())


@pytest.mark.parametrize(("user_id", "trip_id", "detail"), [
    ("missing", "T001", "User not found: missing"),
    ("U001", "missing", "Trip not found: missing"),
])
def test_create_missing_references(client: TestClient, user_id: str, trip_id: str, detail: str) -> None:
    response = client.post("/api/bookings", json={"user_id": user_id, "trip_id": trip_id})
    assert response.status_code == 404
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize("payload", [
    {}, {"user_id": "U001"}, {"trip_id": "T001"},
    {"user_id": "", "trip_id": "T001"},
    {"user_id": "U001", "trip_id": "   "},
    {"user_id": 1, "trip_id": "T001"},
    {"user_id": None, "trip_id": "T001"},
    {"user_id": "U001", "trip_id": "T001", "status": "cancelled"},
    {"user_id": "U001", "trip_id": "T001", "booking_id": "B001"},
])
def test_create_invalid_body(client: TestClient, payload: dict) -> None:
    before = client.get("/api/bookings", params={"user_id": "U001"}).json()
    assert client.post("/api/bookings", json=payload).status_code == 422
    assert client.get("/api/bookings", params={"user_id": "U001"}).json() == before


@pytest.mark.parametrize("payload", [
    {}, {"status": "confirmed"}, {"status": "invalid"}, {"status": None},
    {"status": "cancelled", "trip_id": "T002"},
])
def test_patch_only_accepts_cancellation(client: TestClient, payload: dict) -> None:
    assert client.patch("/api/bookings/B001", json=payload).status_code == 422
    history = client.get("/api/bookings", params={"user_id": "U001"}).json()
    assert next(row for row in history if row["booking_id"] == "B001")["status"] == "confirmed"


@pytest.mark.parametrize("params", [{}, {"user_id": ""}, {"user_id": "   "}])
def test_history_requires_user_id(client: TestClient, params: dict) -> None:
    assert client.get("/api/bookings", params=params).status_code == 422


def test_missing_records_return_404(client: TestClient) -> None:
    responses = [
        client.get("/api/bookings", params={"user_id": "missing"}),
        client.patch("/api/bookings/missing", json={"status": "cancelled"}),
        client.delete("/api/bookings/missing"),
    ]
    for response in responses:
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_instructor_booking_deletion_is_forbidden(client: TestClient) -> None:
    before = client.get("/api/bookings", params={"user_id": "U001"}).json()
    response = client.delete("/api/bookings/B001")
    assert response.status_code == 403
    assert response.json() == {"detail": "Instructor bookings cannot be deleted."}
    assert client.get("/api/bookings", params={"user_id": "U001"}).json() == before


def test_missing_and_malformed_json_bodies(client: TestClient) -> None:
    for method, path in [("POST", "/api/bookings"), ("PATCH", "/api/bookings/B001")]:
        assert client.request(method, path).status_code == 422
        assert client.request(
            method, path, content="{", headers={"Content-Type": "application/json"}
        ).status_code == 422
