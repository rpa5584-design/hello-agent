"""Launch isolation checks without opening any database or provider."""

from fastapi.testclient import TestClient

from app import main
from app.assignment3.database import DATABASE_PATH


def test_assignment3_startup_is_independent(monkeypatch, tmp_path):
    def forbidden():
        raise AssertionError("RoomTour startup must not run")

    monkeypatch.setattr(main, "initialize_database", forbidden)
    monkeypatch.setattr(main, "load_hotel_assistant_prompt", forbidden)
    monkeypatch.setattr("app.assignment3.database.DATABASE_PATH", tmp_path / "assignment3.sqlite3")
    application = main.create_assignment3_app()
    with TestClient(application) as client:
        assert client.get("/api/assignment3/health").json() == {
            "status": "ok", "application": "assignment3"
        }
        assert client.get("/api/health").status_code == 404
        assert not hasattr(application.state, "hotel_assistant_prompt")
    assert DATABASE_PATH.name == "assignment3.sqlite3"
    assert DATABASE_PATH.parent.name == "data"


def test_roomtour_keeps_original_startup_and_routes(monkeypatch):
    calls = []
    monkeypatch.setattr(main, "load_hotel_assistant_prompt", lambda: calls.append("prompt") or "test prompt")
    monkeypatch.setattr(main, "initialize_database", lambda: calls.append("database"))
    with TestClient(main.app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/assignment3/health").status_code == 404
    assert calls == ["prompt", "database"]
