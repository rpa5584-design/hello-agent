"""Explicit one-shot interval fetch; raw provider rows, not transformed library Volume."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from time import monotonic

from .probe_history import RequestBudget, ProbeStopped


class HistoryUnavailable(RuntimeError):
    def __init__(self, reason: str, ledger: list, blocked: bool = False):
        super().__init__(reason)
        self.ledger, self.blocked = ledger, blocked


class YahooHistoryFetcher:
    def __init__(self):
        self.cache_dir = None

    def fetch(self, symbol: str, *, cancel_event=None, deadline=None) -> dict:
        import yfinance as yf
        from curl_cffi.requests import Session
        from yfinance.config import YfConfig
        from yfinance import cache
        if self.cache_dir is None:
            self.cache_dir = tempfile.TemporaryDirectory(
                prefix="pytest-cache-files-dashboard-yahoo-",
                dir=Path(__file__).resolve().parents[2], ignore_cleanup_errors=True)
        yf.set_tz_cache_location(str(Path(self.cache_dir.name) / "cache"))
        budget, captures = RequestBudget(), []
        class GuardedSession(Session):
            def request(self, method, url, **kwargs):
                if (cancel_event is not None and cancel_event.is_set()) or (deadline is not None and monotonic() >= deadline):
                    raise ProbeStopped("interval refresh cancelled; no new HTTP request")
                row = budget.before(url)
                kwargs["timeout"] = min(5, max(0.001, deadline - monotonic())) if deadline is not None else 5
                response = super().request(method, url, **kwargs)
                budget.after(row, response.status_code)
                if (cancel_event is not None and cancel_event.is_set()) or (deadline is not None and monotonic() >= deadline):
                    raise ProbeStopped("interval refresh cancelled after in-flight HTTP response")
                if row["chart"] and response.status_code == 200:
                    values = response.json().get("chart", {}).get("result") or []
                    for value in values:
                        meta = value.get("meta", {})
                        if meta.get("dataGranularity") != "1m":
                            continue  # Timezone/daily overhead is not a minute product.
                        if meta.get("symbol") != symbol:
                            raise ProbeStopped("provider symbol mismatch")
                        timestamps = value.get("timestamp") or []
                        quote = (value.get("indicators", {}).get("quote") or [{}])[0]
                        rows = [{"source_time_s": timestamp, **{
                            field: data[i] if i < len(data) else None
                            for field, data in quote.items()}}
                            for i, timestamp in enumerate(timestamps)]
                        captures.append({"rows": rows,
                            "retrieved_at": datetime.now(timezone.utc),
                            "metadata": {k: meta.get(k) for k in (
                                "symbol", "currency", "instrumentType", "exchangeName",
                                "exchangeTimezoneName", "dataGranularity", "range")}})
                return response
        old_hide, old_retry = YfConfig.debug.hide_exceptions, YfConfig.network.retries
        try:
            YfConfig.debug.hide_exceptions, YfConfig.network.retries = False, 0
            with GuardedSession(impersonate="chrome") as session:
                yf.Ticker(symbol, session=session).history(
                    period="1d", interval="1m", auto_adjust=False, actions=False,
                    repair=False, keepna=True, timeout=5)
            if not captures:
                raise HistoryUnavailable("No raw 1m records returned", budget.http_calls)
            return {**captures[-1], "ledger": budget.http_calls,
                    "duration_seconds": monotonic() - budget.start}
        except ProbeStopped as exc:
            blocked = any(r["http_status"] in (401, 403, 429) for r in budget.http_calls)
            raise HistoryUnavailable(str(exc), budget.http_calls, blocked) from None
        except HistoryUnavailable:
            raise
        except Exception as exc:
            raise HistoryUnavailable(type(exc).__name__, budget.http_calls) from None
        finally:
            YfConfig.debug.hide_exceptions, YfConfig.network.retries = old_hide, old_retry

    def close(self) -> None:
        if self.cache_dir is not None:
            from yfinance import cache
            for manager in (cache._TzDBManager, cache._CookieDBManager, cache._ISINDBManager):
                manager.close_db()
            self.cache_dir.cleanup()
