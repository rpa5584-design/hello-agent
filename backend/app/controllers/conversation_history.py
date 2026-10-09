"""Backend-controlled append-only trace writes, separate from hotel retrieval."""

import re
import sqlite3
from datetime import datetime, timezone

from app.config import get_geoapify_api_key, get_openrouter_api_key
from app.database import DATABASE_PATH


class HistoryError(RuntimeError):
    """Trace persistence or reading failed."""


def safe_content(content: str) -> str:
    for credential in (get_openrouter_api_key(), get_geoapify_api_key()):
        if credential:
            content = content.replace(credential, "[REDACTED]")
    content = re.sub(r"(?i)\bauthorization\s*[=:]\s*(?:bearer\s+)?[^\s\"',}]+", "[REDACTED]", content)
    content = re.sub(r"(?i)\bBearer\s+[^\s\"',}]+", "[REDACTED]", content)
    content = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[REDACTED]", content)
    content = re.sub(r"(?i)(?:OPENROUTER_API_KEY|GEOAPIFY_API_KEY)\s*[=:]\s*[^\s\"',}]+", "[REDACTED]", content)
    return content[:100_000]


def _authorize(action, table, column, database, trigger):
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_TRANSACTION):
        return sqlite3.SQLITE_OK
    if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_READ) and table == "conversation_history":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def append(conversation_id: str, role: str, stage: str, content: str) -> None:
    connection = None
    try:
        connection = sqlite3.connect(DATABASE_PATH.resolve().as_uri() + "?mode=rw", uri=True, timeout=2.0)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.set_authorizer(_authorize)
        with connection:
            connection.execute(
                "INSERT INTO conversation_history (conversation_id, timestamp, role, content, stage) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, datetime.now(timezone.utc).isoformat(timespec="microseconds"), role, safe_content(content), stage),
            )
    except sqlite3.Error:
        raise HistoryError("Conversation history could not be persisted.") from None
    finally:
        if connection is not None:
            connection.close()


def load(conversation_id: str, after_message_id: int = 0) -> list[dict]:
    connection = None
    try:
        connection = sqlite3.connect(DATABASE_PATH.resolve().as_uri() + "?mode=ro", uri=True, timeout=2.0)
        connection.execute("PRAGMA query_only=ON")
        connection.set_authorizer(_authorize)
        connection.row_factory = sqlite3.Row
        records = connection.execute(
            "SELECT message_id, conversation_id, timestamp, role, content, stage FROM conversation_history WHERE conversation_id=? AND message_id>? ORDER BY message_id LIMIT 100",
            (conversation_id, after_message_id),
        ).fetchall()
        return [{**dict(record), "content": safe_content(record["content"])} for record in records]
    except sqlite3.Error:
        raise HistoryError("Conversation history could not be loaded.") from None
    finally:
        if connection is not None:
            connection.close()
