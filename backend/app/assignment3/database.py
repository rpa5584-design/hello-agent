"""Independent SQLite storage for Assignment 3 only."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from collections.abc import Iterator

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "assignment3.sqlite3"


@contextmanager
def connect(path: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(path, timeout=2)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("""CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY NOT NULL,
            selected_skill TEXT NOT NULL CHECK(selected_skill='paced_breathing_4_6'),
            started_at TEXT NOT NULL,
            ended_at TEXT,
            status TEXT NOT NULL CHECK(status IN ('active','completed','stopped','interrupted')),
            measured_duration_seconds REAL CHECK(measured_duration_seconds >= 0),
            fewer_options INTEGER NOT NULL DEFAULT 0 CHECK(fewer_options IN (0,1)),
            CHECK((status='active' AND ended_at IS NULL AND measured_duration_seconds IS NULL)
                OR (status!='active' AND ended_at IS NOT NULL))
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS conversation_messages (
            message_id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','assistant','error')),
            content TEXT NOT NULL CHECK(length(content) BETWEEN 1 AND 1000),
            CHECK(role!='user' OR length(content)<=300)
        )""")
        connection.execute("CREATE INDEX IF NOT EXISTS conversation_order ON conversation_messages(session_id, message_id)")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_user_or_assistant ON conversation_messages(session_id, role) WHERE role IN ('user','assistant')")
        connection.execute("""CREATE TABLE IF NOT EXISTS reflection_requests (
            session_id TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
            attempts INTEGER NOT NULL CHECK(attempts BETWEEN 1 AND 3),
            status TEXT NOT NULL CHECK(status IN ('pending','error','success')),
            token TEXT NOT NULL,
            lease_until REAL NOT NULL
        )""")
