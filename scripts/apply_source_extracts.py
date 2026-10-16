#!/usr/bin/env python3
"""Merge saved public-list extracts into the 2026-10-16 daily board.

Reads data/sources/*-2026-10-16.json (status ok, non-empty items). Does not
read the Taobao placeholder. Re-sorts with the published daily rule and writes
the same document to the latest, dated, and archive daily paths.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib

DATE = "2026-10-16"
FETCHED_NOTE = (
    "2026-10-16 later fetch of https://s.taobao.com/search returned the PC search shell "
    "(documentOnly/CSR, noscript asks for JavaScript). Static HTML had no item.taobao.com "
    "or detail.tmall.com URLs, no item ids, and no prices. Rows were not invented. "
    "Empty placeholder: data/sources/taobao_tmall.placeholder.json."
)


def skipped_rows() -> list[dict]:
    return [
        {
            "platform": "taobao_tmall",
            "status": "blocked",
            "note": FETCHED_NOTE,
        },
        {
            "platform": "gifts_18",
            "status": "blocked",
            "note": (
                "https://www.18gifts.com/bestsellers/ (本月最佳销量排行榜) returned a Cloudflare "
                "interstitial ('Just a moment...') on 2026-10-16. No product rows extracted."
            ),
        },
        {
            "platform": "lelo",
            "status": "not_found",
            "note": "https://www.lelo.com/best-sellers returned HTTP 404 on 2026-10-16. Not included.",
        },
        {
            "platform": "mysteryvibe",
            "status": "not_requested",
            "note": "Not fetched again on 2026-10-16. The 2026-10-15 attempt was HTTP 429. Not backfilled.",
        },
        {
            "platform": "pchome_24h",
            "status": "not_merged",
            "note": (
                "A PChome 24h category URL responded on 2026-10-16, but it was not a confirmed "
                "public bestseller list, so no rows were merged. The 2026-10-15 attempt was HTTP 429."
            ),
        },
    ]


def extracts() -> list[dict]:
    folder = boardlib.ROOT / "data" / "sources"
    docs = []
    for path in sorted(folder.glob(f"*-{DATE}.json")):
        doc = boardlib.load_json(path)
        if doc.get("status") != "ok" or not doc.get("items"):
            continue
        docs.append(doc)
    return docs


def build_item(source: dict, row: dict, scraped_at: str) -> dict:
    platform = source["platform"]
    url = row["product_url"]
    item = {
        "platform": platform,
        "store": source["store"],
        "rank": row["rank"],
        "name": row["name"],
        "product_url": url,
        "purchase_url": row.get("purchase_url") or url,
        "price": row["price"],
        "currency": row.get("currency") or "HKD",
        "reviews": {"rating": None, "count": None, "sample": None},
        "scraped_at": scraped_at,
        "id": boardlib.slug_id(platform, url, row.get("source_product_id")),
        "image": row.get("image"),
        "image_kind": row.get("image_kind") or ("official" if row.get("image") else "missing"),
        "list_url": source["list_url"],
        "note_key": "hk_list_sale" if row.get("compare_at_price") else "hk_list_order",
    }
    if row.get("compare_at_price"):
        item["compare_at_price"] = row["compare_at_price"]
    return item


def main() -> int:
    paths = [
        boardlib.ROOT / "data" / "daily-latest.json",
        boardlib.ROOT / "data" / f"daily-{DATE}.json",
        boardlib.ROOT / "data" / "archive" / "daily" / f"{DATE}.json",
    ]
    base = boardlib.load_json(paths[0])
    if str(base.get("date")) != DATE:
        raise SystemExit(f"daily-latest date is {base.get('date')}, expected {DATE}")
    seen = {boardlib.norm_url(item.get("product_url") or "") for item in base.get("items") or []}
    added = []
    supplement_at = None
    for source in extracts():
        supplement_at = source.get("fetched_at") or supplement_at
        for row in source["items"]:
            url = boardlib.norm_url(row["product_url"])
            if url in seen:
                continue
            seen.add(url)
            added.append(build_item(source, row, source.get("fetched_at") or boardlib.now_shanghai()))
    items = list(base.get("items") or []) + added
    # Dedupe again in case the base file itself repeats a URL.
    deduped = []
    seen_urls = set()
    for item in items:
        url = boardlib.norm_url(item.get("product_url") or "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        item = dict(item)
        item["product_url"] = url
        deduped.append(item)
    selected = boardlib.select_top(deduped, boardlib.daily_sort_key)
    included = []
    for item in selected:
        platform = item.get("platform")
        if platform and platform not in included:
            included.append(platform)
    when = supplement_at or boardlib.now_shanghai()
    base["generated_at"] = when
    base["as_of"] = DATE
    base["sort_rule"] = boardlib.DAILY_SORT_RULE
    base["sources_included"] = included
    base["sources_skipped"] = skipped_rows()
    base["items"] = selected
    base["supplement"] = {
        "at": when,
        "extracts": [source["platform"] for source in extracts()],
        "rows_added": len(added),
        "note": (
            "Same Shanghai date as the 10:59 scrape. Public HK category pages that returned "
            "product URL, name, and price were merged, then the published daily rule was re-run. "
            "Taobao/Tmall stayed empty. No rows were invented."
        ),
    }
    for path in paths:
        boardlib.dump_json(path, base)
        print(f"wrote {path.relative_to(boardlib.ROOT)} items={len(selected)} added={len(added)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
