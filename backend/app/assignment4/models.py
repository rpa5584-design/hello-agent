"""Validated domain values. No Yahoo adapter or inferred source trade IDs."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from typing import Literal

Provenance = Literal["fixture", "yahoo_stream"]
SYMBOLS = {"AAPL", "MSFT", "BTC-USD", "ETH-USD"}
MIN_TIME_MS = 946684800000  # 2000-01-01; fixed milliseconds contract, never auto-detect.


def json_text(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def utc_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("receipt time must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()


def integer(value: object, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    if isinstance(value, str):
        if not value.isascii() or not value.isdigit():
            raise ValueError(f"{name} must be an unsigned integer string")
        value = int(value)
    if not isinstance(value, int) or not 0 <= value <= 2**63 - 1:
        raise ValueError(f"{name} must be a nonnegative SQLite integer")
    return value


@dataclass(frozen=True)
class Observation:
    source: str
    provenance: Provenance
    symbol: str
    source_time_ms: int
    price: float
    exchange: str | None
    quote_type: int | None
    market_hours: int | None
    currency: str | None
    day_volume: int | None
    last_size: int | None
    vol_24hr: int | None

    @property
    def slot_key(self) -> str:
        return json_text([self.source, self.provenance, self.symbol, self.source_time_ms,
                          self.exchange, self.quote_type, self.market_hours])

    def as_dict(self) -> dict:
        return asdict(self)


def normalize(payload: dict, provenance: Provenance, received_at: datetime) -> Observation:
    """Caller explicitly supplies decoded milliseconds; not evidence of Yahoo units."""
    utc_text(received_at)
    if provenance not in ("fixture", "yahoo_stream"):
        raise ValueError("unsupported ingestion provenance")
    if not isinstance(payload.get("id"), str) or payload["id"] not in SYMBOLS:
        raise ValueError("symbol must be AAPL, MSFT, BTC-USD or ETH-USD")
    timestamp = integer(payload.get("time"), "time")
    if timestamp < MIN_TIME_MS or timestamp > int(received_at.timestamp() * 1000) + 5000:
        raise ValueError("time must be plausible Unix milliseconds, at most 5s in future")
    price = payload.get("price")
    if isinstance(price, bool) or not isinstance(price, (float, int)):
        raise ValueError("price must be a finite positive number")
    try:
        price = float(price)
    except (ValueError, OverflowError):
        raise ValueError("price must be a finite positive number") from None
    if not math.isfinite(price) or price <= 0:
        raise ValueError("price must be a finite positive number")
    strings = {}
    for name in ("exchange", "currency"):
        value = payload.get(name)
        if value is not None and (not isinstance(value, str) or not 1 <= len(value) <= 32):
            raise ValueError(f"{name} must be a nonempty short string")
        strings[name] = value
    numbers = {}
    for name in ("quote_type", "market_hours", "day_volume", "last_size", "vol_24hr"):
        value = payload.get(name)
        numbers[name] = None if value is None else integer(value, name)
    return Observation(
        source="fixture" if provenance == "fixture" else "yahoo",
        provenance=provenance, symbol=payload["id"], source_time_ms=timestamp,
        price=price, **strings, **numbers,
    )


def canonical_payload(payload: dict, observation: Observation) -> str:
    """Normalize known numeric representations; preserve extra fields and absence."""
    values = observation.as_dict()
    canonical = dict(payload)
    canonical["time"] = values["source_time_ms"]
    canonical["price"] = values["price"]
    for name in ("quote_type", "market_hours", "day_volume", "last_size", "vol_24hr"):
        if name in canonical:
            canonical[name] = values[name]
    return json_text(canonical)
