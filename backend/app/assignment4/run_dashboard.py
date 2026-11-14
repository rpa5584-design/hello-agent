"""Explicit isolated launcher; offline recording imports never contact a provider."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from . import create_app
from .database import initialize
from .dashboard_store import DashboardStore, EMPTY_CONTROL


def import_recording(path: Path, recording: Path) -> None:
    initialize(path)
    store = DashboardStore(path)
    if store.snapshot()["max_cursor"]:
        raise ValueError("Recording import requires a new empty database; never reset existing data")
    data = json.loads(recording.read_text(encoding="utf-8"))
    if data.get("format") != "assignment4-recording-v1":
        raise ValueError("Unsupported recording format")
    control = {**EMPTY_CONTROL, "offline": True, "reason": "Imported recorded Yahoo evidence; not current live data"}
    usage = store.usage()
    for event in data["events"]:
        received = datetime.fromisoformat(event["received_at"])
        if event["kind"] == "stream":
            store.record_stream(event["raw"], received, control, usage)
        elif event["kind"] == "interval":
            _, counts = store.record_bars(event["symbol"], event["rows"], received,
                event["metadata"], "yahoo_interval", control, usage)
            control["last_interval_fetch_id"] = counts["fetch_id"]
        else:
            raise ValueError("Unsupported recording event")
    store.control(control, usage, kind="recording_imported", at=datetime.now(timezone.utc))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--recording", type=Path)
    parser.add_argument("--no-reconnect", action="store_true")
    args = parser.parse_args()
    if args.recording:
        if not args.offline:
            parser.error("--recording requires --offline")
        import_recording(args.database, args.recording)
    import uvicorn
    uvicorn.run(create_app(args.database, max_attempts=1 if args.no_reconnect else 2,
                          offline=args.offline), host="127.0.0.1", port=8001)


if __name__ == "__main__":
    main()
