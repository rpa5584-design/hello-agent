"""Fictional identity/migration policies plus offline inspection of actual saved evidence."""
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from app.assignment4.controller import MarketStore
from app.assignment4.database import LEGACY_POLICY, POLICY, connect, initialize
from app.assignment4.models import normalize
from app.assignment4.probe_history import ProbeStopped, RequestBudget

NOW = datetime(2026, 11, 13, 22, tzinfo=timezone.utc)
BASE = int(NOW.timestamp() * 1000) - 60000


def ingest(store, price, **extra):
    return store.ingest({"id": "BTC-USD", "time": str(BASE), "price": price, **extra},
                        provenance="yahoo_stream", received_at=NOW)


def test_ambiguous_same_time_prices_never_replace_observed_extrema(tmp_path):
    path = tmp_path / "identity.sqlite3"
    initialize(path)
    store = MarketStore(path)
    states = []
    ids = []
    for price in (100, 150, 90, 100):
        result = ingest(store, price)
        assert result["kind"] == "new"
        ids.append(result["observation_id"])
        states.append(store.snapshot()["candles"])
    assert len(set(ids)) == 4
    candle = states[-1][0]
    assert (candle["open"], candle["high"], candle["low"], candle["close"]) == (100, 150, 90, 100)
    assert candle["observation_count"] == 4
    for i, state in enumerate(states, 1):
        assert store.replay(through=i)["candles"] == state
    assert all(store.versions(i)[0]["supersedes_version_id"] is None for i in ids)
    assert all(store.versions(i)[0]["ambiguous_same_time"] == 1 for i in ids[1:])


def test_exact_current_repeat_has_receipt_but_no_extra_contribution(tmp_path):
    path = tmp_path / "repeat.sqlite3"
    initialize(path)
    store = MarketStore(path)
    a = ingest(store, 100)
    b = ingest(store, 150)
    c = ingest(store, 150)
    d = ingest(store, 100)
    assert c["kind"] == "duplicate" and c["version_id"] == b["version_id"]
    assert d["kind"] == "new" and d["observation_id"] != a["observation_id"]
    assert len(store.receipts()) == 4
    assert store.snapshot()["candles"][0]["observation_count"] == 3


def test_crypto_strings_and_missing_volume_normalize_without_zero():
    o = normalize({"id": "ETH-USD", "time": str(BASE), "price": 100,
                   "quote_type": 41, "market_hours": 1, "vol_24hr": "10000"},
                  "yahoo_stream", NOW)
    assert o.source_time_ms == BASE and o.day_volume is None and o.last_size is None
    assert o.vol_24hr == 10000


def legacy_database(path, yahoo=False):
    initialize(path)
    store = MarketStore(path)
    store.ingest({"id": "AAPL", "time": BASE, "price": 100},
                 provenance="fixture", received_at=NOW)
    with connect(path) as conn:
        conn.execute("DROP INDEX observations_base_slot")
        conn.execute("ALTER TABLE observations DROP COLUMN base_slot_key")
        conn.execute("UPDATE metadata SET policy=?", (LEGACY_POLICY,))
        conn.execute("PRAGMA user_version=1")
        if yahoo:
            conn.execute("UPDATE receipts SET provenance='yahoo_stream'")
    return store


def test_v1_fixture_migration_preserves_history_and_is_idempotent(tmp_path):
    store = legacy_database(tmp_path / "legacy.sqlite3")
    before, receipts = store.snapshot(), store.receipts()
    initialize(store.path)
    initialize(store.path)
    assert store.snapshot() == before and store.receipts() == receipts
    assert store.replay()["candles"] == before["candles"]
    with connect(store.path, readonly=True) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
        assert conn.execute("SELECT policy FROM metadata").fetchone()[0] == POLICY
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_legacy_yahoo_identity_requires_review_not_silent_rewrite(tmp_path):
    store = legacy_database(tmp_path / "legacy-yahoo.sqlite3", yahoo=True)
    before = store.path.read_bytes()
    with pytest.raises(RuntimeError, match="explicit review"):
        initialize(store.path)
    assert store.path.read_bytes() == before


def test_history_probe_caps_chart_requests_and_stops_denial():
    budget = RequestBudget()
    for _ in range(2):
        row = budget.before("https://query2.finance.yahoo.com/v8/finance/chart/BTC-USD")
        budget.after(row, 200)
    with pytest.raises(ProbeStopped, match="two chart"):
        budget.before("https://query2.finance.yahoo.com/v8/finance/chart/BTC-USD")
    assert budget.chart_requests == 2
    with pytest.raises(ProbeStopped, match="403"):
        budget.after(row, 403)


def test_actual_evidence_offline_normalization_and_replay(tmp_path):
    # Recorded source data; no claim of a new live request by this test.
    evidence = Path(__file__).resolve().parents[2] / "docs/assignment4/part4.1/evidence/yahoo-stream-20261113-01.jsonl"
    messages = [json.loads(line) for line in evidence.read_text().splitlines()]
    messages = [r for r in messages if r["kind"] == "source_message"]
    assert len(messages) == 6
    path = tmp_path / "recorded-source.sqlite3"
    initialize(path)
    store = MarketStore(path)
    for event in messages:
        result = store.ingest(event["raw_decoded"], provenance="yahoo_stream",
                              received_at=datetime.fromisoformat(event["received_at"]))
        assert result["kind"] == "new"
        assert store.replay()["candles"] == store.snapshot()["candles"]
    assert len(store.snapshot()["candles"]) == 4
    assert all(c["volume"] is None for c in store.snapshot()["candles"])
