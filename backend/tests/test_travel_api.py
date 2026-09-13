import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_partial_hotel_name_search_returns_joined_stay() -> None:
    response = client.get("/api/stays", params={"hotel_name": "  rIvErSiDe  "})

    assert response.status_code == 200
    assert response.json() == {"stays": [{
        "hotel_id": "H004",
        "hotel_name": "Riverside Studio Hotel",
        "city": "New York",
        "state": "NY",
        "nightly_rate_usd": 175.0,
        "trip_id": "T004",
        "trip_name": "New York Riverside Stay",
        "check_in": "2026-09-25",
        "check_out": "2026-09-28",
    }]}


def test_hotel_with_multiple_trips_returns_every_stay() -> None:
    response = client.get("/api/stays", params={"hotel_name": "Harbor Lantern Hotel"})

    assert response.status_code == 200
    stays = response.json()["stays"]
    assert [stay["trip_id"] for stay in stays] == ["T001", "T009"]
    assert all(stay["hotel_id"] == "H001" for stay in stays)
    assert [stay["check_in"] for stay in stays] == ["2026-09-18", "2026-10-02"]


def test_search_with_no_matches_returns_empty_list() -> None:
    response = client.get("/api/stays", params={"hotel_name": "Nonexistent Hotel"})

    assert response.status_code == 200
    assert response.json() == {"stays": []}


@pytest.mark.parametrize("params", [{}, {"hotel_name": ""}, {"hotel_name": "   "}])
def test_search_requires_nonblank_hotel_name(params: dict[str, str]) -> None:
    assert client.get("/api/stays", params=params).status_code == 422
