"""Mocked source tests: no live network, fixtures never saved as actual evidence."""
import asyncio
import base64
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.assignment4.yahoo_stream import YahooStreamAdapter, YahooTransport, redact

NOW = datetime(2026, 11, 13, 22, tzinfo=timezone.utc)
MESSAGE = {"id": "BTC-USD", "time": "1794607200000", "price": 100.0}


class FakeTransport:
    def __init__(self, messages=(), error=None, wait=False):
        self.messages, self.error, self.wait, self.closed = messages, error, wait, False

    async def run(self, symbols, handler, connected):
        if self.error:
            raise self.error
        connected()
        for value in self.messages:
            handler(value)
        if self.wait:
            await asyncio.Event().wait()

    async def close(self):
        self.closed = True


def run(fake, sink=None, seconds=0.02):
    events = []
    adapter = YahooStreamAdapter(lambda: fake, now=lambda: NOW)
    result = asyncio.run(adapter.capture(["BTC-USD"], sink or events.append, seconds=seconds))
    return result, events


def test_capture_missing_volume_and_same_time_messages_preserved():
    fake = FakeTransport([MESSAGE, {**MESSAGE, "price": 110.0}, MESSAGE])
    result, events = run(fake)
    assert result.status == "captured"
    assert result.received_messages == 3 and result.reconnect_count == 0
    assert [e["raw_decoded"]["price"] for e in events] == [100, 110, 100]
    assert all(e["received_at"] == NOW.isoformat() for e in events)
    assert all("day_volume" not in e["raw_decoded"] for e in events)
    assert fake.closed and result.cleanup_completed


@pytest.mark.parametrize("message", [{}, "bad", None,
                                     {"adapter_error": "malformed_wire_message"},
                                     {"id": "BTC-USD", "price": 1}])
def test_malformed_envelope_recorded_not_substituted(message):
    result, events = run(FakeTransport([message]))
    assert result.malformed_messages == 1 and not events[0]["envelope_valid"]
    assert result.status == "no_data"


def test_timeout_no_data_cleanup_and_no_reconnect():
    fake = FakeTransport(wait=True)
    result, events = run(fake)
    assert result.status == "no_data" and result.stop_reason == "time_limit"
    assert result.duration_seconds < 1 and not events and fake.closed
    assert result.connection_attempts == 1 and result.reconnect_count == 0


@pytest.mark.parametrize("code", [401, 403, 429])
def test_denied_or_rate_limited_stops_without_reconnect(code):
    error = RuntimeError("do not publish exception text")
    error.response = SimpleNamespace(status_code=code)
    result, events = run(FakeTransport(error=error))
    assert result.status == "denied" and result.http_status == code
    assert result.stop_reason == "access_denied_or_rate_limited"
    assert result.reconnect_count == 0 and not events


def test_unavailable_source_no_synthetic_fallback():
    result, events = run(FakeTransport(error=ConnectionError("secret detail")))
    assert result.status == "unavailable" and result.error_type == "ConnectionError"
    assert "secret" not in json.dumps(result.as_dict()) and not events


def test_sink_failure_not_mislabelled_feed_success():
    def broken(event):
        raise OSError("disk unavailable")
    result, _ = run(FakeTransport([MESSAGE]), sink=broken)
    assert result.status == "storage_error"
    assert result.stop_reason == "sink_failure"


@pytest.mark.parametrize("symbols,seconds", [
    ([], 1), (["AAPL", "MSFT", "BTC-USD"], 1), (["BTC-USD"], 111),
    (["BTC-USD"], 0), (["BTC-USD", "BTC-USD"], 1), (["UNKNOWN"], 1),
])
def test_capture_limits_checked_before_transport(symbols, seconds):
    def forbidden():
        raise AssertionError("transport constructed")
    with pytest.raises(ValueError):
        asyncio.run(YahooStreamAdapter(forbidden).capture(symbols, lambda e: None, seconds=seconds))


def test_recursive_redaction():
    assert redact({"cookie": "private", "nested": {"authorization": "private"},
                   "price": 100}) == {
                       "cookie": "[REDACTED]", "nested": {"authorization": "[REDACTED]"},
                       "price": 100}


def test_pinned_decoder_and_wire_loop_without_network(monkeypatch):
    import yfinance as yf
    from yfinance.pricing_pb2 import PricingData
    source = PricingData(id="BTC-USD", price=100, time=1794607200000, vol_24hr=500)
    encoded = base64.b64encode(source.SerializeToString()).decode()
    real_decoder = yf.AsyncWebSocket(verbose=False)._decode_message
    frames = iter([json.dumps({"message": encoded}), "not json"])

    class Client:
        _heartbeat_task = None
        def __init__(self, **kwargs):
            self._ws = self
        async def subscribe(self, symbols):
            assert symbols == ["BTC-USD"]
        async def recv(self):
            try:
                return next(frames)
            except StopIteration:
                raise ConnectionError("mock end") from None
        def _decode_message(self, encoded):
            return real_decoder(encoded)
        async def close(self):
            pass

    monkeypatch.setattr(yf, "AsyncWebSocket", Client)
    result, events = run_transport()
    assert events[0]["raw_decoded"]["time"] == "1794607200000"
    assert events[0]["raw_decoded"]["vol_24hr"] == "500"
    assert result.received_messages == 2 and result.malformed_messages == 1
    assert result.status == "unavailable"


def run_transport():
    events = []
    result = asyncio.run(YahooStreamAdapter(YahooTransport).capture(
        ["BTC-USD"], events.append, seconds=1))
    return result, events
