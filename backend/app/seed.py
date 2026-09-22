"""Import the instructor CSVs within the caller's initialization transaction."""

import csv
import sqlite3
from pathlib import Path


CSV_COLUMNS = {
    "hotels": ("hotel_id", "hotel_name", "city", "state", "nightly_rate_usd"),
    "trips": ("trip_id", "hotel_id", "trip_name", "check_in", "check_out"),
    "users": ("user_id", "display_name"),
    "bookings": ("booking_id", "user_id", "trip_id", "booked_on", "status"),
}


def seed_database(connection: sqlite3.Connection, data_dir: Path) -> None:
    for table, columns in CSV_COLUMNS.items():
        with (data_dir / f"{table}.csv").open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != list(columns):
                raise ValueError(f"Unexpected columns in {table}.csv")
            # Identifiers come only from the fixed mapping; CSV values are bound.
            placeholders = ", ".join("?" for _ in columns)
            connection.executemany(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                (tuple(row[column] for column in columns) for row in reader),
            )
