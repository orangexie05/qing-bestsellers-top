#!/usr/bin/env python3
"""Rebuild sitemap.xml from the live pages, language variants, and JSON boards."""

from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib

BASE = boardlib.BASE
LANGS = ["zh-CN", "en", "ja", "es"]


def loc(path: str, query: list[str]) -> str:
    url = BASE + path
    if query:
        url += "?" + "&".join(query)
    return url


def hreflang_block(path: str, extra: list[str] | None = None) -> str:
    extra = list(extra or [])
    lines = []
    for code in LANGS + ["x-default"]:
        target = "zh-CN" if code in ("zh-CN", "x-default") else code
        query = list(extra)
        if target != "zh-CN":
            query.append("lang=" + target)
        href = loc(path, query)
        lines.append(f'    <xhtml:link rel="alternate" hreflang="{code}" href="{escape(href)}"/>')
    return "\n".join(lines)


def url_node(path: str, lastmod: str, changefreq: str, priority: str, extra: list[str] | None = None, lang: str = "zh-CN") -> str:
    query = list(extra or [])
    if lang != "zh-CN":
        query.append("lang=" + lang)
    # Language-specific priority is a step below the zh-CN URL.
    pri = priority
    if lang != "zh-CN":
        try:
            pri = f"{max(float(priority) - 0.1, 0.1):.1f}"
        except ValueError:
            pri = priority
    return (
        "  <url>\n"
        f"    <loc>{escape(loc(path, query))}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{pri}</priority>\n"
        f"{hreflang_block(path, extra)}\n"
        "  </url>"
    )


def page_set(path: str, lastmod: str, changefreq: str, priority: str, extra: list[str] | None = None) -> list[str]:
    return [url_node(path, lastmod, changefreq, priority, extra, lang) for lang in LANGS]


def plain(path: str, lastmod: str, changefreq: str, priority: str) -> str:
    return (
        "  <url>\n"
        f"    <loc>{escape(BASE + path)}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        "  </url>"
    )


def main() -> int:
    lastmod = "2026-10-17"
    chunks: list[str] = []
    chunks += page_set("/", lastmod, "daily", "1.0")
    chunks += page_set("/", lastmod, "weekly", "0.9", ["board=weekly"])
    chunks += page_set("/by-platform.html", lastmod, "daily", "0.8")
    chunks += page_set("/by-platform.html", lastmod, "weekly", "0.7", ["board=weekly"])
    chunks += page_set("/archive/index.html", lastmod, "weekly", "0.6")
    for day, _path, doc in boardlib.iter_daily_archives():
        chunks += page_set(f"/archive/daily/{day.isoformat()}.html", day.isoformat(), "monthly", "0.5")
    weekly_dir = boardlib.ROOT / "data" / "archive" / "weekly"
    for path in sorted(weekly_dir.glob("*.json")):
        doc = boardlib.load_json(path)
        stamp = str(doc.get("as_of") or doc.get("date") or lastmod)[:10]
        chunks += page_set(f"/archive/weekly/{path.stem}.html", stamp, "monthly", "0.5")
    for name, freq, pri in (
        ("/about.html", "monthly", "0.6"),
        ("/method.html", "monthly", "0.6"),
        ("/faq.html", "monthly", "0.6"),
        ("/privacy.html", "monthly", "0.4"),
        ("/contact.html", "monthly", "0.4"),
    ):
        chunks += page_set(name, lastmod, freq, pri)
    chunks.append(plain("/llms.txt", lastmod, "monthly", "0.3"))
    for rel, pri in (
        ("/data.json", "0.3"),
        ("/data/daily-latest.json", "0.4"),
        ("/data/weekly-latest.json", "0.4"),
        ("/data/daily-2026-10-16.json", "0.4"),
        ("/data/daily-2026-10-17.json", "0.4"),
    ):
        chunks.append(plain(rel, lastmod, "daily", pri))
    for day, path, _doc in boardlib.iter_daily_archives():
        chunks.append(plain(f"/data/archive/daily/{path.name}", day.isoformat(), "monthly", "0.2"))
    for path in sorted(weekly_dir.glob("*.json")):
        doc = boardlib.load_json(path)
        stamp = str(doc.get("as_of") or lastmod)[:10]
        chunks.append(plain(f"/data/archive/weekly/{path.name}", stamp, "monthly", "0.2"))
    body = "\n".join(chunks)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!--
  Adults-only charts. zh-CN is the URL with no lang parameter and is also x-default.
  Daily is the default (no board parameter). Weekly is the same path plus ?board=weekly.
  Archive HTML uses the same ?lang= alternates. Each URL repeats only the hreflang set for that page.
-->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
{body}
</urlset>
"""
    dest = boardlib.ROOT / "sitemap.xml"
    dest.write_text(xml, encoding="utf-8")
    print(f"wrote sitemap.xml ({xml.count('<url>')} urls)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
