import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.prompt_loader import load_hotel_assistant_prompt
from app.services import openrouter, rag_stage1
from app.services.sql_validation import MAX_ROWS, SqlValidationError, validate_sql

QUESTION = "Show the three cheapest available saved hotels near ZIP 16803 for October 11, 2026."
VALID = """SELECT h.hotel_id, h.name, n.nightly_rate_cents, n.rooms_available
FROM saved_hotels AS h
JOIN saved_hotel_zips AS z ON h.hotel_id = z.hotel_id
JOIN demo_hotel_nights AS n ON h.hotel_id = n.hotel_id
WHERE z.zip_code = '16803' AND n.stay_date = '2026-10-11' AND n.rooms_available > 0
ORDER BY n.nightly_rate_cents ASC, h.hotel_id LIMIT 3;"""


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "stage1-fake-secret")
    monkeypatch.setenv("OPENROUTER_MODEL", "test/model:free")
    calls = []
    def install(content=VALID, payload=None):
        def handle(request):
            calls.append(request)
            data = payload if payload is not None else {"choices": [{"message": {"role": "assistant", "content": content}}]}
            return httpx.Response(200, json=data)
        monkeypatch.setattr(openrouter.httpx, "HTTPTransport", lambda **kwargs: httpx.MockTransport(handle))
        return calls
    return install


def test_valid_proposal_sends_loaded_prompt_and_question(provider):
    calls = provider()
    prompt = load_hotel_assistant_prompt()
    proposal = rag_stage1.propose_sql(QUESTION, prompt)
    assert proposal.sql.endswith("LIMIT 3")
    assert set(proposal.tables) == {"saved_hotels", "saved_hotel_zips", "demo_hotel_nights"}
    assert len(calls) == 1
    data = json.loads(calls[0].content)
    assert data["model"] == "test/model:free"
    assert data["messages"][0]["role"] == "system"
    assert data["messages"][0]["content"].startswith(prompt)
    assert data["messages"][1] == {"role": "user", "content": QUESTION}


@pytest.mark.parametrize("sql", [
    "SELECT name FROM saved_hotels LIMIT 3; SELECT name FROM saved_hotels LIMIT 1",
    "INSERT INTO saved_hotels VALUES ('x')",
    "UPDATE saved_hotels SET name = 'x'",
    "DELETE FROM saved_hotels",
    "DROP TABLE saved_hotels", "PRAGMA user_version", "ATTACH 'other.db' AS other",
    "DETACH other", "VACUUM", "CREATE TABLE x (y)", "ALTER TABLE saved_hotels ADD x",
    "REPLACE INTO saved_hotels VALUES ('x')",
    "SELECT * FROM hotels LIMIT 3", "SELECT * FROM trips LIMIT 3",
    "SELECT * FROM users LIMIT 3", "SELECT * FROM bookings LIMIT 3",
    "SELECT * FROM sqlite_master LIMIT 3",
    "SELECT name FROM saved_hotels", "SELECT name FROM saved_hotels LIMIT -1",
    "SELECT name FROM saved_hotels LIMIT 0", "SELECT name FROM saved_hotels LIMIT (1+2)",
    "SELECT name FROM saved_hotels LIMIT 2 OFFSET 0",
    "SELECT name FROM saved_hotels LIMIT 1, 3",
    "SELECT load_extension('x') FROM saved_hotels LIMIT 3",
    "SELECT name FROM saved_hotels UNION SELECT name FROM saved_hotels LIMIT 3",
    "SELECT (SELECT * FROM users) FROM saved_hotels LIMIT 3",
    "SELECT * FROM main.saved_hotels LIMIT 3",
    "SELECT * FROM pragma_table_info('users') LIMIT 3",
    "SELECT name FROM saved_hotels -- comment\n LIMIT 3",
    "SELECT /* comment */ name FROM saved_hotels LIMIT 3",
    "SELECT name FROM saved_hotels JOIN users ON 1=1 LIMIT 3",
    "SELECT name FROM saved_hotels, users LIMIT 3",
    'SELECT * FROM "users" LIMIT 3',
    "SELECT secret FROM saved_hotels LIMIT 3",
    "SELECT name saved_hotels LIMIT 3", "SELECT FROM saved_hotels LIMIT 3",
    "```sql\nSELECT name FROM saved_hotels LIMIT 3\n```",
    "I cannot answer that question.",
])
def test_unsafe_or_unsupported_llm_proposal_rejected(provider, sql):
    provider(sql)
    with pytest.raises(SqlValidationError):
        rag_stage1.propose_sql(QUESTION, "test prompt")


def test_large_limit_is_clamped_and_strings_are_not_sql_keywords():
    proposal = validate_sql("SELECT name FROM saved_hotels WHERE name = 'DROP; it''s text' LIMIT 999;")
    assert proposal.sql.endswith(f"LIMIT {MAX_ROWS}")
    assert proposal.tables == ("saved_hotels",)


def test_grouped_multinight_and_quoted_identifiers_supported():
    sql = '''SELECT h.hotel_id, SUM(n.nightly_rate_cents) AS total_cents
FROM "saved_hotels" h JOIN demo_hotel_nights n ON h.hotel_id = n.hotel_id
WHERE n.stay_date >= '2026-10-10' AND n.stay_date < '2026-10-12' AND n.rooms_available > 0
GROUP BY h.hotel_id HAVING COUNT(DISTINCT n.stay_date) = 2 ORDER BY total_cents LIMIT 5'''
    assert validate_sql(sql).sql.endswith("LIMIT 5")


@pytest.mark.parametrize("payload", [{}, {"choices": []}, {"choices": [{"message": {"role": "assistant", "content": None}}]}])
def test_malformed_model_response(provider, payload):
    provider(payload=payload)
    with pytest.raises(openrouter.ChatProviderError):
        rag_stage1.propose_sql(QUESTION, "test prompt")


def test_endpoint_uses_app_state_and_never_connects_sqlite(provider, monkeypatch):
    import sqlite3
    def forbidden(*args, **kwargs):
        pytest.fail("Stage 1 must not connect to SQLite")
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    monkeypatch.setattr(app.state, "hotel_assistant_prompt", "loaded system prompt", raising=False)
    calls = provider()
    response = TestClient(app).post("/api/rag/propose-sql", json={"question": QUESTION})
    assert response.status_code == 200
    assert response.json()["sql"].endswith("LIMIT 3")
    assert "stage1-fake-secret" not in response.text
    assert json.loads(calls[0].content)["messages"][0]["content"].startswith("loaded system prompt")
    provider("DELETE FROM saved_hotels")
    assert TestClient(app).post("/api/rag/propose-sql", json={"question": QUESTION}).status_code == 422


def test_missing_prompt_never_calls_model(provider, monkeypatch):
    monkeypatch.setattr(app.state, "hotel_assistant_prompt", None, raising=False)
    calls = provider()
    assert TestClient(app).post("/api/rag/propose-sql", json={"question": QUESTION}).status_code == 503
    assert calls == []
