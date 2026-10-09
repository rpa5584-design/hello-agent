"""Bounded, authorized read-only hotel retrieval; no startup or migrations."""

import json
import sqlite3
import time
from dataclasses import dataclass

from app.config import get_geoapify_api_key, get_openrouter_api_key
from app.database import DATABASE_PATH
from app.services.sql_validation import FUNCTIONS, MAX_ROWS, TABLES, ValidatedSql, validate_sql

EXECUTION_SECONDS = 1.0
MAX_VM_STEPS = 1_000_000
MAX_RESULT_BYTES = 64_000


class RetrievalError(RuntimeError):
    """Retrieval failed or exceeded the safe resource bounds."""


@dataclass(frozen=True)
class RetrievalResult:
    executed_sql: str
    rows: list[dict[str, str | int | float | None]]


def _authorize(action, table, column, database, trigger):
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ and table in TABLES and (
        database == "main" or (database is None and column == "")
    ):
        return sqlite3.SQLITE_OK if column == "" or column in TABLES[table] else sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION and column and column.lower() in FUNCTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def retrieve(proposal: ValidatedSql) -> RetrievalResult:
    # Revalidate even typed inputs: callers cannot bypass validation by forging
    # a ValidatedSql instance. This happens before opening any database.
    checked = validate_sql(proposal.sql)
    connection = None
    try:
        connection = sqlite3.connect(DATABASE_PATH.resolve().as_uri() + "?mode=ro", uri=True, timeout=1.0)
        connection.execute("PRAGMA query_only=ON")
        connection.set_authorizer(_authorize)
        deadline = time.monotonic() + EXECUTION_SECONDS
        steps = 0
        def progress():
            nonlocal steps
            steps += 1000
            return int(steps >= MAX_VM_STEPS or time.monotonic() >= deadline)
        connection.set_progress_handler(progress, 1000)
        cursor = connection.execute(checked.sql)
        columns = [field[0] for field in cursor.description]
        if len(columns) > 20 or len(set(columns)) != len(columns):
            raise RetrievalError("Retrieval requires distinct, bounded output columns.")
        records = cursor.fetchmany(MAX_ROWS + 1)
        if len(records) > MAX_ROWS:
            raise RetrievalError("Retrieval exceeded the row bound.")
        rows = [dict(zip(columns, record)) for record in records]
        if any(not isinstance(value, (str, int, float, type(None))) for row in rows for value in row.values()):
            raise RetrievalError("Retrieval returned unsupported values.")
        encoded = json.dumps(rows, ensure_ascii=False, allow_nan=False)
        if len(encoded.encode("utf-8")) > MAX_RESULT_BYTES:
            raise RetrievalError("Retrieval exceeded the payload bound.")
        for credential in (get_openrouter_api_key(), get_geoapify_api_key()):
            if credential and credential in encoded:
                raise RetrievalError("Retrieval returned unsafe content.")
        return RetrievalResult(checked.sql, rows)
    except (sqlite3.Error, ValueError, TypeError):
        raise RetrievalError("Read-only hotel retrieval failed or exceeded its execution bounds.") from None
    finally:
        if connection is not None:
            connection.close()
