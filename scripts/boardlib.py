"""Shared board rules for the static Qing List site.

Daily sort matches the published sort_rule. Weekly aggregation is separate:
it only runs when an ISO week (Monday–Sunday, dates already in Asia/Shanghai)
has at least two daily archives. It does not invent products.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DAILY_DIR = ROOT / "data" / "archive" / "daily"
WEEKLY_DIR = ROOT / "data" / "archive" / "weekly"
BASE = "https://orangexie05.github.io/qing-bestsellers-top"

DAILY_SORT_RULE = (
    "dedupe by product_url; cap 6 per source; sort by source rank ASC, "
    "then rating DESC (nulls last), then review count DESC (nulls last), "
    "then platform id, then name; take Top 20"
)
WEEKLY_SORT_RULE = (
    "dedupe by product_url across daily archives in the same ISO week; "
    "score by appearances DESC, then mean source rank ASC, then best source rank ASC, "
    "then rating DESC (nulls last), then review count DESC (nulls last), "
    "then platform id, then name; cap 6 per source; take Top 20. "
    "Not a merchant-reported weekly sales total. Do not invent products."
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def iso_week_id(day: date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def week_bounds(day: date) -> tuple[date, date]:
    year, week, _ = day.isocalendar()
    return date.fromisocalendar(year, week, 1), date.fromisocalendar(year, week, 7)


def norm_url(url: str) -> str:
    raw = (url or "").strip()
    match = re.search(r"amazon\.com/(?:[^?#]*/)?dp/([A-Z0-9]{10})", raw, re.I)
    if match:
        return "https://www.amazon.com/dp/" + match.group(1).upper()
    raw = raw.split("#", 1)[0]
    if raw.endswith("/") and raw.count("/") > 3:
        raw = raw[:-1]
    return raw


def reviews_of(item: dict[str, Any]) -> tuple[float | None, float | None]:
    reviews = item.get("reviews") or {}
    rating = reviews.get("rating")
    count = reviews.get("count")
    rating_n = float(rating) if isinstance(rating, (int, float)) else None
    count_n = float(count) if isinstance(count, (int, float)) else None
    return rating_n, count_n


def daily_sort_key(item: dict[str, Any]) -> tuple:
    rating, count = reviews_of(item)
    rank = item.get("rank")
    return (
        rank if isinstance(rank, (int, float)) else 9999,
        0 if rating is not None else 1,
        -(rating or 0),
        0 if count is not None else 1,
        -(count or 0),
        item.get("platform") or "",
        item.get("name") or "",
    )


def select_top(items: list[dict[str, Any]], key, limit: int = 20, cap: int = 6) -> list[dict[str, Any]]:
    ordered = sorted(items, key=key)
    kept: list[dict[str, Any]] = []
    per_source: dict[str, int] = {}
    for item in ordered:
        platform = item.get("platform") or ""
        if per_source.get(platform, 0) >= cap:
            continue
        per_source[platform] = per_source.get(platform, 0) + 1
        kept.append(item)
        if len(kept) >= limit:
            break
    for index, item in enumerate(kept, 1):
        item["overall_rank"] = index
    return kept


def iter_daily_archives(directory: Path | None = None) -> list[tuple[date, Path, dict[str, Any]]]:
    folder = directory or DAILY_DIR
    found: list[tuple[date, Path, dict[str, Any]]] = []
    for path in sorted(folder.glob("*.json")):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.stem):
            continue
        doc = load_json(path)
        if doc.get("board") not in (None, "daily"):
            continue
        day = parse_date(str(doc.get("date") or path.stem))
        found.append((day, path, doc))
    return found


def weekly_sort_key(item: dict[str, Any]) -> tuple:
    rating, count = reviews_of(item)
    return (
        -int(item.get("appearances") or 0),
        float(item.get("mean_source_rank") or 9999),
        float(item.get("best_source_rank") or item.get("rank") or 9999),
        0 if rating is not None else 1,
        -(rating or 0),
        0 if count is not None else 1,
        -(count or 0),
        item.get("platform") or "",
        item.get("name") or "",
    )


def aggregate_dailies(dailies: list[dict[str, Any]], generated_at: str) -> dict[str, Any] | None:
    """Build one weekly document from two or more daily documents. Returns None below that."""
    usable = [doc for doc in dailies if (doc.get("items") or [])]
    dates = sorted({str(doc.get("date"))[:10] for doc in usable if doc.get("date")})
    if len(dates) < 2:
        return None
    start, end = week_bounds(parse_date(dates[0]))
    week_id = iso_week_id(parse_date(dates[0]))
    by_url: dict[str, dict[str, Any]] = {}
    for doc in sorted(usable, key=lambda item: str(item.get("date"))):
        day = str(doc.get("date"))[:10]
        for raw in doc.get("items") or []:
            url = norm_url(raw.get("product_url") or "")
            if not url:
                continue
            rank = raw.get("rank")
            rank_n = int(rank) if isinstance(rank, (int, float)) else None
            slot = by_url.get(url)
            if slot is None:
                slot = {
                    "latest": raw,
                    "latest_day": day,
                    "days": [],
                    "ranks": {},
                }
                by_url[url] = slot
            if day not in slot["days"]:
                slot["days"].append(day)
            if rank_n is not None:
                slot["ranks"][day] = rank_n
            if day >= slot["latest_day"]:
                slot["latest"] = raw
                slot["latest_day"] = day

    pooled: list[dict[str, Any]] = []
    for url, slot in by_url.items():
        ranks = [slot["ranks"][day] for day in slot["days"] if day in slot["ranks"]]
        if not ranks:
            continue
        latest = dict(slot["latest"])
        latest.pop("overall_rank", None)
        latest.pop("seed", None)
        best = min(ranks)
        latest["product_url"] = url
        if latest.get("purchase_url"):
            latest["purchase_url"] = norm_url(latest["purchase_url"]) or latest["purchase_url"]
        latest["rank"] = best
        latest["best_source_rank"] = best
        latest["mean_source_rank"] = round(sum(ranks) / len(ranks), 2)
        latest["appearances"] = len(slot["days"])
        latest["appearance_dates"] = list(slot["days"])
        latest["source_ranks"] = {day: slot["ranks"][day] for day in slot["days"] if day in slot["ranks"]}
        pooled.append(latest)

    items = select_top(pooled, weekly_sort_key)
    latest_daily = max(usable, key=lambda item: str(item.get("date")))
    sources = []
    for item in items:
        platform = item.get("platform")
        if platform and platform not in sources:
            sources.append(platform)
    skipped = _merge_skipped(usable)
    omissions = _merge_omissions(usable)
    as_of = dates[-1]
    return {
        "board": "weekly",
        "generated_at": generated_at,
        "date": as_of,
        "as_of": as_of,
        "timezone": "Asia/Shanghai",
        "period": {
            "kind": "week",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "label": f"{start.isoformat()} – {end.isoformat()}",
            "iso_week": week_id,
            "week_starts_on": "monday",
            "timezone": "Asia/Shanghai",
        },
        "aggregation": {
            "method": "appearances_then_mean_source_rank",
            "min_days": 2,
            "daily_dates": dates,
            "daily_count": len(dates),
            "note": (
                f"Built from {len(dates)} daily archives in {week_id} "
                f"({', '.join(dates)}). Deduped by product_url. "
                "Ranked by days appeared, then mean source rank, then best source rank, "
                "then rating, then review count. Not a merchant-reported weekly sales total. "
                "Does not invent products. No seed field, because this is not a one-day copy."
            ),
        },
        "publish": {
            "schema_version": 1,
            "latest": "data/weekly-latest.json",
            "archive": f"data/archive/weekly/{week_id}.json",
            "archive_pattern": "data/archive/weekly/YYYY-Www.json",
            "timezone": "Asia/Shanghai",
            "overwrite": (
                "When at least two data/archive/daily/YYYY-MM-DD.json files fall in the same "
                "ISO week, scripts/build_weekly.py replaces data/weekly-latest.json and "
                "data/archive/weekly/YYYY-Www.json with this aggregate. "
                "When only one daily exists, leave any seed weekly in place and do not pretend it is a tally. "
                "Do not invent products."
            ),
        },
        "category": latest_daily.get("category") or "adult_sex_toys_sexual_wellness",
        "category_zh": latest_daily.get("category_zh") or "性工具 / 情趣用品",
        "sort_rule": WEEKLY_SORT_RULE,
        "sources_included": sources,
        "sources_skipped": skipped,
        "omissions": omissions,
        "items": items,
    }


def _merge_skipped(dailies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(dailies, key=lambda item: str(item.get("date")))
    merged: dict[str, dict[str, Any]] = {}
    for doc in ordered:
        day = str(doc.get("date"))[:10]
        for row in doc.get("sources_skipped") or []:
            platform = row.get("platform")
            if not platform:
                continue
            note = row.get("note") or ""
            status = row.get("status") or ""
            current = merged.get(platform)
            if current is None:
                merged[platform] = {
                    "platform": platform,
                    "status": status,
                    "note": f"{day}: {note}".strip(),
                }
                continue
            if status and status != current.get("status"):
                current["status"] = status
            if note and note not in current["note"]:
                current["note"] = current["note"] + f" | {day}: {note}"
    return list(merged.values())


def _merge_omissions(dailies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    rows = []
    for doc in sorted(dailies, key=lambda item: str(item.get("date"))):
        for row in doc.get("omissions") or []:
            key = (row.get("platform"), row.get("name"))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def slug_id(platform: str, url: str, source_id: str | None) -> str:
    path = (url or "").rstrip("/").split("/products/")[-1]
    try:
        from urllib.parse import unquote
        path = unquote(path)
    except Exception:
        pass
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    if len(slug) < 3:
        slug = re.sub(r"[^a-z0-9]+", "-", (source_id or "item").lower()).strip("-") or "item"
    return f"{platform}-{slug[:48].strip('-')}"


def price_string(price: Any) -> str | None:
    try:
        return f"{float(price):.2f}"
    except (TypeError, ValueError):
        return None


def product_node(item: dict[str, Any], products: dict[str, Any] | None = None) -> dict[str, Any]:
    products = products or {}
    copy = products.get(item.get("id") or "", {})
    node: dict[str, Any] = {
        "@type": "Product",
        "name": item.get("name"),
        "url": item.get("product_url"),
        "brand": {"@type": "Brand", "name": item.get("store")},
    }
    image = item.get("image")
    if image:
        node["image"] = image if str(image).startswith("http") else BASE + "/" + str(image).lstrip("/")
    display = copy.get("display")
    if display and display != item.get("name"):
        node["alternateName"] = display
    sku = None
    match = re.search(r"/dp/([A-Z0-9]{10})(?:[/?#]|$)", item.get("product_url") or "")
    if match:
        sku = match.group(1)
    if sku:
        node["sku"] = sku
    price = price_string(item.get("price"))
    if price and item.get("currency"):
        node["offers"] = {
            "@type": "Offer",
            "url": item.get("purchase_url") or item.get("product_url"),
            "priceCurrency": item.get("currency"),
            "price": price,
        }
    reviews = item.get("reviews") or {}
    if isinstance(reviews.get("rating"), (int, float)) and isinstance(reviews.get("count"), (int, float)) and reviews["count"] > 0:
        node["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": reviews["rating"],
            "bestRating": 5,
            "ratingCount": reviews["count"],
        }
    return node


def money(price: Any, currency: str | None) -> str:
    text = price_string(price)
    if text is None:
        return ""
    if currency == "USD":
        return "US$" + text
    if currency == "HKD":
        return "HK$" + text
    if currency == "CNY":
        return "CN¥" + text
    return f"{currency or ''} {text}".strip()


def html_escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def now_shanghai() -> str:
    # Fixed offset; the site's board dates are Asia/Shanghai wall times.
    from datetime import timedelta, timezone
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
