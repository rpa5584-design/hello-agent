"""Offline scheduling/transport integration; no Yahoo requests."""
import asyncio
from datetime import datetime, timezone
from threading import Event
from time import monotonic

import pytest

from app.assignment4.dashboard import Dashboard, ControlError
from app.assignment4.dashboard_store import DashboardStore
from app.assignment4.database import initialize
from app.assignment4.history_source import YahooHistoryFetcher, HistoryUnavailable
from app.assignment4.yahoo_stream import CaptureResult

AT = datetime(2026, 11, 14, 2, 30, tzinfo=timezone.utc)


class History:
    def __init__(self, failures=0):
        self.calls = 0
        self.failures = failures

    def fetch(self, symbol):
        self.calls += 1
        if self.calls <= self.failures:
            raise HistoryUnavailable("offline transient failure", [{"http_status": 503}])
        return {"rows": [{"source_time_s": int(AT.timestamp()) - 120,
                          "open": 100, "high": 110 + self.calls, "low": 90,
                          "close": 105, "volume": None if self.calls == 1 else self.calls}],
                "retrieved_at": AT, "metadata": {"interval": "1m"}, "ledger": []}

    def close(self):
        pass


@pytest.fixture
def path(tmp_path):
    path = tmp_path / "refresh.sqlite3"
    initialize(path)
    return path


def test_refresh_immediate_cadence_matching_revisions_commit_and_replay(path):
    async def scenario():
        waits, cursors = [], []
        async def wait(delay):
            waits.append(delay)
        h = History()
        d = Dashboard(path, history_fetcher=h, now=lambda: AT, refresh_wait=wait)
        original = d._publish
        def published():
            # A different read connection can already see the committed OHLCV version.
            snapshot = DashboardStore(path).snapshot()
            if d.control.get("history") == "received":
                assert snapshot["interval_bars"][0]["high"] == 110 + h.calls
                cursors.append(snapshot["cursor"])
            original()
        d._publish = published
        await d._refresh_intervals("BTC-USD", monotonic() + 1000)
        assert h.calls == 3 and waits == [60, 60]
        assert d.control["interval_refresh"] == "budget_exhausted"
        first = (await d.snapshot("replay", cursors[0]))["payload"]["interval_bars"][0]
        final = (await d.snapshot())["payload"]["interval_bars"][0]
        assert (first["high"], first["volume"]) == (111, None)
        assert (final["high"], final["volume"], final["revision_no"]) == (113, 3, 3)
        assert first["revision_no"] == 1
        assert Dashboard(path, history_fetcher=h).usage["history_fetches"] == 3
    asyncio.run(scenario())


def test_refresh_failure_backoff_bounded_and_ledger_saved(path):
    async def scenario():
        delays = []
        async def wait(delay):
            delays.append(delay)
        d = Dashboard(path, history_fetcher=History(failures=3), refresh_wait=wait)
        await d._refresh_intervals("BTC-USD", monotonic() + 1000)
        assert delays == [60, 120]
        assert d.usage["history_fetches"] == 3
        assert len(d.store.usage()["http_calls"]) == 3
        assert not d.history_busy
    asyncio.run(scenario())


def test_stop_wakes_scheduled_refresh_without_extra_fetch(path):
    async def scenario():
        h = History()
        d = Dashboard(path, history_fetcher=h)
        task = asyncio.create_task(d._refresh_intervals("BTC-USD", monotonic() + 1000))
        while h.calls == 0 or d.history_busy:
            await asyncio.sleep(0.001)
        await d.stop()
        await asyncio.wait_for(task, 1)
        assert h.calls == 1 and d.control["interval_refresh"] == "stopped"
    asyncio.run(scenario())


class CancellableHistory(YahooHistoryFetcher):
    def __init__(self):
        self.entered = Event()
        self.calls = 0
        self.closed = False

    def fetch(self, symbol, *, cancel_event=None, deadline=None):
        self.calls += 1
        self.entered.set()
        assert cancel_event.wait(2), "test Stop failed to signal worker"
        raise HistoryUnavailable("cancelled after in-flight response", [{"http_status": 200}])

    def close(self):
        self.closed = True


def test_no_overlap_stop_drains_worker_and_preserves_http_ledger(path):
    async def scenario():
        h = CancellableHistory()
        d = Dashboard(path, history_fetcher=h)
        task = asyncio.create_task(d._refresh_intervals("BTC-USD", monotonic() + 1000))
        await asyncio.to_thread(h.entered.wait, 1)
        with pytest.raises(ControlError, match="already in progress"):
            await d.fetch_history("BTC-USD")
        await asyncio.wait_for(d.stop(), 1)
        await task
        assert h.calls == 1 and not d.history_busy
        assert d.store.usage()["http_calls"] == [{"http_status": 200}]
        assert d.store.snapshot()["interval_bars"] == []
        await d.close()
        assert h.closed
    asyncio.run(scenario())


