"""Offline launcher controls use disposable databases, never providers."""
import asyncio
from datetime import datetime, timezone
import json

import pytest
from fastapi.testclient import TestClient

from app.assignment4 import create_app
from app.assignment4.database import initialize
from app.assignment4.dashboard import Dashboard, ControlError
from app.assignment4.run_dashboard import import_recording
from app.assignment4.yahoo_stream import CaptureResult


def test_one_attempt_configuration_never_reconnects(tmp_path):
    class Source:
        async def capture(self, symbols, sink, seconds):
            return CaptureResult("2026-11-14T00:00:00Z", status="no_data", stop_reason="source_error")
    async def scenario():
        path = tmp_path / "one.sqlite3"
        initialize(path)
        d = Dashboard(path, adapter_factory=Source, max_attempts=1)
        await d.start(["BTC-USD"], 1)
        await d.task
        assert d.usage["attempts"] == 1 and d.usage["reconnects"] == 0
        with pytest.raises(ControlError):
            await d.start(["BTC-USD"], 1)
    asyncio.run(scenario())


def test_recorded_import_offline_websocket_replay_and_no_upstream(tmp_path):
    path = tmp_path / "offline.sqlite3"
    fixture = tmp_path / "recording.json"
    fixture.write_text(json.dumps({"format": "assignment4-recording-v1", "events": [
        {"kind": "stream", "received_at": "2026-11-14T00:00:01+00:00",
         "raw": {"id": "BTC-USD", "time": 1794614400000, "price": 123}},
        {"kind": "interval", "symbol": "BTC-USD", "received_at": "2026-11-14T00:01:01+00:00",
         "metadata": {}, "rows": [{"source_time_s": 1794614400, "open": 120,
         "high": 125, "low": 119, "close": 123, "volume": 0}]}]}))
    import_recording(path, fixture)
    with pytest.raises(ValueError, match="empty"):
        import_recording(path, fixture)
    def forbidden():
        raise AssertionError("Provider construction forbidden")
    with TestClient(create_app(path, offline=True, adapter_factory=forbidden)) as c:
        assert c.post("/api/assignment4/live/start", json={"symbols":["BTC-USD"],"seconds":10}).status_code == 409
        assert c.post("/api/assignment4/interval/fetch", json={"symbol":"BTC-USD"}).status_code == 409
        with c.websocket_connect("/api/assignment4/ws") as ws:
            ws.send_json({"type":"hello","mode":"replay","cursor":2})
            result=ws.receive_json()
            assert result["mode"] == "replay"
            assert result["payload"]["quotes"]["BTC-USD"]["price"] == 123
        assert c.post("/api/assignment4/demo/unavailable").status_code == 200
        state = c.get("/api/assignment4/dashboard").json()["payload"]
        assert state["control"]["offline"] and state["control"]["simulated"]
        assert state["usage"]["attempts"] == state["usage"]["history_fetches"] == 0
