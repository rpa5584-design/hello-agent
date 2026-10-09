import json
import sqlite3

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import initialize_database
from app.controllers import conversation_history, rag_retrieval
from app.services import openrouter, rag_answer
from app.services.sql_validation import SqlValidationError, ValidatedSql, validate_sql

SQL = """SELECT h.hotel_id, h.name, n.stay_date, n.nightly_rate_cents, n.rooms_available
FROM saved_hotels h JOIN saved_hotel_zips z ON h.hotel_id=z.hotel_id
JOIN demo_hotel_nights n ON h.hotel_id=n.hotel_id
WHERE z.zip_code='16803' AND n.stay_date='2026-10-11' AND n.rooms_available>0
ORDER BY n.nightly_rate_cents LIMIT 3"""


@pytest.fixture
def database(tmp_path, monkeypatch):
    path = tmp_path / "test.sqlite3"
    initialize_database(path)
    monkeypatch.setattr(rag_retrieval, "DATABASE_PATH", path)
    monkeypatch.setattr(conversation_history, "DATABASE_PATH", path)
    with sqlite3.connect(path) as connection:
        for i in range(30):
            hotel_id = f"hotel-{i:02}"
            connection.execute("INSERT INTO saved_hotels VALUES (?, ?, NULL, 40, -75)", (hotel_id, f"Hotel {i}"))
            connection.execute("INSERT INTO saved_hotel_zips VALUES (?, '16803', 40, -75, 'Test', 'us')", (hotel_id,))
            connection.execute("INSERT INTO demo_hotel_nights VALUES (?, '2026-10-11', ?, 20)", (hotel_id, 10000 + i))
    return path


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "rag-fake-secret")
    monkeypatch.setenv("OPENROUTER_MODEL", "test/model:free")
    calls = []
    def install(sql=SQL, answer="Hotel 0 is $100.00 for the requested night, with 20 rooms. Simulated classroom data.", failure_stage=None):
        calls.clear()
        def handle(request):
            calls.append(json.loads(request.content))
            if len(calls) == failure_stage:
                return httpx.Response(500, json={"error": "rag-fake-secret"})
            text = sql if len(calls) == 1 else answer
            return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": text}}]})
        monkeypatch.setattr(openrouter.httpx, "HTTPTransport", lambda **kwargs: httpx.MockTransport(handle))
        return calls
    return install


def test_successful_retrieval_preserves_database(database):
    before = database.read_bytes()
    result = rag_retrieval.retrieve(validate_sql(SQL))
    assert len(result.rows) == 3
    assert result.rows[0]["nightly_rate_cents"] == 10000
    assert result.rows[0]["stay_date"] == "2026-10-11"
    assert database.read_bytes() == before


def test_limit_is_revalidated_and_capped(database):
    forged = ValidatedSql("SELECT hotel_id FROM saved_hotels LIMIT 999", (), "untrusted")
    result = rag_retrieval.retrieve(forged)
    assert len(result.rows) == 20
    assert result.executed_sql.endswith("LIMIT 20")


@pytest.mark.parametrize("sql", ["DELETE FROM saved_hotels", "UPDATE saved_hotels SET name='x'", "SELECT * FROM users LIMIT 1", "SELECT * FROM saved_hotels"])
def test_invalid_query_never_opens_sqlite(monkeypatch, sql):
    def forbidden(*args, **kwargs):
        pytest.fail("Rejected SQL must not reach SQLite")
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    with pytest.raises(SqlValidationError):
        rag_retrieval.retrieve(ValidatedSql(sql, (), sql))


def test_authorizer_blocks_writes_and_unapproved_reads(database):
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.set_authorizer(rag_retrieval._authorize)
        for sql in ("DELETE FROM saved_hotels", "SELECT * FROM users", "PRAGMA user_version", "ATTACH ':memory:' AS other", "SELECT sqlite_version()"):
            with pytest.raises(sqlite3.DatabaseError):
                connection.execute(sql)
        assert connection.execute("SELECT COUNT(*) FROM saved_hotels").fetchone()[0] == 30


def test_execution_failure_is_safe(database):
    # Validator allows the column globally; SQLite rejects this ambiguous name.
    sql = "SELECT hotel_id FROM saved_hotels h JOIN demo_hotel_nights n ON h.hotel_id=n.hotel_id LIMIT 3"
    with pytest.raises(rag_retrieval.RetrievalError, match="Read-only hotel retrieval failed"):
        rag_retrieval.retrieve(validate_sql(sql))


