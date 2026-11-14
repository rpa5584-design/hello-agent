"""Validated dashboard control requests."""
from typing import Literal
from pydantic import BaseModel, Field


class StartBody(BaseModel):
    symbols: list[Literal["BTC-USD", "ETH-USD"]] = Field(
        default=["BTC-USD", "ETH-USD"], min_length=1, max_length=2)
    seconds: int = Field(default=90, ge=10, le=120)


class HistoryBody(BaseModel):
    symbol: Literal["BTC-USD", "ETH-USD"] = "BTC-USD"
