"""Fictional market fixtures only. No source adapter, network or working databases."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from app.assignment4 import create_app
from app.assignment4 import controller
from app.assignment4.controller import MarketStore
from app.assignment4.database import POLICY, connect, initialize
from app.assignment4.models import normalize
from app.assignment4.services import MarketService

# Whole UTC minute, intentionally fictional prices/volumes.
BASE = 1794571200000
RECEIVED = datetime.fromtimestamp((BASE + 600_000) / 1000, timezone.utc)


def quote(offset=0, price=100, **extras):
    return {"id": "AAPL", "time": BASE + offset, "price": price, **extras}


@pytest.fixture
def store(tmp_path):
    path = tmp_path / "market.sqlite3"
    initialize(path)
    return MarketStore(path)


def record(store, offset=0, price=100, **extras):
    return store.ingest(quote(offset, price, **extras),
                        provenance="fixture", received_at=RECEIVED)


def first(store):
    return store.snapshot()["candles"][0]


def counts(store):
    with connect(store.path, readonly=True) as connection:
        return tuple(connection.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
                     for name in ("receipts", "observations", "observation_versions",
                                  "projection_events"))


def test_duplicate_preserves_receipts_without_double_counting(store):
    a = record(store, day_volume=100)
    before = store.snapshot()["candles"]
    b = record(store, day_volume=100)
    assert (a["kind"], b["kind"]) == ("new", "duplicate")
    assert b["version_id"] == a["version_id"]
    assert counts(store) == (2, 1, 1, 1)
    assert store.snapshot()["candles"] == before
    receipts = store.receipts()
    assert [r["receipt_seq"] for r in receipts] == [1, 2]
    assert receipts[1]["received_at"] == RECEIVED.isoformat()
    assert json.loads(receipts[0]["raw_payload_json"])["time"] == BASE


def test_known_numeric_strings_normalize_without_losing_raw(store):
    record(store, day_volume=100)
    result = store.ingest({"id": "AAPL", "time": str(BASE), "price": 100.0,
                           "day_volume": "100"}, provenance="fixture", received_at=RECEIVED)
    assert result["kind"] == "duplicate"
    assert json.loads(store.receipts()[1]["raw_payload_json"])["day_volume"] == "100"


def test_distinct_time_unchanged_price_and_bucket_boundaries(store):
    record(store)
    record(store, 10_000)
    record(store, 60_000, 101)
    candles = store.snapshot()["candles"]
    assert len(candles) == 2
    assert candles[0]["observation_count"] == 2
    assert candles[1]["bucket_start_ms"] == BASE + 60_000
    assert counts(store)[:3] == (3, 3, 3)


def test_revision_replaces_prior_contribution_and_retains_history(store):
    record(store, 0, 100)
    a = record(store, 10_000, 150, day_volume=130)
    b = record(store, 10_000, 90, day_volume=120)
    assert b["kind"] == "revision"
    assert b["observation_id"] == a["observation_id"]
    c = first(store)
    assert (c["open"], c["high"], c["low"], c["close"], c["observation_count"]) == (
        100, 100, 90, 90, 2)
    versions = store.versions(a["observation_id"])
    assert [v["revision_no"] for v in versions] == [1, 2]
    assert versions[1]["supersedes_version_id"] == versions[0]["version_id"]
    assert versions[1]["ambiguous_same_time"] == 1
    assert json.loads(versions[0]["normalized_json"])["day_volume"] == 130


def test_a_b_a_is_three_versions_not_historical_hash_dedup(store):
    a = record(store, price=100)
    record(store, price=200)
    record(store, price=100)
    assert len(store.versions(a["observation_id"])) == 3
    assert first(store)["high"] == 100


def test_same_slot_absence_null_and_extra_fields_are_revisions(store):
    a = record(store)
    record(store, day_volume=None)
    record(store, day_volume=None, provider_extra="retained")
    assert len(store.versions(a["observation_id"])) == 3


def test_out_of_order_ohlc_uses_source_time_not_receipt_order(store):
    record(store, 40_000, 140)
    record(store, 10_000, 100)
    record(store, 30_000, 90)
    c = first(store)
    assert (c["open"], c["high"], c["low"], c["close"]) == (100, 140, 90, 140)
    assert [json.loads(r["raw_payload_json"])["time"] for r in store.receipts()] == [
        BASE + 40_000, BASE + 10_000, BASE + 30_000]


def test_source_time_tie_uses_first_receipt_stable_across_revision(store):
    record(store, price=100, exchange="ONE")
    record(store, price=200, exchange="TWO")
    record(store, price=50, exchange="ONE")
    c = first(store)
    assert (c["open"], c["close"], c["observation_count"]) == (50, 200, 2)
    assert store.replay()["candles"] == store.snapshot()["candles"]


def test_forming_closure_and_late_correction(store):
    record(store)
    assert first(store)["app_completion"] == "forming"
    record(store, 69_999, 110)
    assert first(store)["app_completion"] == "forming"
    record(store, 70_000, 120)
    closed = first(store)
    assert closed["app_completion"] == "interval_closed_by_app"
    assert closed["source_complete"] is None
    assert closed["late_corrected"] is False
    record(store, 10_000, 80)
    corrected = first(store)
    assert corrected["low"] == 80
    assert corrected["late_corrected"] is True
    assert corrected["app_completion"] == "interval_closed_by_app"
    assert corrected["projection_revision"] == closed["projection_revision"] + 1
    assert corrected["last_corrected_at"] == RECEIVED.isoformat()
    record(store, 10_000, 90)
    assert first(store)["low"] == 90
    assert first(store)["late_corrected"] is True


@pytest.mark.parametrize("volumes", [
    [None, None, None], [100, 130, 150], [100, 100, 100],
    [100, 10, 30], [None, 100, None], [0, 0, 0],
])
def test_volume_is_never_sum_or_unknown_zero(store, volumes):
    for n, volume in enumerate(volumes):
        extras = {} if volume is None else {"day_volume": volume}
        record(store, n * 10_000, 100 + n, **extras)
    c = first(store)
    assert c["volume"] is None
    assert c["volume_coverage"] == "unknown"
    assert c["volume_kind"] == "unavailable_unverified_source_semantics"
    assert [json.loads(v["normalized_json"])["day_volume"]
            for r in store.receipts() for v in
            store.versions(record_id(store, r["version_id"]))] == volumes


def record_id(store, version_id):
    with connect(store.path, readonly=True) as connection:
        return connection.execute(
            "SELECT observation_id FROM observation_versions WHERE version_id=?",
            (version_id,)).fetchone()[0]


def test_late_counter_snapshot_and_revision_still_unavailable(store):
    record(store, 0, day_volume=100, last_size=25, vol_24hr=1000)
    record(store, 40_000, day_volume=130, last_size=25, vol_24hr=1200)
    record(store, 20_000, day_volume=120, last_size=25, vol_24hr=1100)
    record(store, 20_000, day_volume=110, last_size=30, vol_24hr=1050)
    assert first(store)["volume"] is None
    assert first(store)["observation_count"] == 3


@pytest.mark.parametrize("changes", [
    {"id": "UNKNOWN"}, {"time": BASE // 1000}, {"time": None},
    {"time": BASE + 606_000}, {"time": True}, {"price": 0},
    {"price": -1}, {"price": "100"}, {"price": True},
    {"day_volume": -1}, {"day_volume": 1.5}, {"day_volume": True},
    {"day_volume": str(2**63)}, {"exchange": ""}, {"quote_type": -1},
])
def test_invalid_observation_quarantined_without_projection(store, changes):
    result = store.ingest({**quote(), **changes}, provenance="fixture", received_at=RECEIVED)
    assert result["kind"] == "quarantined"
    assert result["error"]
    assert counts(store) == (1, 0, 0, 0)
    assert store.snapshot()["candles"] == []
    assert store.replay()["candles"] == []


@pytest.mark.parametrize("price", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_validation_and_non_json_boundary(store, price):
    with pytest.raises(ValueError, match="finite"):
        normalize(quote(price=price), "fixture", RECEIVED)
    with pytest.raises(ValueError):
        store.ingest(quote(price=price), provenance="fixture", received_at=RECEIVED)
    assert counts(store) == (0, 0, 0, 0)


def test_boundary_size_time_and_provenance_validation(store):
    with pytest.raises(ValueError, match="64KiB"):
        record(store, extra="x" * 65536)
    with pytest.raises(ValueError, match="provenance"):
        store.ingest(quote(), provenance="replay", received_at=RECEIVED)
    with pytest.raises(ValueError, match="timezone"):
        store.ingest(quote(), provenance="fixture", received_at=datetime(2026, 1, 1))
    assert counts(store) == (0, 0, 0, 0)


def test_replay_every_receipt_prefix_and_no_writes(store):
    expected = [[]]
    for args in [(0, 100), (20_000, 120), (0, 90), (0, 90), (70_000, 130),
                 (10_000, 95)]:
        record(store, *args)
        expected.append(store.snapshot()["candles"])
    before = store.path.read_bytes()
    for n, candles in enumerate(expected):
        replay = store.replay(through=n)
        assert replay["mode"] == "replay"
        assert replay["as_of_receipt_seq"] == n
        assert replay["candles"] == candles
    assert store.replay(through=999)["as_of_receipt_seq"] == 6
    assert store.path.read_bytes() == before


def test_transaction_rolls_back_receipt_version_and_projection(store, monkeypatch):
    record(store)
    before, before_counts = store.snapshot(), counts(store)
    def broken(*args):
        raise RuntimeError("projection failed")
    monkeypatch.setattr(controller, "project", broken)
    with pytest.raises(RuntimeError, match="projection failed"):
        record(store, 10_000, 120)
    assert store.snapshot() == before
    assert counts(store) == before_counts
    with connect(store.path, readonly=True) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_explicit_initialization_idempotent_and_policy_checked(tmp_path):
    path = tmp_path / "new" / "market.sqlite3"
    store = MarketStore(path)
    with pytest.raises(sqlite3.OperationalError):
        store.snapshot()
    initialize(path)
    record(store)
    before = store.snapshot()
    initialize(path)
    initialize(path)
    assert MarketStore(path).snapshot() == before
    with connect(path) as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
        assert connection.execute("SELECT policy FROM metadata").fetchone()[0] == POLICY
        connection.execute("UPDATE metadata SET policy='unknown'")
    with pytest.raises(RuntimeError, match="policy"):
        initialize(path)


def test_existing_empty_or_foreign_database_not_reseeded(tmp_path):
    empty = tmp_path / "empty.sqlite3"
    empty.touch()
    with pytest.raises(RuntimeError, match="Unsupported"):
        initialize(empty)
    foreign = tmp_path / "foreign.sqlite3"
    with sqlite3.connect(foreign) as connection:
        connection.execute("CREATE TABLE preserve(value TEXT)")
        connection.execute("INSERT INTO preserve VALUES ('untouched')")
    before = foreign.read_bytes()
    with pytest.raises(RuntimeError, match="Unsupported"):
        initialize(foreign)
    assert foreign.read_bytes() == before


def test_new_app_instance_reuses_persisted_state(tmp_path):
    path = tmp_path / "restart.sqlite3"
    with TestClient(create_app(path)) as client:
        service = client.app.state.market_service
        service.record(quote(), provenance="fixture", received_at=RECEIVED)
        before = client.get("/api/assignment4/candles").json()
        # Repeated GET models backend reload/retrieval only, not a browser refresh.
        assert client.get("/api/assignment4/candles").json() == before
    with TestClient(create_app(path)) as client:
        assert client.get("/api/assignment4/candles").json() == before
        assert client.get("/api/assignment4/replay").json()["candles"] == before["candles"]


def test_fresh_python_process_can_read_after_writer_exit(tmp_path):
    path = tmp_path / "process-restart.sqlite3"
    writer = """
