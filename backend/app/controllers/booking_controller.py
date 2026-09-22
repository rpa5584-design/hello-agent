"""Booking operations using the existing SQLite connection/transaction helper."""

import re
import sqlite3
from datetime import date
from pathlib import Path
from uuid import uuid4

from app.database import DATABASE_PATH, connect_database
from app.models import Booking, BookingHistoryItem, User


class RecordNotFoundError(LookupError):
    """A requested user, trip, or booking does not exist."""


class ProtectedBookingError(ValueError):
    """Only generated test bookings may be permanently deleted."""


def _require_user(connection: sqlite3.Connection, user_id: str) -> None:
    if connection.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
        raise RecordNotFoundError(f"User not found: {user_id}")


def _get_booking(connection: sqlite3.Connection, booking_id: str) -> Booking:
    row = connection.execute(
        "SELECT booking_id, user_id, trip_id, booked_on, status FROM bookings WHERE booking_id = ?",
        (booking_id,),
    ).fetchone()
    if row is None:
        raise RecordNotFoundError(f"Booking not found: {booking_id}")
    return Booking(**dict(row))


def list_users(database_path: Path = DATABASE_PATH) -> list[User]:
    with connect_database(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT user_id, display_name FROM users ORDER BY user_id")
        return [User(**dict(row)) for row in rows]


def create_booking(
    user_id: str, trip_id: str, database_path: Path = DATABASE_PATH
) -> Booking:
    with connect_database(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        _require_user(connection, user_id)
        if connection.execute("SELECT 1 FROM trips WHERE trip_id = ?", (trip_id,)).fetchone() is None:
            raise RecordNotFoundError(f"Trip not found: {trip_id}")
        for _ in range(5):
            booking = Booking(
                booking_id=f"B-{uuid4().hex}",
                user_id=user_id,
                trip_id=trip_id,
                booked_on=date.today().isoformat(),
                status="confirmed",
            )
            result = connection.execute(
                """INSERT INTO bookings (booking_id, user_id, trip_id, booked_on, status)
                   VALUES (?, ?, ?, ?, ?) ON CONFLICT(booking_id) DO NOTHING""",
                (booking.booking_id, booking.user_id, booking.trip_id, booking.booked_on, booking.status),
            )
            if result.rowcount == 1:
                return booking
        raise RuntimeError("Could not generate a unique booking ID after five attempts.")


def get_booking_history(
    user_id: str, database_path: Path = DATABASE_PATH
) -> list[BookingHistoryItem]:
    with connect_database(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN")
        _require_user(connection, user_id)
        rows = connection.execute(
            """SELECT b.booking_id, b.user_id, b.trip_id, b.booked_on, b.status,
                      t.trip_name, t.check_in, t.check_out,
                      h.hotel_id, h.hotel_name, h.city, h.state, h.nightly_rate_usd
               FROM bookings AS b
               JOIN trips AS t ON t.trip_id = b.trip_id
               JOIN hotels AS h ON h.hotel_id = t.hotel_id
               WHERE b.user_id = ?
               ORDER BY b.booked_on DESC, b.booking_id""",
            (user_id,),
        )
        return [BookingHistoryItem(**dict(row)) for row in rows]


def cancel_booking(booking_id: str, database_path: Path = DATABASE_PATH) -> Booking:
    with connect_database(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN IMMEDIATE")
        _get_booking(connection, booking_id)
        connection.execute(
            "UPDATE bookings SET status = ? WHERE booking_id = ?", ("cancelled", booking_id)
        )
        return _get_booking(connection, booking_id)


def delete_test_booking(booking_id: str, database_path: Path = DATABASE_PATH) -> None:
    with connect_database(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN IMMEDIATE")
        _get_booking(connection, booking_id)
        if re.fullmatch(r"B-[0-9a-f]{32}", booking_id) is None:
            raise ProtectedBookingError("Instructor bookings cannot be deleted.")
        connection.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
