"""Bounded, injectable transport. No normalization/database imports or startup connection."""
import asyncio
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import re
from time import monotonic
from typing import Protocol

STREAM_SYMBOLS = {"BTC-USD", "ETH-USD", "AAPL", "MSFT"}


def redact(value: object) -> object:
    if isinstance(value, dict):
        return {str(k): "[REDACTED]" if re.search(
            r"cookie|credential|authorization|password|secret|token|crumb", str(k), re.I
        ) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,})",
                      "[REDACTED]", value)
    return value


class Transport(Protocol):
    async def run(self, symbols: list[str], handler: Callable,
                  connected: Callable) -> None: ...
    async def close(self) -> None: ...


class YahooTransport:
    """Pinned yfinance 1.8.0 transport; intentionally bypasses its unbounded listen loop.

    Public subscribe/close plus pinned _ws/_decode_message seam. Each recv is
    cancellable; normal close/errors propagate. No HTTP, cookie or retry logic.
    """
    def __init__(self):
        self.client = None

    async def run(self, symbols: list[str], handler: Callable,
                  connected: Callable) -> None:
        import yfinance as yf
        if yf.__version__ != "1.8.0":
            raise RuntimeError("Pinned yfinance transport requires 1.8.0")
        self.client = yf.AsyncWebSocket(verbose=False)
        await self.client.subscribe(symbols)
        connected()
        while True:
            wire = await self.client._ws.recv()
            try:
                envelope = json.loads(wire)
                encoded = envelope["message"]
                if not isinstance(encoded, str):
                    raise ValueError("expected encoded pricing message")
                decoded = self.client._decode_message(encoded)
                if not isinstance(decoded, dict) or "error" in decoded:
                    raise ValueError("invalid pricing payload")
            except (ValueError, KeyError, TypeError):
                handler({"adapter_error": "malformed_wire_message"})
                continue
            handler(decoded)

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()
            task = self.client._heartbeat_task
            if task is not None:
                await asyncio.gather(task, return_exceptions=True)


@dataclass
class CaptureResult:
    started_at: str
    ended_at: str = ""
    duration_seconds: float = 0
    connected_seconds: float = 0
    connection_attempts: int = 1
    reconnect_count: int = 0
    received_messages: int = 0
    malformed_messages: int = 0
    status: str = "connecting"
    stop_reason: str = ""
    error_type: str | None = None
    http_status: int | None = None
    cleanup_completed: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


class SinkFailure(RuntimeError):
    pass


class YahooStreamAdapter:
    def __init__(self, transport_factory: Callable[[], Transport] = YahooTransport,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self.transport_factory, self.now = transport_factory, now

    async def capture(self, symbols: list[str], sink: Callable[[dict], None],
                      *, seconds: float = 60) -> CaptureResult:
        if not 0 < seconds <= 110 or not 1 <= len(symbols) <= 2:
            raise ValueError("capture requires 1-2 instruments and 0<seconds<=110")
        if len(set(symbols)) != len(symbols) or any(s not in STREAM_SYMBOLS for s in symbols):
            raise ValueError("unsupported/duplicate symbol")
        result = CaptureResult(started_at=self.now().isoformat())
        start, connected_at = monotonic(), None
        transport = self.transport_factory()

        def connected() -> None:
            nonlocal connected_at
            connected_at = monotonic()
            result.status = "waiting"

        def handle(payload: object) -> None:
            received = self.now().astimezone(timezone.utc).isoformat()
            result.received_messages += 1
            valid = (isinstance(payload, dict) and payload.get("id") in symbols
                     and "time" in payload and "price" in payload)
            if not valid:
                result.malformed_messages += 1
            event = {"kind": "source_message", "provenance": "actual_yahoo_stream",
                     "receipt_seq": result.received_messages, "received_at": received,
                     "envelope_valid": valid, "raw_decoded": redact(payload)}
            try:
                sink(event)
            except Exception as exc:
                raise SinkFailure("evidence sink failed") from exc
            if valid:
                result.status = "receiving"

        try:
            async with asyncio.timeout(seconds):
                await transport.run(symbols, handle, connected)
            result.stop_reason = "source_closed"
        except TimeoutError:
            result.stop_reason = "time_limit"
        except SinkFailure:
            result.status, result.stop_reason = "storage_error", "sink_failure"
        except Exception as exc:
            response = getattr(exc, "response", None)
            code = getattr(response, "status_code", getattr(exc, "status_code", None))
            result.http_status = code if isinstance(code, int) else None
            result.error_type = type(exc).__name__
            result.status = "denied" if code in (401, 403, 429) else "unavailable"
            result.stop_reason = "access_denied_or_rate_limited" if code in (401, 403, 429) else "source_error"
        finally:
            # Time budget reserves at most 3 seconds for cleanup; never reconnect.
            try:
                await asyncio.wait_for(transport.close(), timeout=3)
                result.cleanup_completed = True
            except Exception:
                result.cleanup_completed = False
            end = monotonic()
            result.duration_seconds = round(end - start, 6)
            result.connected_seconds = round(end - connected_at, 6) if connected_at else 0
            result.ended_at = self.now().isoformat()
        if result.stop_reason in ("time_limit", "source_closed"):
            result.status = "captured" if result.received_messages > result.malformed_messages else "no_data"
        return result
