"""SQLite connections and one-time database initialization."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.seed import seed_database


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATABASE_PATH = DATA_DIR / "roomtour.sqlite3"

SCHEMA = (
    """CREATE TABLE hotels (
        hotel_id TEXT PRIMARY KEY NOT NULL,
        hotel_name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        nightly_rate_usd REAL NOT NULL
    )""",
    """CREATE TABLE trips (
        trip_id TEXT PRIMARY KEY NOT NULL,
        hotel_id TEXT NOT NULL REFERENCES hotels(hotel_id),
        trip_name TEXT NOT NULL,
        check_in TEXT NOT NULL,
        check_out TEXT NOT NULL
    )""",
    """CREATE TABLE users (
        user_id TEXT PRIMARY KEY NOT NULL,
        display_name TEXT NOT NULL
    )""",
    """CREATE TABLE bookings (
        booking_id TEXT PRIMARY KEY NOT NULL,
        user_id TEXT NOT NULL REFERENCES users(user_id),
        trip_id TEXT NOT NULL REFERENCES trips(trip_id),
        booked_on TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled'))
    )""",
)


@contextmanager
def connect_database(database_path: Path = DATABASE_PATH) -> Iterator[sqlite3.Connection]:
    """Open an existing database with foreign keys and managed transactions."""
    connection = sqlite3.connect(database_path.resolve().as_uri() + "?mode=rw", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database(
    database_path: Path = DATABASE_PATH, data_dir: Path = DATA_DIR
) -> None:
    """Seed only a newly created database; never repair/reseed an existing file."""
    try:
        # Exclusive creation prevents treating an existing empty file as a new DB.
        with database_path.open("xb"):
            pass
        newly_created = True
    except FileExistsError:
        newly_created = False

    with connect_database(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version == 1:
            return
        if not newly_created:
            raise RuntimeError(
                f"Existing database is uninitialized or unsupported: {database_path}. "
                "Inspect it before recovery; starter data will not be reloaded."
            )
        for statement in SCHEMA:
            connection.execute(statement)
        seed_database(connection, data_dir)
        connection.execute("PRAGMA user_version = 1")
