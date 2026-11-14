"""Parameterized transactional persistence. Each receipt and its projection commit together."""
from datetime import datetime, timezone
from contextlib import nullcontext
from pathlib import Path
import json
import sqlite3
from uuid import uuid4

from .database import connect
from .models import Provenance, canonical_payload, json_text, normalize, utc_text
from .projection import project


def _active(connection: sqlite3.Connection, through: int | None = None) -> dict[str, dict]:
    clause = "" if through is None else "WHERE v.receipt_seq<=?"
    params = () if through is None else (through,)
    rows = connection.execute(
        f"""SELECT v.*, o.first_receipt_seq FROM observation_versions v
            JOIN observations o USING(observation_id) {clause}
            ORDER BY v.receipt_seq""", params).fetchall()
    active = {}
    for row in rows:
        active[row["observation_id"]] = {
            **json.loads(row["normalized_json"]), "version_id": row["version_id"],
            "first_receipt_seq": row["first_receipt_seq"],
        }
    return active


def _candles(connection: sqlite3.Connection) -> list[dict]:
    rows = connection.execute("""SELECT state_json FROM candles_current
        ORDER BY source,provenance,symbol,bucket_start_ms""").fetchall()
    return [json.loads(r[0]) for r in rows]


class MarketStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def ingest(self, payload: dict, *, provenance: Provenance,
               received_at: datetime | None = None,
               connection: sqlite3.Connection | None = None) -> dict:
        """Internal service boundary, not an HTTP ingestion route.

        Strict JSON <=64KiB is required before durable receipt creation. Invalid
        normalized observations within that envelope are quarantined durably.
        """
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
        if provenance not in ("fixture", "yahoo_stream"):
            raise ValueError("unsupported ingestion provenance")
        raw = json_text(payload)
        if len(raw.encode("utf-8")) > 65536:
            raise ValueError("payload exceeds 64KiB")
        received_at = received_at if received_at is not None else datetime.now(timezone.utc)
        received = utc_text(received_at)
        with (nullcontext(connection) if connection is not None else connect(self.path)) as connection:
            if not connection.in_transaction:
                connection.execute("BEGIN IMMEDIATE")
            seq = connection.execute(
                """INSERT INTO receipts(received_at,provenance,raw_payload_json,kind)
                   VALUES (?,?,?,'quarantined')""", (received, provenance, raw)).lastrowid
            try:
                observation = normalize(payload, provenance, received_at)
            except ValueError as exc:
                connection.execute("UPDATE receipts SET error=? WHERE receipt_seq=?", (str(exc), seq))
                return {"receipt_seq": seq, "kind": "quarantined", "error": str(exc)}
            canonical = canonical_payload(payload, observation)
            prior = connection.execute(
                """SELECT v.* FROM observations o JOIN observation_versions v USING(observation_id)
                   WHERE o.base_slot_key=? ORDER BY v.receipt_seq DESC LIMIT 1""",
                (observation.slot_key,)).fetchone()
            if prior is not None and prior["canonical_payload"] == canonical:
                connection.execute(
                    "UPDATE receipts SET kind='duplicate',version_id=? WHERE receipt_seq=?",
                    (prior["version_id"], seq))
                return {"receipt_seq": seq, "kind": "duplicate", "version_id": prior["version_id"]}
            preserve_distinct = provenance == "yahoo_stream"
            if prior is None or preserve_distinct:
                observation_id, revision, kind = str(uuid4()), 1, "new"
                slot_key = json_text([observation.slot_key, seq]) if preserve_distinct else observation.slot_key
                connection.execute(
                    """INSERT INTO observations
                       (observation_id,slot_key,identity_kind,first_receipt_seq,base_slot_key)
                       VALUES (?,?,'app_quote_slot',?,?)""",
                    (observation_id, slot_key, seq, observation.slot_key))
            else:
                observation_id = prior["observation_id"]
                revision, kind = prior["revision_no"] + 1, "revision"
            version_id = connection.execute(
                """INSERT INTO observation_versions
                   (observation_id,revision_no,receipt_seq,supersedes_version_id,canonical_payload,
                    normalized_json,ambiguous_same_time) VALUES (?,?,?,?,?,?,?)""",
                (observation_id, revision, seq, prior["version_id"] if prior and not preserve_distinct else None,
                 canonical, json_text(observation.as_dict()), int(prior is not None))).lastrowid
            connection.execute("UPDATE receipts SET kind=?,version_id=? WHERE receipt_seq=?",
                               (kind, version_id, seq))
            state = project(_active(connection), _candles(connection), seq, received)
            connection.execute("DELETE FROM candles_current")
            connection.executemany(
                "INSERT INTO candles_current VALUES (?,?,?,?,?)",
                [(c["source"], c["provenance"], c["symbol"], c["bucket_start_ms"], json_text(c))
                 for c in state])
            connection.execute("INSERT INTO projection_events VALUES (?,?)", (seq, json_text(state)))
            return {"receipt_seq": seq, "kind": kind, "observation_id": observation_id,
                    "version_id": version_id, "revision_no": revision}

    def snapshot(self) -> dict:
        with connect(self.path, readonly=True) as connection:
            connection.execute("BEGIN")
            seq = connection.execute("SELECT coalesce(max(receipt_seq),0) FROM receipts").fetchone()[0]
            return {"mode": "stored", "as_of_receipt_seq": seq, "candles": _candles(connection),
                    "streaming_connected": False}

    def receipts(self, *, after: int = 0, limit: int = 100) -> list[dict]:
        if after < 0 or not 1 <= limit <= 500:
            raise ValueError("receipt pagination bounds invalid")
        with connect(self.path, readonly=True) as connection:
            return [dict(row) for row in connection.execute(
                "SELECT * FROM receipts WHERE receipt_seq>? ORDER BY receipt_seq LIMIT ?",
                (after, limit))]

    def versions(self, observation_id: str) -> list[dict]:
        with connect(self.path, readonly=True) as connection:
            return [dict(row) for row in connection.execute(
                """SELECT * FROM observation_versions WHERE observation_id=?
                   ORDER BY revision_no""", (observation_id,))]

    def replay(self, *, through: int | None = None) -> dict:
        """Read a frozen receipt prefix; never reads the latest projection as its input."""
        if through is not None and through < 0:
            raise ValueError("replay cursor must be nonnegative")
        with connect(self.path, readonly=True) as connection:
            connection.execute("BEGIN")
            latest = connection.execute("SELECT coalesce(max(receipt_seq),0) FROM receipts").fetchone()[0]
            cutoff = latest if through is None else min(through, latest)
            rows = connection.execute(
                """SELECT r.receipt_seq,r.received_at,v.*,o.first_receipt_seq
                   FROM receipts r JOIN observation_versions v ON v.receipt_seq=r.receipt_seq
                   JOIN observations o USING(observation_id)
                   WHERE r.receipt_seq<=? ORDER BY r.receipt_seq""", (cutoff,)).fetchall()
            active, state = {}, []
            for row in rows:
                active[row["observation_id"]] = {
                    **json.loads(row["normalized_json"]), "version_id": row["version_id"],
                    "first_receipt_seq": row["first_receipt_seq"],
                }
                state = project(active, state, row["receipt_seq"], row["received_at"])
            return {"mode": "replay", "as_of_receipt_seq": cutoff, "candles": state,
                    "streaming_connected": False}
