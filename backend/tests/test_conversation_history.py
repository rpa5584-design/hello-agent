import json
import sqlite3
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import CONVERSATION_SCHEMA, initialize_database
from app.controllers import conversation_history, rag_retrieval
from app.services import openrouter
from app.services.sql_validation import SqlValidationError, validate_sql

SQL = "SELECT hotel_id, name FROM saved_hotels LIMIT 3"
OLD_TABLES = ("hotels", "trips", "users", "bookings", "saved_hotels", "saved_hotel_zips", "demo_hotel_nights")


def snapshot(path):
    with sqlite3.connect(path) as connection:
        return {table: connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall() for table in OLD_TABLES}


@pytest.fixture
def database(tmp_path, monkeypatch):
    path = tmp_path / "history.sqlite3"
    initialize_database(path)
    monkeypatch.setattr(conversation_history, "DATABASE_PATH", path)
    monkeypatch.setattr(rag_retrieval, "DATABASE_PATH", path)
    monkeypatch.setattr(app.state, "hotel_assistant_prompt", "loaded prompt", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "history-fake-secret")
    monkeypatch.setenv("GEOAPIFY_API_KEY", "geo-fake-secret")
    monkeypatch.setenv("OPENROUTER_MODEL", "test/model:free")
    return path


@pytest.fixture
def provider(monkeypatch):
    calls = []
    def install(sql=SQL, failure_stage=None):
        calls.clear()
        def handle(request):
            calls.append(json.loads(request.content))
            if len(calls) == failure_stage:
                return httpx.Response(500, json={"error": "history-fake-secret"})
            text = sql if len(calls) == 1 else "No matching local data. Simulated classroom data."
            return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": text}}]})
        monkeypatch.setattr(openrouter.httpx, "HTTPTransport", lambda **kwargs: httpx.MockTransport(handle))
        return calls
    return install


def test_persisted_success_trace_empty_rows_and_restart(database, provider):
    before = snapshot(database)
    provider()
    client = TestClient(app)
    response = client.post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 200
    cid = response.json()["conversation_id"]
    history = client.get(f"/api/rag/conversations/{cid}").json()["messages"]
    assert [record["stage"] for record in history] == ["user_question", "proposed_sql", "executed_sql", "retrieval_result", "assistant_answer"]
    assert {record["conversation_id"] for record in history} == {cid}
    assert [record["role"] for record in history] == ["user", "system", "system", "system", "assistant"]
    assert json.loads(history[3]["content"]) == {"row_count": 0, "rows": []}
    assert history[4]["content"] == response.json()["answer"]
    assert [r["message_id"] for r in history] == sorted(r["message_id"] for r in history)
    assert all(r["timestamp"].endswith("+00:00") for r in history)
    initialize_database(database, data_dir=database.parent / "no-csvs")
    assert conversation_history.load(cid) == history
    assert TestClient(app).get(f"/api/rag/conversations/{cid}").json()["messages"] == history
    assert snapshot(database) == before


@pytest.mark.parametrize("failure_stage,expected", [(1, ["user_question", "error"]), (2, ["user_question", "proposed_sql", "executed_sql", "retrieval_result", "error"])])
def test_provider_failure_trace_has_no_success(database, provider, failure_stage, expected):
    calls = provider(failure_stage=failure_stage)
    response = TestClient(app).post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 502
    records = conversation_history.load(response.json()["conversation_id"])
    assert [r["stage"] for r in records] == expected
    assert len(calls) == failure_stage
    assert "history-fake-secret" not in json.dumps(records)
    assert "assistant_answer" not in [r["stage"] for r in records]


def test_failed_retrieval_records_proposal_and_error(database, provider, monkeypatch):
    calls = provider()
    def fail(*args):
        raise rag_retrieval.RetrievalError("history-fake-secret")
    monkeypatch.setattr(rag_retrieval, "retrieve", fail)
    response = TestClient(app).post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 503
    records = conversation_history.load(response.json()["conversation_id"])
    assert [r["stage"] for r in records] == ["user_question", "proposed_sql", "error"]
    assert "history-fake-secret" not in json.dumps(records)
    assert len(calls) == 1


def test_invalid_proposal_persisted_before_validation_error(database, provider):
    provider(sql="DELETE FROM saved_hotels")
    response = TestClient(app).post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 422
    records = conversation_history.load(response.json()["conversation_id"])
    assert [r["stage"] for r in records] == ["user_question", "proposed_sql", "error"]
    assert records[1]["content"] == "DELETE FROM saved_hotels"


