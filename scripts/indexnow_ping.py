#!/usr/bin/env python3
"""Tell IndexNow which URLs a board publish just refreshed.

This site is a GitHub project Pages site under /qing-bestsellers-top/, so the
key file cannot live at the host root. The committed file is the only repo-root
*.txt whose name is 8–128 hex characters. Submissions pass keyLocation to

    https://orangexie05.github.io/qing-bestsellers-top/<key>.txt

A failed POST is logged and does not fail the publish. Set QING_SKIP_INDEXNOW=1
to skip the network call (local rebuilds and tests).
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib

HOST = "orangexie05.github.io"
ENDPOINT = "https://api.indexnow.org/indexnow"
KEY_FILE_NAME = re.compile(r"^[0-9a-f]{8,128}\.txt$")
DAY_NAME = re.compile(r"\d{4}-\d{2}-\d{2}")
WEEK_NAME = re.compile(r"\d{4}-W\d{2}")


def key_path() -> Path:
    matches = sorted(path for path in boardlib.ROOT.glob("*.txt") if KEY_FILE_NAME.fullmatch(path.name))
    if len(matches) != 1:
        names = [path.name for path in matches]
        raise RuntimeError(f"expected one IndexNow key file at the repo root, found {names}")
    return matches[0]


def load_key() -> str:
    path = key_path()
    text = path.read_text(encoding="utf-8")
    key = text.strip()
    if text not in (key, key + "\n") or key != path.stem:
        raise RuntimeError(f"{path.name} must contain only the key, matching the filename")
    return key


def changed_urls(daily: dict | None = None, weekly: dict | None = None) -> list[str]:
    """URLs this publish rewrites. Historical archives stay out of the ping."""
    if daily is None:
        daily = boardlib.load_json(boardlib.ROOT / "data" / "daily-latest.json")
    if weekly is None:
        weekly_path = boardlib.ROOT / "data" / "weekly-latest.json"
        weekly = boardlib.load_json(weekly_path) if weekly_path.exists() else {}
    day = str(daily.get("date") or daily.get("as_of") or "")[:10]
    week_id = str((weekly.get("period") or {}).get("iso_week") or "")
    urls = [
        f"{boardlib.BASE}/",
        f"{boardlib.BASE}/?board=weekly",
        f"{boardlib.BASE}/by-platform.html",
        f"{boardlib.BASE}/about.html",
        f"{boardlib.BASE}/faq.html",
        f"{boardlib.BASE}/method.html",
        f"{boardlib.BASE}/privacy.html",
        f"{boardlib.BASE}/contact.html",
        f"{boardlib.BASE}/archive/index.html",
        f"{boardlib.BASE}/llms.txt",
        f"{boardlib.BASE}/sitemap.xml",
        f"{boardlib.BASE}/sitemap.txt",
    ]
    if DAY_NAME.fullmatch(day):
        urls.append(f"{boardlib.BASE}/archive/daily/{day}.html")
    if WEEK_NAME.fullmatch(week_id):
        urls.append(f"{boardlib.BASE}/archive/weekly/{week_id}.html")
    deduped = []
    seen = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


def payload(urls: list[str] | None = None) -> dict:
    key = load_key()
    url_list = list(urls if urls is not None else changed_urls())
    prefix = f"https://{HOST}/"
    if any(not url.startswith(prefix) for url in url_list):
        raise RuntimeError("IndexNow urlList must use the site host")
    return {
        "host": HOST,
        "key": key,
        "keyLocation": f"{boardlib.BASE}/{key}.txt",
        "urlList": url_list,
    }


def submit(body: dict, opener=None) -> None:
    opener = opener or urllib.request.urlopen
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "QingListIndexNow/1.0",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=20) as response:
            status = getattr(response, "status", None) or response.getcode()
            print(f"indexnow {status} urls={len(body['urlList'])}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300].strip()
        print(f"indexnow HTTP {exc.code}: {detail}", file=sys.stderr)
    except Exception as exc:
        print(f"indexnow skipped: {exc}", file=sys.stderr)


def main(opener=None) -> int:
    if os.environ.get("QING_SKIP_INDEXNOW") == "1":
        print("indexnow skipped (QING_SKIP_INDEXNOW=1)")
        return 0
    try:
        submit(payload(), opener=opener)
    except Exception as exc:
        print(f"indexnow skipped: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
