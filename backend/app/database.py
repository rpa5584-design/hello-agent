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

# API mapping: place_id -> hotel_id, name -> name,
# formatted_address -> address, latitude/longitude -> latitude/longitude.
# Provider identity is stored verbatim with SQLite's default binary comparison.
LOCAL_STORAGE_SCHEMA = (
    """CREATE TABLE saved_hotels (
        hotel_id TEXT PRIMARY KEY NOT NULL,
        name TEXT,
        address TEXT,
        latitude REAL NOT NULL CHECK (
            typeof(latitude) IN ('integer', 'real') AND latitude BETWEEN -90 AND 90
        ),
        longitude REAL NOT NULL CHECK (
            typeof(longitude) IN ('integer', 'real') AND longitude BETWEEN -180 AND 180
        )
    )""",
    """CREATE TABLE demo_hotel_nights (
        hotel_id TEXT NOT NULL REFERENCES saved_hotels(hotel_id),
        stay_date TEXT NOT NULL CHECK (
            stay_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
            AND date(stay_date, '+0 days') IS NOT NULL
            AND date(stay_date, '+0 days') = stay_date
        ),
        nightly_rate_cents INTEGER NOT NULL DEFAULT 10000 CHECK (
            typeof(nightly_rate_cents) = 'integer' AND nightly_rate_cents >= 0
        ),
        rooms_available INTEGER NOT NULL DEFAULT 20 CHECK (
            typeof(rooms_available) = 'integer' AND rooms_available >= 0
        ),
        PRIMARY KEY (hotel_id, stay_date)
    )""",
)


ZIP_ASSOCIATION_SCHEMA = """CREATE TABLE saved_hotel_zips (
    hotel_id TEXT NOT NULL REFERENCES saved_hotels(hotel_id),
    zip_code TEXT NOT NULL CHECK (zip_code GLOB '[0-9][0-9][0-9][0-9][0-9]'),
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    locality TEXT,
    country_code TEXT NOT NULL CHECK (country_code = 'us'),
    PRIMARY KEY (hotel_id, zip_code)
)"""

CONVERSATION_SCHEMA = (
    """CREATE TABLE conversation_history (
        message_id INTEGER PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('user', 'system', 'assistant')),
        content TEXT NOT NULL,
        stage TEXT NOT NULL CHECK (stage IN (
            'user_question', 'proposed_sql', 'executed_sql',
            'retrieval_result', 'assistant_answer', 'error'
        ))
    )""",
    "CREATE INDEX conversation_history_order ON conversation_history(conversation_id, message_id)",
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
    """Seed new databases only, then apply transactional, versioned migrations."""
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
        if version == 4:
            return
        if version in (1, 2, 3):
            if version == 1:
                for statement in LOCAL_STORAGE_SCHEMA:
                    connection.execute(statement)
            if version < 3:
                connection.execute(ZIP_ASSOCIATION_SCHEMA)
            for statement in CONVERSATION_SCHEMA:
                connection.execute(statement)
            connection.execute("PRAGMA user_version = 4")
            return
        if not newly_created:
            raise RuntimeError(
                f"Existing database is uninitialized or unsupported: {database_path}. "
                "Inspect it before recovery; starter data will not be reloaded."
            )
        for statement in SCHEMA:
            connection.execute(statement)
        seed_database(connection, data_dir)
        for statement in LOCAL_STORAGE_SCHEMA:
            connection.execute(statement)
        connection.execute(ZIP_ASSOCIATION_SCHEMA)
        for statement in CONVERSATION_SCHEMA:
            connection.execute(statement)
        connection.execute("PRAGMA user_version = 4")
