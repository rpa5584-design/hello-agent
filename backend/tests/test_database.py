import csv
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import DATA_DIR, connect_database, initialize_database
from app.main import app


EXPECTED_COUNTS = {"hotels": 8, "trips": 12, "users": 6, "bookings": 6}


def counts(database_path: Path) -> dict[str, int]:
    with connect_database(database_path) as connection:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in EXPECTED_COUNTS
        }


def test_first_initialization_preserves_all_csv_values(tmp_path: Path) -> None:
    database_path = tmp_path / "roomtour.sqlite3"
    initialize_database(database_path)

    assert counts(database_path) == EXPECTED_COUNTS
    with connect_database(database_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        for table in EXPECTED_COUNTS:
            with (DATA_DIR / f"{table}.csv").open(encoding="utf-8-sig", newline="") as source:
                reader = csv.DictReader(source)
                columns = reader.fieldnames
                expected = []
                for row in reader:
                    expected.append(tuple(
                        float(row[column]) if column == "nightly_rate_usd" else row[column]
                        for column in columns
                    ))
            actual = connection.execute(f"SELECT * FROM {table}").fetchall()
            assert sorted(actual) == sorted(expected)
            assert [row[1] for row in connection.execute(f"PRAGMA table_info({table})")] == columns


def test_foreign_keys_are_valid_and_declared(tmp_path: Path) -> None:
    database_path = tmp_path / "roomtour.sqlite3"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        for table, expected in {
            "trips": {("hotel_id", "hotels", "hotel_id")},
            "bookings": {("user_id", "users", "user_id"), ("trip_id", "trips", "trip_id")},
        }.items():
            actual = {(row[3], row[2], row[4]) for row in connection.execute(f"PRAGMA foreign_key_list({table})")}
            assert actual == expected


@pytest.mark.parametrize("statement", [
    "UPDATE trips SET hotel_id = 'missing' WHERE trip_id = 'T001'",
    "UPDATE bookings SET user_id = 'missing' WHERE booking_id = 'B001'",
    "UPDATE bookings SET trip_id = 'missing' WHERE booking_id = 'B001'",
])
def test_broken_references_are_rejected(tmp_path: Path, statement: str) -> None:
    database_path = tmp_path / "roomtour.sqlite3"
    initialize_database(database_path)
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        with connect_database(database_path) as connection:
            connection.execute(statement)


def test_reinitialization_does_not_reload_or_duplicate_rows(tmp_path: Path) -> None:
    database_path = tmp_path / "roomtour.sqlite3"
    initialize_database(database_path)
    # No CSVs exist here: a later initialization must not even read them.
    initialize_database(database_path, data_dir=tmp_path / "missing-csvs")
    initialize_database(database_path)
    assert counts(database_path) == EXPECTED_COUNTS


def test_updates_and_deletions_persist_after_reinitialization(tmp_path: Path) -> None:
    database_path = tmp_path / "roomtour.sqlite3"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        connection.execute("UPDATE users SET display_name = ? WHERE user_id = ?", ("Edited traveler", "U001"))
        connection.execute("DELETE FROM bookings")

    initialize_database(database_path)
    with connect_database(database_path) as connection:
        assert connection.execute("SELECT display_name FROM users WHERE user_id = 'U001'").fetchone() == ("Edited traveler",)
        assert connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0] == 0


def test_failed_seed_rolls_back_and_is_not_silently_retried(tmp_path: Path) -> None:
    database_path = tmp_path / "roomtour.sqlite3"
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    # Hotels import succeeds before the missing trips CSV aborts initialization.
    (seed_dir / "hotels.csv").write_bytes((DATA_DIR / "hotels.csv").read_bytes())
    with pytest.raises(FileNotFoundError):
        initialize_database(database_path, seed_dir)
    with connect_database(database_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
        assert connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall() == []
    with pytest.raises(RuntimeError, match="uninitialized or unsupported"):
        initialize_database(database_path)


def test_application_startup_preserves_database_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_path = tmp_path / "roomtour.sqlite3"
    monkeypatch.setattr("app.main.initialize_database", lambda: initialize_database(database_path))
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        assert counts(database_path) == EXPECTED_COUNTS
        with connect_database(database_path) as connection:
            connection.execute("UPDATE bookings SET status = 'cancelled' WHERE booking_id = 'B001'")
    with TestClient(app) as client:
        stays = client.get("/api/stays", params={"hotel_name": "Harbor"}).json()["stays"]
        assert [stay["trip_id"] for stay in stays] == ["T001", "T009"]
        with connect_database(database_path) as connection:
            assert connection.execute("SELECT status FROM bookings WHERE booking_id = 'B001'").fetchone() == ("cancelled",)
        assert counts(database_path) == EXPECTED_COUNTS
