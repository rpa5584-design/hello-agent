"""Explicit opt-in evidence capture. Never imported by app startup; no database use."""
import argparse
import asyncio
from importlib.metadata import version
import json
from pathlib import Path

from .yahoo_stream import YahooStreamAdapter


async def capture_file(path: Path, seconds: float, symbols: list[str]) -> dict:
    # Exclusive creation prevents overwriting prior actual evidence.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        header = {"kind": "capture_header", "source": "Yahoo Finance via yfinance",
                  "package_version": version("yfinance"), "symbols": symbols,
                  "max_capture_seconds": seconds, "max_reconnects": 0,
                  "raw_format": "redacted decoded protobuf dictionary; not raw network frames",
                  "historical_requests_in_this_process": 0}
        output.write(json.dumps(header) + "\n")
        output.flush()

        def sink(event: dict) -> None:
            output.write(json.dumps(event, allow_nan=False) + "\n")
            output.flush()

        result = await YahooStreamAdapter().capture(symbols, sink, seconds=seconds)
        summary = {"kind": "capture_summary", **result.as_dict()}
        output.write(json.dumps(summary) + "\n")
        output.flush()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Opt-in bounded Yahoo stream evidence")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--symbols", nargs="+", default=["BTC-USD", "ETH-USD"])
    args = parser.parse_args()
    if not 0 < args.seconds <= 110 or not 1 <= len(args.symbols) <= 2:
        parser.error("limits: <=110 seconds plus <=3s cleanup, <=2 instruments")
    print(json.dumps(asyncio.run(capture_file(args.output, args.seconds, args.symbols))))


if __name__ == "__main__":
    main()
