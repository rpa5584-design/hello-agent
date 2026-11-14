"""Integrated data/transport tests are offline; each test uses a disposable database."""
import asyncio
from datetime import datetime, timezone, timedelta
import json

import pytest
from fastapi.testclient import TestClient

from app.assignment4 import create_app
from app.assignment4.database import initialize, connect, V2_POLICY
from app.assignment4.dashboard_store import DashboardStore, EMPTY_CONTROL, DEFAULT_USAGE
from app.assignment4.dashboard import Dashboard, ControlError
from app.assignment4.interval_models import normalize_bar
from app.assignment4.yahoo_stream import CaptureResult

AT = datetime(2026, 11, 14, 2, 30, tzinfo=timezone.utc)
BASE = int(AT.timestamp()) - 120


def row(**extra):
    return {"source_time_s": BASE, "open": 100, "high": 110, "low": 90,
            "close": 105, "volume": 0, **extra}


@pytest.fixture
def store(tmp_path):
    path = tmp_path / "dashboard.sqlite3"
    initialize(path)
    return DashboardStore(path)


def record_bars(store, rows, when=AT):
    return store.record_bars("BTC-USD", rows, when, {"interval": "1m"},
                             "fixture_interval", dict(EMPTY_CONTROL), dict(DEFAULT_USAGE))


@pytest.mark.parametrize("volume,quality", [(0, "reported_zero"), (None, "unknown"), (10, "reported"), (0.5, "reported")])
def test_matching_interval_ohlcv_and_volume_quality(store, volume, quality):
    seq, counts = record_bars(store, [row(volume=volume)])
    bar = store.snapshot(seq)["interval_bars"][0]
    assert [bar[k] for k in ("open","high","low","close","volume")] == [100,110,90,105,volume]
    assert bar["volume_quality"] == quality and bar["source_complete"] is None
    assert bar["app_completion"] == "interval_elapsed_by_app"
    assert counts["accepted"] == 1


@pytest.mark.parametrize("bad,reason", [
    (row(source_time_s=BASE+13), "aligned"), (row(open=None), "OHLC"),
    (row(high=99), "range"), (row(low=101), "range"),
    (row(volume=-1), "volume"), (row(volume=True), "volume"),
    (row(source_time_s=100), "plausible"), (None, "object"),
])
def test_bad_intervals_quarantined_with_original_record_and_reason(store, bad, reason):
    seq, counts = record_bars(store, [bad])
    snapshot = store.snapshot(seq)
    assert snapshot["interval_bars"] == []
    assert counts["quarantined"] == 1 and snapshot["quarantine_count"] == 1
    assert reason in snapshot["quarantine"][0]["reason"]
    assert json.loads(snapshot["quarantine"][0]["raw_json"]) == bad


def test_interval_revision_duplicate_and_replay_cutoffs(store):
    a, _ = record_bars(store, [row(volume=None)])
    b, _ = record_bars(store, [row(high=120, volume=20)])
    c, counts = record_bars(store, [row(high=120, volume=20)])
    assert counts["duplicate"] == 1
    assert store.snapshot(a)["interval_bars"][0]["volume"] is None
    revised = store.snapshot(b)["interval_bars"][0]
    assert revised["high"] == 120 and revised["volume"] == 20
    assert revised["revision_no"] == 2 and revised["corrected"] is True
    assert store.snapshot(c)["interval_bars"] == store.snapshot(b)["interval_bars"]
    with connect(store.path, readonly=True) as conn:
        assert conn.execute("SELECT count(*) FROM interval_versions").fetchone()[0] == 2
    assert store.snapshot(0)["interval_bars"] == []


def test_forming_interval_closure_is_app_state_not_source_finality(store):
    current = row(source_time_s=int(AT.timestamp()), volume=0)
    a, _ = record_bars(store, [current])
    assert store.snapshot(a)["interval_bars"][0]["app_completion"] == "forming"
    b, _ = record_bars(store, [current], AT+timedelta(seconds=61))
    assert store.snapshot(b)["interval_bars"][0]["app_completion"] == "interval_elapsed_by_app"
    assert store.snapshot(b)["interval_bars"][0]["source_complete"] is None
    assert store.snapshot(a)["interval_bars"][0]["revision_no"] == 1


def test_stream_and_publication_cursor_roll_back_together(store, monkeypatch):
    def fail(*args):
        raise RuntimeError("event write failed")
    monkeypatch.setattr(store, "_event", fail)
    with pytest.raises(RuntimeError):
        store.record_stream({"id":"BTC-USD","time":BASE*1000,"price":100},
                            AT, dict(EMPTY_CONTROL), dict(DEFAULT_USAGE))
    with connect(store.path, readonly=True) as conn:
        assert conn.execute("SELECT count(*) FROM receipts").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM candles_current").fetchone()[0] == 0