def test_reuse_conversation_and_cursor_order(database, provider):
    cid = str(uuid4())
    client = TestClient(app)
    for i in range(2):
        provider()
        response = client.post("/api/rag/answer", json={"question": f"Hotels {i}?", "conversation_id": cid})
        assert response.json()["conversation_id"] == cid
    records = conversation_history.load(cid)
    assert len(records) == 10
    later = client.get(f"/api/rag/conversations/{cid}?after_message_id={records[4]['message_id']}").json()
    assert later["messages"] == records[5:]
    assert later["next_after_message_id"] == records[-1]["message_id"]


def test_credentials_and_authorization_never_stored(database):
    cid = str(uuid4())
    conversation_history.append(cid, "user", "user_question", "history-fake-secret geo-fake-secret Authorization: Bearer another-token OPENROUTER_API_KEY=unknown-value sk-another-secret")
    with sqlite3.connect(database) as connection:
        stored = connection.execute("SELECT content FROM conversation_history").fetchone()[0]
    for secret in ("history-fake-secret", "geo-fake-secret", "another-token", "unknown-value", "sk-another-secret"):
        assert secret not in stored
    assert "[REDACTED]" in stored
    assert "Authorization:" not in stored


def test_nonempty_retrieval_trace(database, provider):
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO saved_hotels VALUES ('kept', 'Saved Hotel', NULL, 40, -75)")
    before = snapshot(database)
    provider()
    response = TestClient(app).post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 200
    records = conversation_history.load(response.json()["conversation_id"])
    result = json.loads(records[3]["content"])
    assert result == {"row_count": 1, "rows": [{"hotel_id": "kept", "name": "Saved Hotel"}]}
    assert records[4]["content"] == response.json()["answer"]
    assert snapshot(database) == before


def test_missing_prompt_stores_error_without_provider(database, provider, monkeypatch):
    calls = provider()
    monkeypatch.setattr(app.state, "hotel_assistant_prompt", None)
    response = TestClient(app).post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 503
    assert calls == []
    assert [r["stage"] for r in conversation_history.load(response.json()["conversation_id"])] == ["user_question", "error"]


def test_logging_authorizer_cannot_write_hotels(database):
    with sqlite3.connect(database) as connection:
        connection.set_authorizer(conversation_history._authorize)
        for sql in ("DELETE FROM conversation_history", "UPDATE saved_hotels SET name='x'", "INSERT INTO saved_hotels VALUES ('x','x',NULL,40,-75)"):
            with pytest.raises(sqlite3.DatabaseError):
                connection.execute(sql)


def test_history_never_accessible_to_model_sql(database):
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT content FROM conversation_history LIMIT 20")
    with sqlite3.connect(database) as connection:
        connection.set_authorizer(rag_retrieval._authorize)
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("SELECT content FROM conversation_history")


def test_version3_migration_preserves_existing_data(database):
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO saved_hotels VALUES ('kept', 'Keep', NULL, 40, -75)")
        connection.execute("INSERT INTO saved_hotel_zips VALUES ('kept', '16803', 40, -75, NULL, 'us')")
        connection.execute("INSERT INTO demo_hotel_nights VALUES ('kept', '2026-10-11', 12345, 7)")
        connection.execute("DROP TABLE conversation_history")
        connection.execute("PRAGMA user_version=3")
    before = snapshot(database)
    initialize_database(database)
    initialize_database(database, data_dir=database.parent / "missing")
    assert snapshot(database) == before
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
        assert connection.execute("SELECT COUNT(*) FROM conversation_history").fetchone()[0] == 0


def test_migration_failure_rolls_back(database, monkeypatch):
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TABLE conversation_history")
        connection.execute("PRAGMA user_version=3")
    monkeypatch.setattr("app.database.CONVERSATION_SCHEMA", (*CONVERSATION_SCHEMA, "INVALID SQL"))
    with pytest.raises(sqlite3.Error):
        initialize_database(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='conversation_history'").fetchall() == []


def test_history_failure_stops_provider(database, provider, monkeypatch):
    calls = provider()
    monkeypatch.setattr(conversation_history, "DATABASE_PATH", database.parent / "absent.db")
    response = TestClient(app).post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 503
    assert calls == []


def test_transient_trace_failure_persists_error(database, provider, monkeypatch):
    calls = provider()
    original_append = conversation_history.append
    appends = 0
    def append(*args):
        nonlocal appends
        appends += 1
        if appends == 2:
            raise conversation_history.HistoryError("Cannot append proposal")
        return original_append(*args)
    monkeypatch.setattr(conversation_history, "append", append)
    response = TestClient(app).post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 503
    assert len(calls) == 1
    assert [r["stage"] for r in conversation_history.load(response.json()["conversation_id"])] == ["user_question", "error"]
