#!/usr/bin/env python3
"""Homepage shell stays aligned with data/daily-latest.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib
import build_homepage


def fail(message: str) -> None:
    raise SystemExit(message)


def ld_json(html: str) -> dict:
    match = re.search(
        r'<script type="application/ld\+json" id="ld-json">\s*(.*?)\s*</script>',
        html,
        re.S,
    )
    if not match:
        fail("missing ld-json")
    return json.loads(match.group(1))


def main() -> int:
    build_homepage.main()
    daily = boardlib.load_json(boardlib.ROOT / "data" / "daily-latest.json")
    weekly = boardlib.load_json(boardlib.ROOT / "data" / "weekly-latest.json")
    day = str(daily["date"])[:10]
    top = daily["items"][0]
    html = (boardlib.ROOT / "index.html").read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    if not title or day not in title.group(1):
        fail(f"title {title.group(1) if title else ''}")
    desc = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
    if not desc or day not in desc.group(1):
        fail("description date")
    graph = ld_json(html)
    webpage = next(node for node in graph["@graph"] if node.get("@type") == "WebPage")
    if webpage.get("dateModified") != day or not str(webpage.get("temporalCoverage", "")).startswith(day):
        fail(f"jsonld dates {webpage.get('dateModified')} {webpage.get('temporalCoverage')}")
    if webpage.get("isFamilyFriendly") is not False:
        fail("family friendly")
    item_list = next(node for node in graph["@graph"] if node.get("@type") == "ItemList")
    first = item_list["itemListElement"][0]["item"]
    if first.get("name") != top["name"]:
        fail(first.get("name") or "")
    if first.get("offers", {}).get("price") != f"{float(top['price']):.2f}":
        fail(str(first.get("offers")))
    if "FAQPage" not in {node.get("@type") for node in graph["@graph"]}:
        fail("missing FAQPage")
    if top["name"] not in html or f"{float(top['price']):.2f}" not in html:
        fail("summary missing top item")
    if "这份周榜是 2026-10-16" in html:
        fail("stale seed claim")
    dates = weekly["aggregation"]["daily_dates"]
    if dates[-1] not in html:
        fail("weekly summary missing last aggregated day")
    llms = (boardlib.ROOT / "llms.txt").read_text(encoding="utf-8")
    if day not in llms or weekly["period"]["iso_week"] not in llms:
        fail("llms dates")
    if "sitemap.txt" not in llms or "does not sell products" not in llms:
        fail("llms discovery")
    if "2026-10-15, 2026-10-16, and 2026-10-17 daily" in llms:
        fail("llms still describes a three-day week")
    if "seed" in weekly and "no seed" not in llms.lower() and "has no seed" not in llms:
        pass
    if not weekly.get("seed") and "no seed" not in llms.lower() and "has no seed" not in llms:
        fail("llms seed wording")
    robots = (boardlib.ROOT / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap: https://orangexie05.github.io/qing-bestsellers-top/sitemap.xml" not in robots:
        fail("robots sitemap")
    if 'type="text/plain" href="llms.txt"' not in html:
        fail("llms link")
    if 'name="msvalidate.01"' in html or 'name="baidu-site-verification"' in html:
        fail("verification meta present without a code")
    if "webmaster-verify" not in html:
        fail("webmaster hook")
    if 'name="rating" content="adult"' not in html:
        fail("rating")
    if "不直接售卖" not in html:
        fail("non-store positioning")
    sitemap = (boardlib.ROOT / "sitemap.xml").read_text(encoding="utf-8")
    if f"/archive/daily/{day}.html" not in sitemap:
        fail("sitemap daily")
    if f"/archive/weekly/{weekly['period']['iso_week']}.html" not in sitemap:
        fail("sitemap weekly")
    before = html
    build_homepage.main()
    after = (boardlib.ROOT / "index.html").read_text(encoding="utf-8")
    if before != after:
        fail("homepage rebuild is not idempotent")
    print("homepage shell ok", day, top["name"], first["offers"]["price"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
