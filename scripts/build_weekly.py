#!/usr/bin/env python3
"""Build a weekly Top from daily archives in the same ISO week.

Monday routine, from the repo root:

    python3 scripts/publish_boards.py

That also rebuilds archive HTML, sitemap.xml, sitemap.txt, llms.txt, and the
homepage SEO shell from data/daily-latest.json, then notifies IndexNow.
Do not stop after the JSON files:
index.html title, description, and JSON-LD dates are rewritten only by
scripts/build_homepage.py.

If an ISO week has only one daily archive, this script does not write a weekly
file and does not relabel a seed copy as a real week. The page keeps showing
the seed note when the JSON still has a seed object.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib


def weeks(directory: Path | None = None) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for day, _path, doc in boardlib.iter_daily_archives(directory):
        grouped.setdefault(boardlib.iso_week_id(day), []).append(doc)
    return grouped


def write_week(doc: dict, latest: bool) -> None:
    week_id = doc["period"]["iso_week"]
    archive = boardlib.WEEKLY_DIR / f"{week_id}.json"
    boardlib.dump_json(archive, doc)
    print(f"wrote {archive.relative_to(boardlib.ROOT)} days={doc['aggregation']['daily_dates']}")
    if latest:
        latest_path = boardlib.ROOT / "data" / "weekly-latest.json"
        boardlib.dump_json(latest_path, doc)
        print(f"wrote {latest_path.relative_to(boardlib.ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", help="Only this ISO week, for example 2026-W42")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    grouped = weeks()
    if args.week:
        grouped = {args.week: grouped.get(args.week, [])}
    if not grouped:
        print("no daily archives")
        return 0
    generated_at = boardlib.now_shanghai()
    built = []
    for week_id in sorted(grouped):
        docs = grouped[week_id]
        dates = sorted({str(doc.get("date"))[:10] for doc in docs})
        result = boardlib.aggregate_dailies(docs, generated_at)
        if result is None:
            print(
                f"{week_id}: {len(dates)} daily archive(s) ({', '.join(dates) or 'none'}). "
                "Need at least 2 distinct dates before writing an aggregated week. "
                "Existing weekly file, including a seed copy, was left unchanged."
            )
            continue
        built.append(result)
        if args.dry_run:
            print(
                f"dry-run {week_id}: {result['aggregation']['daily_dates']} "
                f"top={len(result['items'])} first={result['items'][0]['name']}"
            )
    if args.dry_run or not built:
        return 0
    latest_week = max(built, key=lambda doc: doc["period"]["end"])
    for doc in built:
        write_week(doc, latest=doc["period"]["iso_week"] == latest_week["period"]["iso_week"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
