"""Parameterized transactional session operations."""
from .database import connect
from pathlib import Path
from uuid import UUID
from .models import SessionStart, SessionEnd


class ConflictError(Exception):
    pass


def get(path: Path, session_id: UUID) -> dict | None:
    with connect(path) as connection:
        row = connection.execute("SELECT * FROM sessions WHERE session_id=?", (str(session_id),)).fetchone()
        return dict(row) if row else None


def create(path: Path, request: SessionStart) -> dict:
    sid = str(request.session_id)
    with connect(path) as connection:
        connection.execute("INSERT INTO sessions (session_id, selected_skill, started_at, status, fewer_options) VALUES (?, ?, ?, 'active', ?) ON CONFLICT(session_id) DO NOTHING", (sid, request.selected_skill, request.started_at.isoformat(), int(request.fewer_options)))
        row = dict(connection.execute("SELECT * FROM sessions WHERE session_id=?", (sid,)).fetchone())
        if (row['started_at'], row['selected_skill'], bool(row['fewer_options'])) != (request.started_at.isoformat(), request.selected_skill, request.fewer_options):
            raise ConflictError()
        return row


def finish(path: Path, session_id: UUID, request: SessionEnd) -> dict | None:
    with connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT * FROM sessions WHERE session_id=?", (str(session_id),)).fetchone()
        if row is None:
            return None
        if request.ended_at.isoformat() < row['started_at']:
            raise ConflictError()
        values = (request.status, request.ended_at.isoformat(), request.measured_duration_seconds)
        if row['status'] != 'active':
            if (row['status'], row['ended_at'], row['measured_duration_seconds']) != values:
                raise ConflictError()
        else:
            connection.execute("UPDATE sessions SET status=?, ended_at=?, measured_duration_seconds=? WHERE session_id=?", (*values, str(session_id)))
        return dict(connection.execute("SELECT * FROM sessions WHERE session_id=?", (str(session_id),)).fetchone())


def list_sessions(path: Path, limit: int, offset: int) -> list[dict]:
    with connect(path) as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM sessions ORDER BY started_at DESC, session_id LIMIT ? OFFSET ?", (limit, offset))]
