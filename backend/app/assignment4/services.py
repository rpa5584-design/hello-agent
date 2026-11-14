"""Domain service entry points; no provider dependencies or startup side effects."""
from datetime import datetime
from pathlib import Path

from .controller import MarketStore
from .models import Provenance


class MarketService:
    def __init__(self, database_path: Path):
        self.store = MarketStore(database_path)

    def record(self, payload: dict, *, provenance: Provenance, received_at: datetime) -> dict:
        return self.store.ingest(payload, provenance=provenance, received_at=received_at)

    def snapshot(self) -> dict:
        return self.store.snapshot()

    def replay(self, through: int | None = None) -> dict:
        return self.store.replay(through=through)

    def receipts(self, after: int = 0, limit: int = 100) -> list[dict]:
        return self.store.receipts(after=after, limit=limit)
