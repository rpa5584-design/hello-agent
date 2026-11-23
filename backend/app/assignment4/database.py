"""Independent schema; no earlier-app imports, seeding or implicit initialization."""
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sqlite3

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "assignment4.sqlite3"
SCHEMA_VERSION = 4
LEGACY_POLICY = '{"interval_ms":60000,"lateness_ms":10000,"normalization_version":1,"reducer_version":1,"volume":"unavailable"}'
V2_POLICY = '{"interval_ms":60000,"lateness_ms":10000,"normalization_version":2,"reducer_version":1,"volume":"unavailable","yahoo_identity":"preserve_distinct"}'
V3_POLICY = '{"interval_ms":60000,"lateness_ms":10000,"normalization_version":2,"reducer_version":1,"volume":"unavailable","yahoo_identity":"preserve_distinct","dashboard_version":3}'
POLICY = '{"interval_ms":60000,"lateness_ms":10000,"normalization_version":2,"reducer_version":1,"volume":"unavailable","yahoo_identity":"preserve_distinct","dashboard_version":4}'
SCHEMA = (
    """CREATE TABLE metadata (singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        policy TEXT NOT NULL)""",
    """CREATE TABLE receipts (
        receipt_seq INTEGER PRIMARY KEY AUTOINCREMENT,
        received_at TEXT NOT NULL, provenance TEXT NOT NULL
        CHECK(provenance IN ('fixture','yahoo_stream')),
        raw_payload_json TEXT NOT NULL, kind TEXT NOT NULL
        CHECK(kind IN ('new','revision','duplicate','quarantined')),
        error TEXT, version_id INTEGER REFERENCES observation_versions(version_id)
        DEFERRABLE INITIALLY DEFERRED)""",
    """CREATE TABLE observations (
        observation_id TEXT PRIMARY KEY NOT NULL, slot_key TEXT NOT NULL UNIQUE,
        identity_kind TEXT NOT NULL CHECK(identity_kind='app_quote_slot'),
        first_receipt_seq INTEGER NOT NULL UNIQUE REFERENCES receipts(receipt_seq),
        base_slot_key TEXT NOT NULL)""",
    """CREATE TABLE observation_versions (
        version_id INTEGER PRIMARY KEY AUTOINCREMENT,
        observation_id TEXT NOT NULL REFERENCES observations(observation_id),
        revision_no INTEGER NOT NULL CHECK(revision_no>=1),
        receipt_seq INTEGER NOT NULL UNIQUE REFERENCES receipts(receipt_seq),
        supersedes_version_id INTEGER REFERENCES observation_versions(version_id),
        canonical_payload TEXT NOT NULL, normalized_json TEXT NOT NULL,
        ambiguous_same_time INTEGER NOT NULL CHECK(ambiguous_same_time IN (0,1)),
        UNIQUE(observation_id,revision_no))""",
    """CREATE TABLE candles_current (
        source TEXT NOT NULL, provenance TEXT NOT NULL, symbol TEXT NOT NULL,
        bucket_start_ms INTEGER NOT NULL, state_json TEXT NOT NULL,
        PRIMARY KEY(source,provenance,symbol,bucket_start_ms))""",
    """CREATE TABLE projection_events (
        receipt_seq INTEGER PRIMARY KEY REFERENCES receipts(receipt_seq),
        state_json TEXT NOT NULL)""",
    "CREATE INDEX versions_observation ON observation_versions(observation_id,revision_no)",
    "CREATE INDEX observations_base_slot ON observations(base_slot_key)",
)