def test_missing_database_is_not_created(tmp_path, monkeypatch):
    path = tmp_path / "absent.sqlite3"
    monkeypatch.setattr(rag_retrieval, "DATABASE_PATH", path)
    with pytest.raises(rag_retrieval.RetrievalError):
        rag_retrieval.retrieve(validate_sql("SELECT name FROM saved_hotels LIMIT 3"))
    assert not path.exists()


def test_execution_deadline_interrupts(database, monkeypatch):
    monkeypatch.setattr(rag_retrieval, "EXECUTION_SECONDS", -1.0)
    sql = "SELECT COUNT(*) AS total FROM saved_hotels a JOIN saved_hotels b ON 1=1 JOIN saved_hotels c ON 1=1 LIMIT 1"
    with pytest.raises(rag_retrieval.RetrievalError):
        rag_retrieval.retrieve(validate_sql(sql))


def test_payload_bound(database, monkeypatch):
    monkeypatch.setattr(rag_retrieval, "MAX_RESULT_BYTES", 1)
    with pytest.raises(rag_retrieval.RetrievalError, match="payload bound"):
        rag_retrieval.retrieve(validate_sql(SQL))


def test_duplicate_columns_are_rejected(database):
    with pytest.raises(rag_retrieval.RetrievalError, match="distinct"):
        rag_retrieval.retrieve(validate_sql("SELECT name, name FROM saved_hotels LIMIT 1"))


def test_stage2_only_receives_question_instructions_and_limited_rows(database, provider):
    calls = provider()
    result = rag_answer.answer_question("Hotels in 16803 on October 11?", "loaded instructions")
    assert len(calls) == 2
    assert result.retrieved_row_count == 3
    assert result.proposed_sql == SQL
    assert result.executed_sql == SQL
    assert "simulated" in result.answer.lower()
    messages = calls[1]["messages"]
    assert messages[0]["content"].startswith("loaded instructions")
    content = json.loads(messages[1]["content"])
    assert set(content) == {"original_question", "retrieved_records"}
    assert content["retrieved_records"] == result.retrieved_rows
    assert "rag-fake-secret" not in result.model_dump_json()


def test_empty_result_is_grounded_even_if_model_invents(database, provider):
    calls = provider(sql=SQL.replace("16803", "99999"), answer="Fictional Hotel has 100 rooms for $99.")
    result = rag_answer.answer_question("Hotels in 99999?", "instructions")
    assert len(calls) == 2
    assert json.loads(calls[1]["messages"][1]["content"])["retrieved_records"] == []
    assert result.retrieved_row_count == 0 and result.retrieved_rows == []
    assert "No matching" in result.answer
    assert "simulated classroom" in result.answer
    assert "Fictional" not in result.answer


def test_simulation_label_added_if_provider_omits_it(database, provider):
    provider(answer="Hotel 0 costs $100.00.")
    assert "simulated classroom data" in rag_answer.answer_question("Hotels?", "instructions").answer


def test_stage2_failure_is_safe_and_not_retried(database, provider):
    calls = provider(failure_stage=2)
    with pytest.raises(openrouter.ChatProviderError):
        rag_answer.answer_question("Hotels?", "instructions")
    assert len(calls) == 2


def test_stage1_write_proposal_stops_before_retrieval_or_stage2(database, provider, monkeypatch):
    calls = provider(sql="DELETE FROM saved_hotels")
    monkeypatch.setattr(rag_retrieval, "retrieve", lambda *args, **kwargs: pytest.fail("No hotel retrieval allowed"))
    with pytest.raises(SqlValidationError):
        rag_answer.answer_question("Hotels?", "instructions")
    assert len(calls) == 1


def test_credential_in_retrieved_rows_never_sent_or_returned(database, provider):
    calls = provider()
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE saved_hotels SET name='rag-fake-secret'")
    with pytest.raises(rag_retrieval.RetrievalError, match="unsafe content"):
        rag_answer.answer_question("Hotels?", "instructions")
    assert len(calls) == 1


def test_endpoint_success_and_stage2_failure(database, provider, monkeypatch):
    monkeypatch.setattr(app.state, "hotel_assistant_prompt", "loaded prompt", raising=False)
    provider()
    response = TestClient(app).post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 200
    assert response.json()["retrieved_row_count"] == 3
    assert "rag-fake-secret" not in response.text
    provider(failure_stage=2)
    response = TestClient(app).post("/api/rag/answer", json={"question": "Hotels?"})
    assert response.status_code == 502
    assert "rag-fake-secret" not in response.text
