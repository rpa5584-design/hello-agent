from datetime import date
from pathlib import Path
from uuid import UUID

import pytest

from app.controllers.booking_controller import (
    ProtectedBookingError,
    RecordNotFoundError,
    cancel_booking,
    create_booking,
    delete_test_booking,
    get_booking_history,
    list_users,
)
from app.database import connect_database, initialize_database


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "roomtour.sqlite3"
    initialize_database(path)
    return path


def booking_rows(database_path: Path) -> list[tuple]:
    with connect_database(database_path) as connection:
        return connection.execute("SELECT * FROM bookings ORDER BY booking_id").fetchall()


def test_list_demo_users(database_path: Path) -> None:
    assert [user.model_dump() for user in list_users(database_path)] == [
        {"user_id": f"U{i:03}", "display_name": f"Demo Traveler {i}"} for i in range(1, 7)
    ]


def test_create_unique_confirmed_bookings_preserves_instructor_rows(database_path: Path) -> None:
    original = booking_rows(database_path)
    first = create_booking("U001", "T001", database_path)
    second = create_booking("U001", "T001", database_path)
    assert first.booking_id != second.booking_id
    assert UUID(first.booking_id.removeprefix("B-")).version == 4
    assert first.status == "confirmed"
    assert first.booked_on == date.today().isoformat()
    rows = booking_rows(database_path)
    assert len(rows) == 8
    assert all(row in rows for row in original)
    assert (first.booking_id, "U001", "T001", first.booked_on, "confirmed") in rows


@pytest.mark.parametrize(("user_id", "trip_id", "message"), [
    ("missing", "T001", "User not found"),
    ("U001", "missing", "Trip not found"),
    ("U001' OR 1=1 --", "T001", "User not found"),
    ("U001", "T001' OR 1=1 --", "Trip not found"),
])
def test_invalid_references_leave_no_changes(
    database_path: Path, user_id: str, trip_id: str, message: str
) -> None:
    original = booking_rows(database_path)
    with pytest.raises(RecordNotFoundError, match=message):
        create_booking(user_id, trip_id, database_path)
    assert booking_rows(database_path) == original


def test_history_includes_both_statuses_and_joined_information(database_path: Path) -> None:
    created = create_booking("U001", "T001", database_path)
    history = get_booking_history("U001", database_path)
    assert {item.booking_id for item in history} == {"B001", "B002", created.booking_id}
    assert {item.status for item in history} == {"confirmed", "cancelled"}
    item = next(item for item in history if item.booking_id == created.booking_id)
    assert item.model_dump() == {
        **created.model_dump(), "trip_name": "Boston Harbor Weekend",
        "check_in": "2026-09-18", "check_out": "2026-09-20",
        "hotel_id": "H001", "hotel_name": "Harbor Lantern Hotel",
        "city": "Boston", "state": "MA", "nightly_rate_usd": 150.0,
    }
    assert all(item.user_id == "U001" for item in history)
    assert get_booking_history("U006", database_path) == []


def test_history_rejects_missing_user(database_path: Path) -> None:
    with pytest.raises(RecordNotFoundError, match="User not found"):
        get_booking_history("missing", database_path)


def test_cancel_retains_record_and_is_repeatable(database_path: Path) -> None:
    created = create_booking("U006", "T001", database_path)
    cancelled = cancel_booking(created.booking_id, database_path)
    assert cancelled.model_dump() == {**created.model_dump(), "status": "cancelled"}
    assert cancel_booking(created.booking_id, database_path) == cancelled
    assert len(booking_rows(database_path)) == 7
    assert get_booking_history("U006", database_path)[0].status == "cancelled"


def test_delete_generated_booking_preserves_starter_rows(database_path: Path) -> None:
    original = booking_rows(database_path)
    created = create_booking("U006", "T001", database_path)
    delete_test_booking(created.booking_id, database_path)
    assert get_booking_history("U006", database_path) == []
    assert booking_rows(database_path) == original
    with pytest.raises(ProtectedBookingError):
        delete_test_booking("B001", database_path)
    assert booking_rows(database_path) == original


@pytest.mark.parametrize("operation", [cancel_booking, delete_test_booking])
def test_missing_booking_is_rejected(database_path: Path, operation) -> None:
    original = booking_rows(database_path)
    with pytest.raises(RecordNotFoundError, match="Booking not found"):
        operation("missing' OR 1=1 --", database_path)
    assert booking_rows(database_path) == original


def test_crud_persists_across_reinitialization(database_path: Path) -> None:
    created = create_booking("U006", "T001", database_path)
    initialize_database(database_path)
    assert get_booking_history("U006", database_path)[0].booking_id == created.booking_id
    cancel_booking(created.booking_id, database_path)
    initialize_database(database_path)
    assert get_booking_history("U006", database_path)[0].status == "cancelled"
    delete_test_booking(created.booking_id, database_path)
    initialize_database(database_path)
    assert get_booking_history("U006", database_path) == []
    assert len(booking_rows(database_path)) == 6


def test_id_collision_retries_without_overwriting(database_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    created = create_booking("U006", "T001", database_path)
    collision = UUID(created.booking_id.removeprefix("B-"))
    replacement = UUID("12345678-1234-4234-8234-123456789abc")
    ids = iter([collision, replacement])
    monkeypatch.setattr("app.controllers.booking_controller.uuid4", lambda: next(ids))
    second = create_booking("U005", "T002", database_path)
    assert second.booking_id == f"B-{replacement.hex}"
    assert get_booking_history("U006", database_path)[0].trip_id == "T001"
    assert len(booking_rows(database_path)) == 8


def test_repeated_id_collisions_fail_without_changes(database_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    created = create_booking("U006", "T001", database_path)
    original = booking_rows(database_path)
    monkeypatch.setattr(
        "app.controllers.booking_controller.uuid4",
        lambda: UUID(created.booking_id.removeprefix("B-")),
    )
    with pytest.raises(RuntimeError, match="unique booking ID"):
        create_booking("U005", "T002", database_path)
    assert booking_rows(database_path) == original
