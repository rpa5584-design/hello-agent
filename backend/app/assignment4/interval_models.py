"""One provider interval record supplies BOTH OHLC and volume."""
from dataclasses import dataclass
from datetime import datetime
import math

from .models import integer, utc_text, json_text

INTERVAL_S = 60


@dataclass(frozen=True)
class IntervalBar:
    symbol: str
    source_time_s: int
    open: float
    high: float
    low: float
    close: float
    volume: int | float | None
    app_completion: str

    def state(self) -> dict:
        return {**self.__dict__, "source": "Yahoo Finance interval OHLCV",
                "interval_s": INTERVAL_S, "volume_units": "provider-reported; unverified",
                "volume_quality": "unknown" if self.volume is None else
                ("reported_zero" if self.volume == 0 else "reported"),
                "coverage": "returned interval snapshot; completeness unverified",
                "source_complete": None}


def normalize_bar(symbol: str, raw: dict, retrieved_at: datetime) -> IntervalBar:
    utc_text(retrieved_at)
    if symbol not in ("BTC-USD", "ETH-USD", "AAPL", "MSFT"):
        raise ValueError("unsupported interval symbol")
    if not isinstance(raw, dict):
        raise ValueError("interval record must be an object")
    timestamp = integer(raw.get("source_time_s"), "source_time_s")
    if timestamp < 946684800 or timestamp > retrieved_at.timestamp() + 5:
        raise ValueError("interval timestamp must be plausible Unix seconds")
    if timestamp % INTERVAL_S:
        raise ValueError("interval timestamp is not aligned to 60 seconds")
    prices = {}
    for name in ("open", "high", "low", "close"):
        value = raw.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be finite positive OHLC")
        try:
            price = float(value)
        except OverflowError:
            raise ValueError(f"{name} must be finite positive OHLC") from None
        if not math.isfinite(price) or price <= 0:
            raise ValueError(f"{name} must be finite positive OHLC")
        prices[name] = price
    if prices["high"] < max(prices.values()) or prices["low"] > min(prices.values()):
        raise ValueError("OHLC range does not contain open/close")
    volume = raw.get("volume")
    if volume is not None:
        if isinstance(volume, bool) or not isinstance(volume, (int, float)):
            raise ValueError("volume must be a finite nonnegative reported number")
        try:
            valid_volume = math.isfinite(volume) and volume >= 0
        except OverflowError:
            valid_volume = False
        if not valid_volume:
            raise ValueError("volume must be a finite nonnegative reported number")
    completion = "interval_elapsed_by_app" if timestamp + INTERVAL_S <= retrieved_at.timestamp() else "forming"
    return IntervalBar(symbol, timestamp, **prices, volume=volume, app_completion=completion)


def canonical_bar(bar: IntervalBar, raw: dict) -> str:
    return json_text({"normalized": bar.state(), "raw": raw})