@contextmanager
def connect(path: Path, *, readonly: bool = False) -> Iterator[sqlite3.Connection]:
    mode = "ro" if readonly else "rw"
    connection = sqlite3.connect(path.resolve().as_uri() + f"?mode={mode}", uri=True, timeout=2)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    if readonly:
        connection.execute("PRAGMA query_only=ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(path: Path) -> None:
    """Only this explicit operation creates a database; reject unknown existing files."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb"):
            pass
        new = True
    except FileExistsError:
        new = False
    # Opening does not initialize an existing empty/foreign database.
    with connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if not new:
            if version == 1:
                policy = connection.execute("SELECT policy FROM metadata WHERE singleton=1").fetchone()
                if policy is None or policy["policy"] != LEGACY_POLICY:
                    raise RuntimeError("Legacy Assignment 4 policy mismatch")
                if connection.execute("SELECT 1 FROM receipts WHERE provenance='yahoo_stream' LIMIT 1").fetchone():
                    raise RuntimeError("Legacy Yahoo identity history requires explicit review; not migrated")
                connection.execute("ALTER TABLE observations ADD COLUMN base_slot_key TEXT NOT NULL DEFAULT ''")
                connection.execute("UPDATE observations SET base_slot_key=slot_key")
                connection.execute("CREATE INDEX observations_base_slot ON observations(base_slot_key)")
                connection.execute("UPDATE metadata SET policy=? WHERE singleton=1", (V2_POLICY,))
                version = 2
            if version == 2:
                policy = connection.execute("SELECT policy FROM metadata WHERE singleton=1").fetchone()
                if policy is None or policy["policy"] != V2_POLICY:
                    raise RuntimeError("Assignment 4 v2 policy mismatch")
                for statement in DASHBOARD_SCHEMA:
                    connection.execute(statement)
                connection.execute("UPDATE metadata SET policy=? WHERE singleton=1", (V3_POLICY,))
                connection.execute("PRAGMA user_version=3")
                version = 3
            if version == 3:
                policy = connection.execute("SELECT policy FROM metadata WHERE singleton=1").fetchone()
                if policy is None or policy["policy"] != V3_POLICY:
                    raise RuntimeError("Assignment 4 v3 policy mismatch")
                for statement in TRADING_SCHEMA:
                    connection.execute(statement)
                connection.execute("UPDATE metadata SET policy=? WHERE singleton=1", (POLICY,))
                connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                return
            if version != SCHEMA_VERSION:
                raise RuntimeError("Unsupported/uninitialized Assignment 4 database; no reset performed")
            row = connection.execute("SELECT policy FROM metadata WHERE singleton=1").fetchone()
            if row is None or row["policy"] != POLICY:
                raise RuntimeError("Assignment 4 policy mismatch; explicit migration required")
            return
        for statement in SCHEMA + DASHBOARD_SCHEMA + TRADING_SCHEMA:
            connection.execute(statement)
        connection.execute("INSERT INTO metadata VALUES (1,?)", (POLICY,))
        connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")


DASHBOARD_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS interval_fetches (
        fetch_id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
        provenance TEXT NOT NULL, retrieved_at TEXT NOT NULL, metadata_json TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS interval_receipts (
        receipt_seq INTEGER PRIMARY KEY AUTOINCREMENT,
        fetch_id INTEGER NOT NULL REFERENCES interval_fetches(fetch_id),
        raw_json TEXT NOT NULL, kind TEXT NOT NULL, reason TEXT,
        version_id INTEGER REFERENCES interval_versions(version_id) DEFERRABLE INITIALLY DEFERRED)""",
    """CREATE TABLE IF NOT EXISTS interval_versions (
        version_id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
        provenance TEXT NOT NULL, source_time_s INTEGER NOT NULL,
        revision_no INTEGER NOT NULL CHECK(revision_no>=1),
        receipt_seq INTEGER NOT NULL UNIQUE REFERENCES interval_receipts(receipt_seq),
        supersedes_version_id INTEGER REFERENCES interval_versions(version_id),
        canonical_json TEXT NOT NULL, state_json TEXT NOT NULL,
        UNIQUE(symbol,provenance,source_time_s,revision_no))""",
    """CREATE TABLE IF NOT EXISTS dashboard_events (
        event_seq INTEGER PRIMARY KEY AUTOINCREMENT, recorded_at TEXT NOT NULL,
        kind TEXT NOT NULL, stream_cutoff INTEGER NOT NULL, bar_cutoff INTEGER NOT NULL,
        control_json TEXT NOT NULL, usage_json TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS dashboard_budget (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1), state_json TEXT NOT NULL)""",
)

TRADING_SCHEMA = (
    """CREATE TABLE paper_account (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        initial_cash_cents INTEGER NOT NULL CHECK(initial_cash_cents>=0),
        cash_cents INTEGER NOT NULL CHECK(cash_cents>=0),
        realized_pnl_cents INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL)""",
    """CREATE TABLE paper_positions (
        symbol TEXT PRIMARY KEY, quantity TEXT NOT NULL,
        cost_cents INTEGER NOT NULL CHECK(cost_cents>=0))""",
    """CREATE TABLE paper_orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL, side TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
        status TEXT NOT NULL CHECK(status IN ('PENDING','FILLED')),
        signal_time_s INTEGER NOT NULL, created_at TEXT NOT NULL,
        fill_time_s INTEGER, fill_price REAL, quantity TEXT,
        notional_cents INTEGER)""",
    """CREATE INDEX paper_orders_pending ON paper_orders(status,symbol,order_id)""",
    """CREATE TABLE paper_fills (
        fill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL UNIQUE REFERENCES paper_orders(order_id),
        symbol TEXT NOT NULL, side TEXT NOT NULL,
        fill_time_s INTEGER NOT NULL, fill_price REAL NOT NULL,
        quantity TEXT NOT NULL, notional_cents INTEGER NOT NULL,
        realized_pnl_cents INTEGER NOT NULL)""",
    """CREATE TABLE paper_bar_progress (
        symbol TEXT NOT NULL, source_time_s INTEGER NOT NULL,
        version_id INTEGER NOT NULL,
        open_processed INTEGER NOT NULL CHECK(open_processed IN (0,1)),
        signal_processed INTEGER NOT NULL CHECK(signal_processed IN (0,1)),
        PRIMARY KEY(symbol,source_time_s))""",
    """CREATE TABLE backtest_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
        created_at TEXT NOT NULL, starting_cash_cents INTEGER NOT NULL,
        ending_cash_cents INTEGER NOT NULL, realized_pnl_cents INTEGER NOT NULL,
        unrealized_pnl_cents INTEGER NOT NULL, equity_cents INTEGER NOT NULL,
        bar_count INTEGER NOT NULL, result_json TEXT NOT NULL)""",
    """CREATE TABLE backtest_trades (
        trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL REFERENCES backtest_runs(run_id) ON DELETE CASCADE,
        symbol TEXT NOT NULL, side TEXT NOT NULL, signal_time_s INTEGER NOT NULL,
        fill_time_s INTEGER NOT NULL, fill_price REAL NOT NULL,
        quantity TEXT NOT NULL, notional_cents INTEGER NOT NULL,
        realized_pnl_cents INTEGER NOT NULL)""",
    "CREATE INDEX backtest_trades_run ON backtest_trades(run_id,trade_id)",
)
