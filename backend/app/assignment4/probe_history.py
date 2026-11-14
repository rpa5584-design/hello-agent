"""Explicit investigation only. One history call; <=2 chart requests; no app DB."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import tempfile
from time import monotonic
from urllib.parse import urlsplit

from .yahoo_stream import redact


class ProbeStopped(BaseException):
    """Bypass library fallback/retry exception handlers when authorization bounds are hit."""


class RequestBudget:
    def __init__(self):
        self.chart_requests = 0
        self.http_calls = []
        self.start = monotonic()

    def before(self, url: str) -> dict:
        if monotonic() - self.start >= 45 or len(self.http_calls) >= 8:
            raise ProbeStopped("probe budget exhausted")
        parsed = urlsplit(url)
        chart = "/v8/finance/chart/" in parsed.path
        if chart:
            if self.chart_requests >= 2:
                raise ProbeStopped("two chart requests exhausted")
            self.chart_requests += 1
        row = {"host": parsed.hostname, "path": parsed.path, "chart": chart,
               "started_at": datetime.now(timezone.utc).isoformat(), "http_status": None}
        self.http_calls.append(row)
        return row

    def after(self, row: dict, status: int) -> None:
        row["http_status"] = status
        if status in (401, 403, 429):
            raise ProbeStopped(f"access denied/rate limited HTTP {status}")


def main() -> None:
    import argparse
    import yfinance as yf
    from curl_cffi.requests import Session
    from yfinance.config import YfConfig
    from yfinance import cache

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve evidence before requests and never overwrite prior results.
    with args.output.open("x", encoding="utf-8") as output:
        budget = RequestBudget()
        result = {"provenance": "actual_yahoo_intraday_history", "symbol": "BTC-USD",
                  "history_calls": 0, "requested_interval": "1m", "requested_period": "1d",
                  "source": "Yahoo Finance via yfinance.Ticker.history",
                  "package_version": yf.__version__, "chart_responses": []}
        class GuardedSession(Session):
            def request(self, method, url, **kwargs):
                row = budget.before(url)
                kwargs["timeout"] = 5
                response = super().request(method, url, **kwargs)
                budget.after(row, response.status_code)
                if row["chart"] and response.status_code == 200:
                    doc = response.json()
                    values = doc.get("chart", {}).get("result") or []
                    if values:
                        value = values[0]
                        meta = value.get("meta", {})
                        times = value.get("timestamp") or []
                        quotes = (value.get("indicators", {}).get("quote") or [{}])[0]
                        bars = [{"source_time_s": t, **{
                            name: (data[i] if i < len(data) else None)
                            for name, data in quotes.items()}}
                            for i, t in enumerate(times)]
                        result["chart_responses"].append({
                            "received_at": datetime.now(timezone.utc).isoformat(),
                            "metadata": {k: meta.get(k) for k in (
                                "symbol", "currency", "instrumentType", "exchangeName",
                                "exchangeTimezoneName", "dataGranularity", "range")},
                            "raw_bar_count": len(times), "raw_bars_tail": bars[-20:],
                        })
                return response

        old_hide, old_retries = YfConfig.debug.hide_exceptions, YfConfig.network.retries
        try:
            YfConfig.debug.hide_exceptions = False
            YfConfig.network.retries = 0
            with tempfile.TemporaryDirectory(prefix="pytest-cache-files-yahoo-",
                                             dir=Path.cwd(), ignore_cleanup_errors=True) as temp:
                yf.set_tz_cache_location(str(Path(temp) / "cache"))
                try:
                    with GuardedSession(impersonate="chrome") as session:
                        ticker = yf.Ticker("BTC-USD", session=session)
                        result["history_calls"] = 1
                        frame = ticker.history(period="1d", interval="1m", auto_adjust=False,
                                               actions=False, repair=False, keepna=True,
                                               timeout=5, raise_errors=True)
                        result["library_row_count"] = len(frame)
                        result["library_rows_tail"] = []
                        for index, row in frame.tail(20).iterrows():
                            values = {}
                            for name in ("Open", "High", "Low", "Close", "Volume"):
                                value = float(row[name])
                                values[name] = value if math.isfinite(value) else None
                            result["library_rows_tail"].append(
                                {"source_time": index.isoformat(), **values})
                        result["status"] = "received" if len(frame) else "no_data"
                finally:
                    # No cookie/timezone DB escapes this worktree-local temporary probe.
                    for manager in (cache._TzDBManager, cache._CookieDBManager, cache._ISINDBManager):
                        manager.close_db()
        except ProbeStopped as exc:
            result["status"] = "stopped"
            result["stop_reason"] = str(exc)  # Fixed guard wording only, no library response bodies.
        except Exception as exc:
            result["status"] = "unavailable"
            result["error_type"] = type(exc).__name__
        finally:
            YfConfig.debug.hide_exceptions, YfConfig.network.retries = old_hide, old_retries
            result["chart_requests"] = budget.chart_requests
            result["http_calls"] = budget.http_calls
            result["duration_seconds"] = round(monotonic() - budget.start, 6)
            result["ended_at"] = datetime.now(timezone.utc).isoformat()
            output.write(json.dumps(redact(result), allow_nan=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "status", "history_calls", "chart_requests", "duration_seconds")}))


if __name__ == "__main__":
    main()
