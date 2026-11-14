"""Managed source lifecycle and race-safe persisted snapshot publication."""
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from time import monotonic
from uuid import uuid4
from threading import Event as ThreadEvent

from .dashboard_store import DashboardStore, EMPTY_CONTROL
from .history_source import YahooHistoryFetcher, HistoryUnavailable
from .models import normalize
from .yahoo_stream import YahooStreamAdapter


class ControlError(ValueError):
    pass


def ages(state: dict, at: datetime) -> dict:
    for quote in state["quotes"].values():
        quote["source_age_seconds"] = round(at.timestamp() - quote["source_time_ms"] / 1000, 3)
        quote["receipt_age_seconds"] = round(
            (at - datetime.fromisoformat(quote["received_at"])).total_seconds(), 3)
        quote["freshness"] = "clock_skew" if min(quote["source_age_seconds"], quote["receipt_age_seconds"]) < -5 else (
            "stale" if max(quote["source_age_seconds"], quote["receipt_age_seconds"]) > 30 else "fresh")
    retrieval = state["last_interval_retrieval"]
    state["retrieval_age_seconds"] = round(
        (at - datetime.fromisoformat(retrieval)).total_seconds(), 3) if retrieval else None
    return state


class Dashboard:
    def __init__(self, path: Path, adapter_factory=YahooStreamAdapter,
                 history_fetcher=None, now=None, backoff: float = 1,
                 refresh_cadence: float = 60, refresh_wait=None, max_attempts: int = 2, offline: bool = False):
        self.max_attempts = max_attempts
        self.offline = offline
        self.store = DashboardStore(path)
        self.adapter_factory = adapter_factory
        self.history_fetcher = history_fetcher or YahooHistoryFetcher()
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.backoff = backoff
        self.lock = asyncio.Lock()
        self.clients = set()
        self.stream_id = str(uuid4())
        self.usage = self.store.usage()
        previous = self.store.snapshot()
        self.control = {**EMPTY_CONTROL, "offline": offline, "max_attempts": max_attempts}
        if previous["last_interval_retrieval"]:
            self.control["history"] = "stored"
            if previous["control"].get("last_interval_fetch_id"):
                self.control["last_interval_fetch_id"] = previous["control"]["last_interval_fetch_id"]
        self.task = None
        self.history_busy = False
        self.refresh_cadence = refresh_cadence
        self.refresh_wait = refresh_wait or self._wait_refresh
        self.session_stop = asyncio.Event()
        self.history_cancel = ThreadEvent()
        self.history_done = asyncio.Event()
        self.history_done.set()
        self.refresh_task = None
        self.session_deadline = None
        # Records a new local server lifecycle, never reconnects Yahoo.
        self.store.control(self.control, self.usage, kind="server_started", at=self.now())

    def _state(self, mode: str = "live", through: int | None = None) -> dict:
        state = self.store.snapshot(through if mode == "replay" else None)
        at = datetime.fromisoformat(state["recorded_at"]) if mode == "replay" and state["recorded_at"] else self.now()
        state = ages(state, at)
        state["mode"], state["server_time"] = mode, self.now().isoformat()
        state["virtual_time"] = at.isoformat() if mode == "replay" else None
        if mode == "live":
            state["control"] = dict(self.control)
            state["usage"] = json.loads(json.dumps(self.usage))
        for name in ("stream_seconds", "stream_reserved_seconds"):
            state["usage"][name] = round(state["usage"].get(name, 0), 3)
        state["effective_feed"] = state["control"]["feed"]
        if state["effective_feed"] in ("receiving", "waiting"):
            selected = [q for q in state["quotes"].values() if not state["usage"]["instruments"] or q["symbol"] in state["usage"]["instruments"]]
            if selected and all(q["freshness"] != "fresh" for q in selected):
                state["effective_feed"] = "stale"
        if state["effective_feed"] == "waiting" and state["control"].get("started_at"):
            waiting_age = (at - datetime.fromisoformat(state["control"]["started_at"])).total_seconds()
            if waiting_age >= 30:
                state["effective_feed"] = "unavailable" if waiting_age >= 90 else "stale"
        return state

    def envelope(self, mode="live", through=None, message_type="snapshot") -> dict:
        state = self._state(mode, through)
        return {"protocol_version": 1, "stream_id": self.stream_id,
                "message_type": message_type, "mode": mode, "cursor": state["cursor"],
                "payload": state}

    def _publish(self) -> None:
        # Called only AFTER the store transaction has returned/committed.
        for queue in tuple(self.clients):
            if queue.full():
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait("resync")
            else:
                queue.put_nowait("update")

    async def subscribe(self) -> tuple[asyncio.Queue, dict]:
        async with self.lock:
            queue = asyncio.Queue(maxsize=32)
            self.clients.add(queue)
            snapshot = self.envelope()
            return queue, snapshot

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        async with self.lock:
            self.clients.discard(queue)

    async def snapshot(self, mode="live", through=None) -> dict:
        async with self.lock:
            return self.envelope(mode, through)

    async def status(self, **values) -> None:
        async with self.lock:
            self.control.update(values)
            self.store.control(self.control, self.usage, at=self.now())
            self._publish()

    def _allow_symbols(self, symbols: list[str]) -> None:
        if not 1 <= len(symbols) <= 2 or len(set(symbols)) != len(symbols) or any(s not in ("BTC-USD", "ETH-USD") for s in symbols):
            raise ControlError("Choose one or two supported crypto instruments")
        union = set(self.usage["instruments"]) | set(symbols)
        if len(union) > 2:
            raise ControlError("Two-instrument development budget exhausted")
        self.usage["instruments"] = sorted(union)

    async def start(self, symbols: list[str], seconds: float) -> None:
        async with self.lock:
            if self.offline:
                raise ControlError("Offline recorded-data mode: upstream access disabled")
            if self.task and not self.task.done():
                raise ControlError("Live stream already running")
            if self.history_busy:
                raise ControlError("Wait for the current interval fetch before starting")
            if not 0 < seconds <= 120:
                raise ControlError("Stream duration must be 0-120 seconds")
            if self.usage["blocked"] or self.usage["attempts"] >= self.max_attempts:
                raise ControlError("Connection budget exhausted or access denied; no automatic reset")
            if self.usage["stream_reserved_seconds"] + seconds + 3 > 180:
                raise ControlError("180-second development budget exhausted")
            self._allow_symbols(symbols)
            self.usage["stream_reserved_seconds"] += seconds + 3
            self.session_stop = asyncio.Event()
            self.session_deadline = monotonic() + seconds
            self.control.update(interval_refresh="scheduled", refresh_cadence_seconds=self.refresh_cadence,
                                refresh_symbol=symbols[0])
            self.control.update(feed="waiting", reason="Waiting for actual persisted observations",
                                simulated=False, running=True, started_at=self.now().isoformat())
            self.store.control(self.control, self.usage, kind="start_requested", at=self.now())
            self._publish()
            self.task = asyncio.create_task(self._run(symbols, seconds))

    async def _run(self, symbols: list[str], seconds: float) -> None:
        start = monotonic()
        deadline = self.session_deadline or start + seconds
        self.refresh_task = asyncio.create_task(self._refresh_intervals(symbols[0], deadline))
        try:
            while monotonic() < deadline:
                async with self.lock:
                    if self.usage["attempts"] >= self.max_attempts:
                        break
                    if self.usage["attempts"]:
                        self.usage["reconnects"] += 1
                    self.usage["attempts"] += 1
                    self.store.control(self.control, self.usage, kind="connection_attempt", at=self.now())
                    self._publish()
                result = await self.adapter_factory().capture(
                    symbols, self._receive, seconds=min(110, max(0.001, deadline - monotonic())))
                if result.status == "denied":
                    self.usage["blocked"] = True
                    await self.status(feed="unavailable", reason="Access denied/rate limited; stopped",
                                      running=False)
                    return
                if result.status == "storage_error":
                    await self.status(feed="storage_error", reason="Persistence failed; not publishing quotes")
                    return
                if result.stop_reason == "time_limit":
                    if monotonic() < deadline - 0.05 and result.status == "captured":
                        # Longer requested session can use remaining time only via permitted reconnect.
                        pass
                    else:
                        await self.status(feed="stopped" if result.status == "captured" else "unavailable",
                                          reason="Session limit reached" if result.status == "captured" else
                                          "No valid observations arrived during bounded session")
                        return
                if self.usage["attempts"] >= self.max_attempts or monotonic() + self.backoff >= deadline:
                    await self.status(feed="unavailable", reason="Bounded source retry exhausted")
                    return
                await self.status(feed="retrying", reason="Source unavailable; one bounded reconnect")
                await asyncio.sleep(self.backoff)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self.status(feed="unavailable", reason=f"Source stopped: {type(exc).__name__}")
        finally:
            self.session_stop.set()
            self.history_cancel.set()
            if self.refresh_task:
                await asyncio.gather(self.refresh_task, return_exceptions=True)
            async with self.lock:
                self.control["interval_refresh"] = "stopped"
                self.usage["stream_seconds"] += monotonic() - start
                self.control["running"] = False
                self.store.control(self.control, self.usage, kind="stream_stopped", at=self.now())
                self._publish()

    def _receive(self, event: dict) -> None:
        # Synchronous callback runs on this event loop, with no await between commit and queue.
        # Async operations hold the lock only while executing synchronous store operations.
        received = datetime.fromisoformat(event["received_at"])
        raw = event.get("raw_decoded")
        if not isinstance(raw, dict):
            raw = {"adapter_error": "non-object source payload"}
        next_control = dict(self.control)
        try:
            normalize(raw, "yahoo_stream", received)
            next_control.update(feed="receiving", reason="Persisted source observations")
        except ValueError:
            pass
        _, accepted = self.store.record_stream(raw, received, next_control, self.usage)
        if accepted["kind"] != "quarantined":
            self.control = next_control
        self._publish()

    async def stop(self) -> None:
        self.session_stop.set()
        self.history_cancel.set()
        task = self.task
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await self.history_done.wait()
        await self.status(feed="stopped", reason="Stopped explicitly", running=False, interval_refresh="stopped")

    async def simulate_unavailable(self) -> None:
        await self.stop()
        await self.status(feed="unavailable", reason="Simulated unavailable feed; no source request",
                          simulated=True, running=False)

    async def fetch_history(self, symbol: str) -> dict:
        async with self.lock:
            if self.offline:
                raise ControlError("Offline recorded-data mode: upstream access disabled")
            if self.history_busy:
                raise ControlError("An interval fetch is already in progress")
            if self.usage["blocked"] or self.usage["history_fetches"] >= 3:
                raise ControlError("Three-fetch budget exhausted or access denied")
            self._allow_symbols([symbol])
            self.usage["history_fetches"] += 1
            self.history_busy = True
            self.history_cancel.clear()
            self.history_done.clear()
            self.control["history"] = "fetching"
            self.store.control(self.control, self.usage, kind="history_requested", at=self.now())
            self._publish()
        try:
            # Shield the bounded worker: cancelling an asyncio waiter cannot stop a thread.
            # The real fetcher checks history_cancel before/after every HTTP request.
            worker = asyncio.create_task(asyncio.to_thread(self.history_fetcher.fetch, symbol,
                **({"cancel_event": self.history_cancel,
                   "deadline": self.session_deadline if self.control.get("running") else None} if isinstance(self.history_fetcher, YahooHistoryFetcher) else {})))
            try:
                result = await asyncio.shield(worker)
            except asyncio.CancelledError:
                self.history_cancel.set()
                # Drain before releasing history_busy/closing the cache. No overlap.
                try:
                    await worker
                except Exception:
                    pass
                raise
            async with self.lock:
                self.usage["http_calls"].extend(result["ledger"])
                self.control["history"] = "received" if result["rows"] else "no_data"
                _, counts = self.store.record_bars(
                    symbol, result["rows"], result["retrieved_at"], result["metadata"],
                    "yahoo_interval", self.control, self.usage)
                self.control["last_interval_fetch_id"] = counts["fetch_id"]
                self._publish()
                return counts
        except HistoryUnavailable as exc:
            async with self.lock:
                self.usage["http_calls"].extend(exc.ledger)
                self.usage["blocked"] = self.usage["blocked"] or exc.blocked
                self.control["history"] = "unavailable"
                self.control["reason"] = f"Interval fetch unavailable: {exc}"
                self.store.control(self.control, self.usage, kind="history_failed", at=self.now())
                self._publish()
            if exc.blocked:
                self.session_stop.set()
                self.history_cancel.set()
                if self.task and self.task is not asyncio.current_task() and not self.task.done():
                    self.task.cancel()
                await self.status(feed="unavailable",
                                  reason="Yahoo access denied/rate limited; all source requests stopped")
            raise ControlError(str(exc)) from None
        except Exception as exc:
            # A failed fetch/projection must not leave the UI permanently "fetching".
            await self.status(history="unavailable", reason=f"Interval processing failed: {type(exc).__name__}")
            raise
        finally:
            self.history_busy = False
            self.history_done.set()

    async def _wait_refresh(self, delay: float) -> None:
        try:
            await asyncio.wait_for(self.session_stop.wait(), timeout=delay)
        except TimeoutError:
            pass

    async def _refresh_intervals(self, symbol: str, deadline: float) -> None:
        """Immediate then fixed-delay polling, shared durable three-request budget.

        Failure delays are 60s, then 120s (default cadence); successes reset backoff.
        An in-flight request drains on Stop; transport checks cancellation between HTTPs.
        """
        failures = 0
        while not self.session_stop.is_set() and monotonic() < deadline:
            if self.usage["blocked"] or self.usage["history_fetches"] >= 3:
                await self.status(interval_refresh="budget_exhausted")
                return
            # A manual fetch uses the same busy flag/budget, never overlaps this loop.
            if self.history_busy:
                await self.refresh_wait(min(self.refresh_cadence, max(0, deadline - monotonic())))
                continue
            await self.status(interval_refresh="fetching")
            try:
                await self.fetch_history(symbol)
                failures = 0
                await self.status(interval_refresh="waiting")
            except ControlError:
                failures += 1
                if self.usage["blocked"] or self.session_stop.is_set():
                    return
                await self.status(interval_refresh="backoff")
            except Exception as exc:
                # Persistence/unexpected failure is not a reason to keep polling.
                await self.status(interval_refresh="failed", reason=f"Interval refresh stopped: {type(exc).__name__}")
                return
            if self.usage["history_fetches"] >= 3:
                await self.status(interval_refresh="budget_exhausted")
                return
            delay = min(self.refresh_cadence * (2 ** max(0, failures - 1)), 120)
            await self.refresh_wait(min(delay, max(0, deadline - monotonic())))

    async def close(self) -> None:
        await self.stop()
        await asyncio.to_thread(self.history_fetcher.close)