def test_session_expiry_owns_and_stops_refresh(path):
    class Source:
        async def capture(self, symbols, sink, seconds):
            await asyncio.sleep(0.02)
            return CaptureResult(AT.isoformat(), status="no_data", stop_reason="time_limit")
    async def scenario():
        h = History()
        d = Dashboard(path, adapter_factory=Source, history_fetcher=h)
        await d.start(["BTC-USD"], 0.03)
        await asyncio.wait_for(d.task, 1)
        assert h.calls == 1 and d.refresh_task.done()
        assert d.session_stop.is_set() and not d.control["running"]
        assert d.control["interval_refresh"] == "stopped"
    asyncio.run(scenario())


def test_refresh_denial_stops_stream_without_deadlock_or_retry(path):
    class Source:
        async def capture(self, symbols, sink, seconds):
            await asyncio.Event().wait()
    class Denied(History):
        def fetch(self, symbol):
            self.calls += 1
            raise HistoryUnavailable("HTTP 429", [{"http_status": 429}], True)
    async def scenario():
        h = Denied()
        d = Dashboard(path, adapter_factory=Source, history_fetcher=h)
        await d.start(["BTC-USD"], 1)
        await asyncio.wait_for(asyncio.gather(d.task, return_exceptions=True), 1)
        assert h.calls == 1 and d.usage["blocked"]
        assert d.control["feed"] == "unavailable" and d.usage["reconnects"] == 0
        assert d.refresh_task.done()
    asyncio.run(scenario())


def test_no_poll_on_startup_or_expired_deadline_or_exhausted_budget(path):
    async def scenario():
        h = History()
        d = Dashboard(path, history_fetcher=h)
        assert d.refresh_task is None and h.calls == 0
        await d._refresh_intervals("BTC-USD", monotonic() - 1)
        assert h.calls == 0
        d.usage["history_fetches"] = 3
        await d._refresh_intervals("BTC-USD", monotonic() + 10)
        assert h.calls == 0 and d.control["interval_refresh"] == "budget_exhausted"
    asyncio.run(scenario())


@pytest.mark.parametrize("cancelled,expired", [(True, False), (False, True)])
def test_real_history_guard_prevents_http_after_stop_or_deadline(tmp_path, monkeypatch, cancelled, expired):
    import tempfile
    import yfinance as yf
    from curl_cffi.requests import Session
    import app.assignment4.history_source as module
    original_temp = tempfile.TemporaryDirectory
    monkeypatch.setattr(module.tempfile, "TemporaryDirectory",
                        lambda **kw: original_temp(prefix="guard-", dir=tmp_path))
    monkeypatch.setattr(yf, "set_tz_cache_location", lambda path: None)
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("HTTP must not start")
    monkeypatch.setattr(Session, "request", forbidden)
    class Ticker:
        def __init__(self, symbol, session):
            self.session = session
        def history(self, **kwargs):
            self.session.request("GET", "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD")
    monkeypatch.setattr(yf, "Ticker", Ticker)
    fetcher = YahooHistoryFetcher()
    event = Event()
    if cancelled:
        event.set()
    with pytest.raises(HistoryUnavailable) as error:
        fetcher.fetch("BTC-USD", cancel_event=event,
                      deadline=monotonic() - 1 if expired else monotonic() + 5)
    assert calls == [] and error.value.ledger == []
    fetcher.close()


def test_unexpected_processing_failure_stops_loop_and_clears_fetching_state(path):
    class Broken(History):
        def fetch(self, symbol):
            self.calls += 1
            raise ValueError("fictional malformed response envelope")
    async def scenario():
        h = Broken()
        d = Dashboard(path, history_fetcher=h)
        await d._refresh_intervals("BTC-USD", monotonic() + 10)
        assert h.calls == 1 and not d.history_busy
        assert d.control["history"] == "unavailable"
        assert d.control["interval_refresh"] == "failed"
        assert d.store.snapshot()["interval_bars"] == []
    asyncio.run(scenario())


def test_retrieval_age_is_per_instrument_and_replay_keeps_earlier_empty_fetch(path):
    from datetime import timedelta
    from app.assignment4.dashboard_store import EMPTY_CONTROL, DEFAULT_USAGE
    store = DashboardStore(path)
    first, _ = store.record_bars("BTC-USD", [], AT, {}, "fixture_interval",
                                 dict(EMPTY_CONTROL), dict(DEFAULT_USAGE))
    second, _ = store.record_bars("ETH-USD", [], AT + timedelta(seconds=30), {}, "fixture_interval",
                                  dict(EMPTY_CONTROL), dict(DEFAULT_USAGE))
    assert store.snapshot(first)["interval_retrievals"] == {"BTC-USD": AT.isoformat()}
    assert store.snapshot(second)["interval_retrievals"] == {
        "BTC-USD": AT.isoformat(), "ETH-USD": (AT + timedelta(seconds=30)).isoformat()}
