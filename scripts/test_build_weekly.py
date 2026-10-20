#!/usr/bin/env python3
"""Checks for weekly aggregation. Uses the real archives plus a one-day fixture."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib


def fail(message: str) -> None:
    raise SystemExit(message)


def test_real_week() -> None:
    dailies = [
        doc
        for day, _path, doc in boardlib.iter_daily_archives()
        if boardlib.iso_week_id(day) == "2026-W42"
    ]
    doc = boardlib.aggregate_dailies(dailies, "2026-10-16T17:03:22+08:00")
    if not doc:
        fail("expected an aggregate for the October dailies")
    if "seed" in doc:
        fail("aggregated week must not carry seed")
    if doc["period"]["iso_week"] != "2026-W42":
        fail(doc["period"]["iso_week"])
    if doc["aggregation"]["daily_dates"] != ["2026-10-15", "2026-10-16", "2026-10-17", "2026-10-18"]:
        fail(str(doc["aggregation"]["daily_dates"]))
    if len(doc["items"]) != 20:
        fail(f"expected 20 items, got {len(doc['items'])}")
    per = {}
    for item in doc["items"]:
        per[item["platform"]] = per.get(item["platform"], 0) + 1
        if per[item["platform"]] > 6:
            fail("cap 6 violated")
        if not item.get("product_url"):
            fail("missing url")
    hug = next(item for item in doc["items"] if item["id"] == "dame-hug")
    if hug["appearances"] != 4:
        fail(f"hug appearances {hug['appearances']}")
    partial = [item for item in doc["items"] if item["appearances"] < 4]
    if not partial:
        fail("expected some products that did not appear on every day")
    ranks = [item["overall_rank"] for item in doc["items"]]
    if ranks != list(range(1, 21)):
        fail(str(ranks))
    print("real week ok", doc["items"][0]["name"], "appearances", doc["items"][0]["appearances"])


def test_single_day_is_not_a_week() -> None:
    dailies = [doc for day, _path, doc in boardlib.iter_daily_archives() if day.isoformat() == "2026-10-16"]
    if boardlib.aggregate_dailies(dailies, "2026-10-16T17:03:22+08:00") is not None:
        fail("one daily must not become an aggregated week")
    print("single day ok")


if __name__ == "__main__":
    test_real_week()
    test_single_day_is_not_a_week()
    print("ok")
