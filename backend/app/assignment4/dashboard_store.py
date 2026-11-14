"""Atomic domain records plus durable publication cursors; no network."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from .controller import MarketStore
from .database import connect
from .models import json_text, utc_text
from .interval_models import normalize_bar, canonical_bar

DEFAULT_USAGE = {"stream_reserved_seconds": 0, "stream_seconds": 0, "attempts": 0,
                 "reconnects": 0, "history_fetches": 0, "http_calls": [],
                 "instruments": [], "blocked": False}
EMPTY_CONTROL = {"feed": "stopped", "reason": "Start live explicitly; no automatic connection",
                 "history": "not_fetched", "simulated": False, "running": False}


class DashboardStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.market = MarketStore(self.path)

    def usage(self) -> dict:
        with connect(self.path, readonly=True) as c:
            row = c.execute("SELECT state_json FROM dashboard_budget WHERE singleton=1").fetchone()
            return json.loads(row[0]) if row else json.loads(json_text(DEFAULT_USAGE))

    def _event(self, c: sqlite3.Connection, kind: str, at: datetime,
               control: dict, usage: dict) -> int:
        c.execute("INSERT OR REPLACE INTO dashboard_budget VALUES (1,?)", (json_text(usage),))
        stream = c.execute("SELECT coalesce(max(receipt_seq),0) FROM receipts").fetchone()[0]
        bars = c.execute("SELECT coalesce(max(receipt_seq),0) FROM interval_receipts").fetchone()[0]
        return c.execute(
            """INSERT INTO dashboard_events(recorded_at,kind,stream_cutoff,bar_cutoff,control_json,usage_json)
               VALUES (?,?,?,?,?,?)""",
            (utc_text(at), kind, stream, bars, json_text(control), json_text(usage))).lastrowid

    def control(self, control: dict, usage: dict, *, kind: str = "status",
                at: datetime | None = None) -> int:
        with connect(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            return self._event(c, kind, at or datetime.now(timezone.utc), control, usage)

    def record_stream(self, payload: dict, received_at: datetime, control: dict,
                      usage: dict) -> tuple[int, dict]:
        with connect(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            accepted = self.market.ingest(payload, provenance="yahoo_stream",
                                          received_at=received_at, connection=c)
            return self._event(c, "stream_receipt", received_at, control, usage), accepted

    def record_bars(self, symbol: str, raw_rows: list, retrieved_at: datetime,
                    metadata: dict, provenance: str, control: dict, usage: dict) -> tuple[int, dict]:
        if provenance not in ("yahoo_interval", "fixture_interval"):
            raise ValueError("unsupported interval provenance")
        if len(raw_rows) > 2000:
            raise ValueError("interval response exceeds 2000 row bound")
        counts = {"accepted": 0, "duplicate": 0, "quarantined": 0}
        with connect(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            fetch_id = c.execute(
                """INSERT INTO interval_fetches(symbol,provenance,retrieved_at,metadata_json)
                   VALUES (?,?,?,?)""",
                (symbol, provenance, utc_text(retrieved_at), json_text(metadata))).lastrowid
            for raw in raw_rows:
                # Strict JSON is a transport prerequisite; source nulls are retained.
                receipt = c.execute(
                    """INSERT INTO interval_receipts(fetch_id,raw_json,kind)
                       VALUES (?,?,'quarantined')""", (fetch_id, json_text(raw))).lastrowid
                try:
                    bar = normalize_bar(symbol, raw, retrieved_at)
                except ValueError as exc:
                    c.execute("UPDATE interval_receipts SET reason=? WHERE receipt_seq=?",
                              (str(exc), receipt))
                    counts["quarantined"] += 1
                    continue
                previous = c.execute(
                    """SELECT * FROM interval_versions WHERE symbol=? AND provenance=?
                       AND source_time_s=? ORDER BY version_id DESC LIMIT 1""",
                    (symbol, provenance, bar.source_time_s)).fetchone()
                canonical = canonical_bar(bar, raw)
                if previous and previous["canonical_json"] == canonical:
                    c.execute(
                        "UPDATE interval_receipts SET kind='duplicate',version_id=? WHERE receipt_seq=?",
                        (previous["version_id"], receipt))
                    counts["duplicate"] += 1
                    continue
                revision = previous["revision_no"] + 1 if previous else 1
                state = {**bar.state(), "provenance": provenance, "retrieved_at": utc_text(retrieved_at),
                         "revision_no": revision, "corrected": bool(previous),
                         "revision_meaning": "retrieved-snapshot/app-completion change; not exchange correction",
                         "receipt_seq": receipt, "fetch_id": fetch_id}
                version = c.execute(
                    """INSERT INTO interval_versions(symbol,provenance,source_time_s,revision_no,
                       receipt_seq,supersedes_version_id,canonical_json,state_json)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (symbol, provenance, bar.source_time_s, revision, receipt,
                     previous["version_id"] if previous else None, canonical, json_text(state))).lastrowid
                c.execute("UPDATE interval_receipts SET kind=?,version_id=? WHERE receipt_seq=?",
                          ("revision" if previous else "new", version, receipt))
                counts["accepted"] += 1
            return self._event(c, "interval_fetch", retrieved_at,
                               {**control, "last_interval_fetch_id": fetch_id}, usage), {
                **counts, "fetch_id": fetch_id}

    def _snapshot(self, c: sqlite3.Connection, through: int | None) -> dict:
        if through is None:
            event = c.execute("SELECT * FROM dashboard_events ORDER BY event_seq DESC LIMIT 1").fetchone()
        else:
            event = c.execute(
                "SELECT * FROM dashboard_events WHERE event_seq<=? ORDER BY event_seq DESC LIMIT 1",
                (max(0, through),)).fetchone()
        stream_cutoff, bar_cutoff = (event["stream_cutoff"], event["bar_cutoff"]) if event else (0, 0)
        projection = c.execute(
            "SELECT state_json FROM projection_events WHERE receipt_seq<=? ORDER BY receipt_seq DESC LIMIT 1",
            (stream_cutoff,)).fetchone()
        quotes = {}
        for row in c.execute(
            """SELECT r.receipt_seq,r.received_at,r.version_id,v.normalized_json
               FROM receipts r JOIN observation_versions v ON r.version_id=v.version_id
               WHERE r.receipt_seq<=? AND r.provenance='yahoo_stream' ORDER BY r.receipt_seq""", (stream_cutoff,)):
            value = json.loads(row["normalized_json"])
            quotes[value["symbol"]] = {**value, "receipt_seq": row["receipt_seq"],
                                      "version_id": row["version_id"], "received_at": row["received_at"]}
        versions = {}
        for row in c.execute(
            "SELECT * FROM interval_versions WHERE receipt_seq<=? ORDER BY version_id", (bar_cutoff,)):
            state = json.loads(row["state_json"])
            versions[(row["symbol"], row["provenance"], row["source_time_s"])] = {
                **state, "version_id": row["version_id"]}
        bars = sorted(versions.values(), key=lambda b: (b["symbol"], b["source_time_s"]))
        # Chart window is bounded; raw receipts/version history are never pruned.
        bars = [b for symbol in sorted({b["symbol"] for b in bars})
                for b in [v for v in bars if v["symbol"] == symbol][-500:]]
        stream_candles = json.loads(projection[0]) if projection else []
        stream_candles = [b for symbol in sorted({b["symbol"] for b in stream_candles})
                          for b in [v for v in stream_candles if v["symbol"] == symbol][-500:]]
        event_control = json.loads(event["control_json"]) if event else dict(EMPTY_CONTROL)
        fetch_id = event_control.get("last_interval_fetch_id")
        fetch = c.execute("SELECT * FROM interval_fetches WHERE fetch_id=?", (fetch_id,)).fetchone() if fetch_id else c.execute(
            """SELECT f.* FROM interval_fetches f JOIN interval_receipts r USING(fetch_id)
               WHERE r.receipt_seq<=? ORDER BY f.fetch_id DESC LIMIT 1""", (bar_cutoff,)).fetchone()
        # Per-symbol retrieval age must not make ETH look freshly fetched after BTC.
        # The saved last completed fetch ID also handles empty responses without
        # leaking a later retrieval into an earlier replay event.
        retrievals = {}
        if fetch:
            for item in c.execute(
                    "SELECT symbol,retrieved_at FROM interval_fetches WHERE fetch_id<=? ORDER BY fetch_id",
                    (fetch["fetch_id"],)):
                retrievals[item["symbol"]] = item["retrieved_at"]
        quarantined = c.execute(
            """SELECT r.receipt_seq,r.reason,r.raw_json,f.symbol,f.retrieved_at
               FROM interval_receipts r JOIN interval_fetches f USING(fetch_id)
               WHERE r.receipt_seq<=? AND r.kind='quarantined'
               ORDER BY r.receipt_seq DESC LIMIT 10""", (bar_cutoff,)).fetchall()
        last_receipts = c.execute(
            """SELECT r.receipt_seq,r.received_at,r.kind,r.version_id,r.raw_payload_json
               FROM receipts r WHERE r.receipt_seq<=? ORDER BY receipt_seq DESC LIMIT 5""",
            (stream_cutoff,)).fetchall()
        return {
            "cursor": event["event_seq"] if event else 0,
            "recorded_at": event["recorded_at"] if event else None,
            "event_kind": event["kind"] if event else "empty",
            "stream_cutoff": stream_cutoff, "bar_cutoff": bar_cutoff,
            "quotes": quotes, "stream_candles": stream_candles, "interval_bars": bars,
            "quarantine_count": c.execute(
                "SELECT count(*) FROM interval_receipts WHERE receipt_seq<=? AND kind='quarantined'",
                (bar_cutoff,)).fetchone()[0],
            "quarantine": [dict(r) for r in quarantined],
            "recent_receipts": [dict(r) for r in last_receipts],
            "last_interval_retrieval": fetch["retrieved_at"] if fetch else None,
            "interval_retrievals": retrievals,
            "control": json.loads(event["control_json"]) if event else dict(EMPTY_CONTROL),
            "usage": json.loads(event["usage_json"]) if event else json.loads(json_text(DEFAULT_USAGE)),
        }

    def snapshot(self, through: int | None = None) -> dict:
        with connect(self.path, readonly=True) as c:
            c.execute("BEGIN")
            state = self._snapshot(c, through)
            state["max_cursor"] = c.execute(
                "SELECT coalesce(max(event_seq),0) FROM dashboard_events").fetchone()[0]
            return state