from pathlib import Path
from datetime import datetime, timezone
from app.assignment4.database import initialize
from app.assignment4.controller import MarketStore
import json, sys
p=Path(sys.argv[1]); initialize(p)
s=MarketStore(p)
s.ingest({"id":"AAPL","time":1794571200000,"price":123,"day_volume":500},
         provenance="fixture",received_at=datetime.fromtimestamp(1794571800000/1000,timezone.utc))
print(json.dumps(s.snapshot(),sort_keys=True))
"""
    reader = """
from pathlib import Path
from app.assignment4.database import initialize
from app.assignment4.controller import MarketStore
import json, sys
p=Path(sys.argv[1]); initialize(p)
print(json.dumps(MarketStore(p).snapshot(),sort_keys=True))
"""
    a = subprocess.run([sys.executable, "-c", writer, str(path)],
                       capture_output=True, text=True, check=True, timeout=20)
    b = subprocess.run([sys.executable, "-c", reader, str(path)],
                       capture_output=True, text=True, check=True, timeout=20)
    result = json.loads(a.stdout)
    assert result["as_of_receipt_seq"] == 1
    assert result["candles"][0]["close"] == 123
    assert json.loads(b.stdout) == result


def test_factory_isolation_read_only_routes_and_bounds(tmp_path, monkeypatch):
    from app import main
    def forbidden(*args, **kwargs):
        raise AssertionError("earlier startup/provider called")
    monkeypatch.setattr(main, "initialize_database", forbidden)
    monkeypatch.setattr(main, "load_hotel_assistant_prompt", forbidden)
    monkeypatch.setattr("app.assignment3.database.initialize", forbidden)
    path = tmp_path / "factory.sqlite3"
    app = main.create_assignment4_app(path)
    with TestClient(app) as client:
        assert client.get("/api/assignment4/health").json()["feed_status"] == "stopped"
        assert client.get("/api/health").status_code == 404
        assert client.get("/api/assignment3/health").status_code == 404
        assert client.post("/api/assignment4/receipts", json=quote()).status_code == 405
        assert client.get("/api/assignment4/receipts?after=-1").status_code == 422
        assert client.get("/api/assignment4/receipts?limit=501").status_code == 422
        assert client.get("/api/assignment4/replay?through=-1").status_code == 422
        assert not hasattr(app.state, "hotel_assistant_prompt")
    assert path.exists()
    assert main.app.title == "RoomTour API"


def test_service_pagination_and_fixture_provenance(store):
    service = MarketService(store.path)
    record(store)
    record(store, 10_000)
    assert len(service.receipts(limit=1)) == 1
    assert service.receipts(after=1)[0]["receipt_seq"] == 2
    assert service.snapshot()["mode"] == "stored"
    assert service.snapshot()["streaming_connected"] is False
    assert first(store)["source"] == "fixture"
    assert first(store)["provenance"] == "fixture"
    assert service.replay(1)["candles"][0]["provenance"] == "fixture"
    for kwargs in ({"after": -1}, {"limit": 0}, {"limit": 501}):
        with pytest.raises(ValueError):
            store.receipts(**kwargs)