def test_bar_and_event_rollback_together(store, monkeypatch):
    def fail(*args):
        raise RuntimeError("event write failed")
    monkeypatch.setattr(store, "_event", fail)
    with pytest.raises(RuntimeError):
        record_bars(store, [row()])
    with connect(store.path, readonly=True) as conn:
        assert conn.execute("SELECT count(*) FROM interval_receipts").fetchone()[0] == 0


class FakeHistory:
    def fetch(self, symbol):
        return {"rows":[row()], "retrieved_at":AT, "metadata":{"interval":"1m"}, "ledger":[]}
    def close(self):
        pass


class NoData:
    async def capture(self, symbols, sink, seconds):
        return CaptureResult(AT.isoformat(), status="no_data", stop_reason="source_error")


class Denied:
    async def capture(self, symbols, sink, seconds):
        return CaptureResult(AT.isoformat(), status="denied", stop_reason="access_denied_or_rate_limited")


def test_retry_limit_unavailable_and_persistent_budget(store):
    async def scenario():
        d=Dashboard(store.path, adapter_factory=NoData, history_fetcher=FakeHistory(), backoff=0)
        await d.start(["BTC-USD"], 1)
        await d.task
        assert d.control["feed"] == "unavailable"
        assert d.usage["attempts"] == 2 and d.usage["reconnects"] == 1
        restarted=Dashboard(store.path, adapter_factory=NoData, history_fetcher=FakeHistory())
        with pytest.raises(ControlError, match="budget"):
            await restarted.start(["BTC-USD"], 1)
    asyncio.run(scenario())


def test_denied_feed_stops_without_retry(store):
    async def scenario():
        d=Dashboard(store.path, adapter_factory=Denied, history_fetcher=FakeHistory())
        await d.start(["BTC-USD"],1)
        await d.task
        assert d.usage["blocked"] is True and d.usage["attempts"] == 1
        assert d.usage["reconnects"] == 0 and d.control["feed"] == "unavailable"
    asyncio.run(scenario())


def test_snapshot_registration_and_commit_before_queue_publish(store, monkeypatch):
    async def scenario():
        d=Dashboard(store.path, history_fetcher=FakeHistory(), now=lambda: AT)
        queue, initial=await d.subscribe()
        initial_cursor=initial["cursor"]
        d._receive({"received_at":AT.isoformat(),"raw_decoded":{
            "id":"BTC-USD","time":BASE*1000,"price":100}})
        assert await queue.get() == "update"
        after=await d.snapshot()
        assert after["cursor"] > initial_cursor
        assert after["payload"]["quotes"]["BTC-USD"]["price"] == 100
        assert d.store.snapshot()["stream_cutoff"] == 1
        # Source time is two minutes old despite just-received network message.
        assert after["payload"]["quotes"]["BTC-USD"]["freshness"] == "stale"
        assert after["payload"]["effective_feed"] == "stale"
        await d.unsubscribe(queue)
        assert not d.clients
    asyncio.run(scenario())


def test_simulation_uses_no_source_and_preserves_data(store):
    async def scenario():
        def forbidden():
            raise AssertionError("source accessed")
        d=Dashboard(store.path, adapter_factory=forbidden, history_fetcher=FakeHistory())
        await d.simulate_unavailable()
        state=(await d.snapshot())["payload"]
        assert state["control"]["simulated"] is True
        assert state["effective_feed"] == "unavailable" and state["usage"]["attempts"] == 0
    asyncio.run(scenario())


def test_three_explicit_fetch_limit_and_replay_freezes_versions(store):
    async def scenario():
        d=Dashboard(store.path, history_fetcher=FakeHistory())
        await d.fetch_history("BTC-USD")
        first=(await d.snapshot())["cursor"]
        await d.fetch_history("BTC-USD")
        await d.fetch_history("BTC-USD")
        with pytest.raises(ControlError, match="budget"):
            await d.fetch_history("BTC-USD")
        replay=await d.snapshot("replay",first)
        assert replay["mode"] == "replay"
        assert replay["payload"]["usage"]["history_fetches"] == 1
        assert replay["payload"]["interval_bars"][0]["revision_no"] == 1
    asyncio.run(scenario())


