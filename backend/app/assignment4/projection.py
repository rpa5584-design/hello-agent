"""Pure receipt-prefix reducer. Volume remains explicitly unavailable."""
from collections import defaultdict

INTERVAL_MS = 60_000
LATENESS_MS = 10_000
REDUCER_VERSION = 1


def project(active: dict[str, dict], previous: list[dict],
            receipt_seq: int, received_at: str) -> list[dict]:
    grouped = defaultdict(list)
    maxima = {}
    for item in active.values():
        group = (item["source"], item["provenance"], item["symbol"])
        timestamp = item["source_time_ms"]
        maxima[group] = max(maxima.get(group, timestamp), timestamp)
        grouped[(*group, timestamp // INTERVAL_MS * INTERVAL_MS)].append(item)
    old = {key(c): c for c in previous}
    result = []
    for bucket, rows in sorted(grouped.items()):
        rows.sort(key=lambda r: (r["source_time_ms"], r["first_receipt_seq"]))
        prices = [r["price"] for r in rows]
        watermark = maxima[bucket[:3]] - LATENESS_MS
        base = {
            "source": bucket[0], "provenance": bucket[1], "symbol": bucket[2],
            "interval_ms": INTERVAL_MS, "bucket_start_ms": bucket[3],
            "open": prices[0], "high": max(prices), "low": min(prices), "close": prices[-1],
            "observation_count": len(rows), "volume": None,
            "volume_kind": "unavailable_unverified_source_semantics",
            "volume_coverage": "unknown", "source_complete": None,
            "app_completion": "interval_closed_by_app"
            if bucket[3] + INTERVAL_MS <= watermark else "forming",
            "version_ids": [r["version_id"] for r in rows],
            "reducer_version": REDUCER_VERSION,
        }
        prior = old.get(key(base))
        changed = prior is None or any(prior.get(k) != v for k, v in base.items())
        # Closure alone is not a late correction. A changed closed candle's contributors are.
        corrected = bool(prior and prior["app_completion"] == "interval_closed_by_app"
                         and any(prior[k] != base[k] for k in
                                 ("open", "high", "low", "close", "version_ids")))
        if not changed:
            result.append(prior)
            continue
        base.update({
            "projection_revision": prior["projection_revision"] + 1 if prior else 1,
            "late_corrected": corrected or bool(prior and prior["late_corrected"]),
            "last_corrected_at": received_at if corrected else
            (prior["last_corrected_at"] if prior else None),
            "as_of_receipt_seq": receipt_seq,
        })
        result.append(base)
    return result


def key(candle: dict) -> tuple:
    return (candle["source"], candle["provenance"], candle["symbol"],
            candle["bucket_start_ms"])