def test_websocket_snapshot_replay_and_reconnect_no_automatic_source(tmp_path):
    def forbidden():
        raise AssertionError("source accessed from startup or socket")
    path=tmp_path/"socket.sqlite3"
    with TestClient(create_app(path, adapter_factory=forbidden, history_fetcher=FakeHistory())) as client:
        with client.websocket_connect("/api/assignment4/ws") as ws:
            ws.send_json({"type":"hello","mode":"live","request_id":1})
            initial=ws.receive_json()
            assert initial["mode"] == "live"
            assert initial["payload"]["usage"]["attempts"] == 0
            ws.send_json({"type":"replay","cursor":0,"request_id":2})
            replay=ws.receive_json()
            assert replay["mode"] == "replay" and replay["payload"]["interval_bars"] == []
        with client.websocket_connect("/api/assignment4/ws") as ws:
            ws.send_json({"type":"hello","mode":"live"})
            again=ws.receive_json()
            assert again["cursor"] == initial["cursor"]
            assert again["payload"]["usage"]["attempts"] == 0
        assert client.post("/api/assignment4/demo/unavailable").status_code == 200
        assert client.get("/api/assignment4/dashboard").json()["payload"]["control"]["simulated"]


def test_v2_additive_migration_preserves_receipts(store):
    with connect(store.path) as c:
        c.execute("UPDATE metadata SET policy=?", (V2_POLICY,))
        c.execute("PRAGMA user_version=2")
    initialize(store.path)
    initialize(store.path)
    with connect(store.path,readonly=True) as c:
        assert c.execute("PRAGMA user_version").fetchone()[0] == 3
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []




def test_stop_cancels_owned_source_and_retains_records(store):
    closed = []
    class WaitingSource:
        async def capture(self, symbols, sink, seconds):
            try:
                sink({"received_at":AT.isoformat(),"raw_decoded":{
                    "id":"BTC-USD","time":(int(AT.timestamp())-1)*1000,"price":123}})
                await asyncio.Event().wait()
            finally:
                closed.append(True)
    async def scenario():
        d=Dashboard(store.path, adapter_factory=WaitingSource, history_fetcher=FakeHistory(), now=lambda:AT)
        await d.start(["BTC-USD"],1)
        await asyncio.sleep(0)
        await d.stop()
        assert closed and d.task.done() and d.control["feed"] == "stopped"
        assert d.store.snapshot()["quotes"]["BTC-USD"]["price"] == 123
    asyncio.run(scenario())


def test_slow_subscriber_resync_keeps_durable_receipts(store):
    async def scenario():
        d=Dashboard(store.path, history_fetcher=FakeHistory(), now=lambda:AT)
        queue, _ = await d.subscribe()
        for i in range(33):
            d._receive({"received_at":AT.isoformat(),"raw_decoded":{
                "id":"BTC-USD","time":(BASE+i)*1000,"price":100+i}})
        assert await queue.get() == "resync"
        assert d.store.snapshot()["stream_cutoff"] == 33
        with connect(store.path,readonly=True) as c:
            assert c.execute("SELECT count(*) FROM receipts").fetchone()[0] == 33
    asyncio.run(scenario())


def test_fixture_quotes_not_exposed_as_actual_yahoo(store):
    store.market.ingest({"id":"BTC-USD","time":BASE*1000,"price":123},
                        provenance="fixture",received_at=AT)
    store.control(dict(EMPTY_CONTROL),dict(DEFAULT_USAGE),at=AT)
    assert store.snapshot()["quotes"] == {}


def test_empty_fetch_retrieval_time_has_its_own_receipt_cutoff(store):
    a, _ = record_bars(store,[row()],AT)
    b, _ = record_bars(store,[],AT+timedelta(seconds=10))
    assert store.snapshot(a)["last_interval_retrieval"] == AT.isoformat()
    assert store.snapshot(b)["last_interval_retrieval"] == (AT+timedelta(seconds=10)).isoformat()
    assert store.snapshot(a)["interval_bars"] == store.snapshot(b)["interval_bars"]



def test_history_denial_blocks_all_future_upstream_requests(store):
    from app.assignment4.history_source import HistoryUnavailable
    class BlockedHistory(FakeHistory):
        def fetch(self,symbol):
            raise HistoryUnavailable("access denied HTTP 403",
                                     [{"http_status":403,"chart":True}],True)
    async def scenario():
        d=Dashboard(store.path,history_fetcher=BlockedHistory())
        with pytest.raises(ControlError,match="403"):
            await d.fetch_history("BTC-USD")
        assert d.control["feed"] == "unavailable"
        assert d.usage["blocked"] is True
        with pytest.raises(ControlError):
            await d.start(["BTC-USD"],1)
        with pytest.raises(ControlError):
            await d.fetch_history("BTC-USD")
        assert d.usage["attempts"] == 0
        assert d.usage["history_fetches"] == 1
    asyncio.run(scenario())
