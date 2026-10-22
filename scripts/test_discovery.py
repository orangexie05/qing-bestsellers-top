#!/usr/bin/env python3
"""IndexNow, sitemap.txt, robots allows, and empty Bing/Baidu hooks."""

from __future__ import annotations

import io
import json
import os
import re
import sys
import urllib.error
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib
import build_homepage
import build_sitemap
import build_trust_pages
import indexnow_ping
import publish_boards


def fail(message: str) -> None:
    raise SystemExit(message)


class Response:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def getcode(self) -> int:
        return self.status


def main() -> int:
    build_sitemap.main()
    daily = boardlib.load_json(boardlib.ROOT / "data" / "daily-latest.json")
    weekly = boardlib.load_json(boardlib.ROOT / "data" / "weekly-latest.json")
    day = str(daily["date"])[:10]
    week_id = weekly["period"]["iso_week"]

    key = indexnow_ping.load_key()
    path = indexnow_ping.key_path()
    raw = path.read_text(encoding="utf-8")
    if raw not in (key, key + "\n") or key != path.stem:
        fail("key file")
    body = indexnow_ping.payload()
    if body["host"] != "orangexie05.github.io":
        fail("host")
    if body["key"] != key:
        fail("key")
    expected_location = f"{boardlib.BASE}/{key}.txt"
    if body["keyLocation"] != expected_location or "/qing-bestsellers-top/" not in body["keyLocation"]:
        fail(body["keyLocation"])
    required = [
        f"{boardlib.BASE}/",
        f"{boardlib.BASE}/?board=weekly",
        f"{boardlib.BASE}/by-platform.html",
        f"{boardlib.BASE}/about.html",
        f"{boardlib.BASE}/faq.html",
        f"{boardlib.BASE}/method.html",
        f"{boardlib.BASE}/partners/",
        f"{boardlib.BASE}/llms.txt",
        f"{boardlib.BASE}/sitemap.xml",
        f"{boardlib.BASE}/sitemap.txt",
        f"{boardlib.BASE}/archive/daily/{day}.html",
        f"{boardlib.BASE}/archive/weekly/{week_id}.html",
    ]
    missing = [url for url in required if url not in body["urlList"]]
    if missing:
        fail("urlList missing " + ", ".join(missing))

    def forbidden(request, timeout=0):
        raise urllib.error.HTTPError(
            indexnow_ping.ENDPOINT,
            403,
            "Forbidden",
            hdrs=None,
            fp=io.BytesIO(b"key not found"),
        )

    indexnow_ping.submit(body, opener=forbidden)

    def down(request, timeout=0):
        raise RuntimeError("offline")

    if indexnow_ping.main(opener=down) != 0:
        fail("indexnow failure must not fail publish")

    previous = os.environ.get("QING_SKIP_INDEXNOW")
    os.environ["QING_SKIP_INDEXNOW"] = "1"
    called = []

    def should_not_run(request, timeout=0):
        called.append(request)
        return Response(200)

    try:
        if indexnow_ping.main(opener=should_not_run) != 0 or called:
            fail("skip flag")
    finally:
        if previous is None:
            os.environ.pop("QING_SKIP_INDEXNOW", None)
        else:
            os.environ["QING_SKIP_INDEXNOW"] = previous

    txt_path = boardlib.ROOT / "sitemap.txt"
    lines = [line for line in txt_path.read_text(encoding="utf-8").splitlines() if line]
    if len(lines) != len(set(lines)):
        fail("sitemap.txt duplicates")
    if f"{boardlib.BASE}/" not in lines:
        fail("sitemap.txt home")
    if f"{boardlib.BASE}/archive/daily/{day}.html" not in lines:
        fail("sitemap.txt daily")
    if f"{boardlib.BASE}/partners/" not in lines:
        fail("sitemap.txt partners")
    if f"{boardlib.BASE}/partners/?lang=en" not in lines:
        fail("sitemap.txt partners lang")
    if any(line.split("?", 1)[0].endswith(".json") or line.endswith(".txt") for line in lines):
        fail("sitemap.txt included a non-html url")
    xml = (boardlib.ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for line in lines:
        if escape(line) not in xml:
            fail("sitemap.txt url missing from xml: " + line)
    if "daily-latest.json" in txt_path.read_text(encoding="utf-8"):
        fail("json leaked into sitemap.txt")

    robots = (boardlib.ROOT / "robots.txt").read_text(encoding="utf-8")
    if "User-agent: *\nAllow: /" not in robots:
        fail("generic allow")
    if "Disallow" in robots:
        fail("unexpected disallow")
    for agent in (
        "Bingbot",
        "DuckDuckBot",
        "Slurp",
        "Baiduspider",
        "Yandex",
        "GPTBot",
        "ChatGPT-User",
        "ClaudeBot",
        "Anthropic-AI",
        "PerplexityBot",
        "Google-Extended",
        "Applebot-Extended",
    ):
        if f"User-agent: {agent}" not in robots:
            fail("missing " + agent)
    if "Sitemap: https://orangexie05.github.io/qing-bestsellers-top/sitemap.txt" not in robots:
        fail("robots sitemap.txt")
    if key not in robots:
        fail("robots key pointer")

    sample = '<meta name="google-site-verification" content="abc">'
    empty = build_homepage.apply_webmaster_hooks(sample, {})
    if 'name="msvalidate.01"' in empty or 'name="baidu-site-verification"' in empty or "webmaster-verify" not in empty:
        fail("empty hook")
    again = build_homepage.apply_webmaster_hooks(empty, {})
    if again != empty:
        fail("hook not idempotent")
    coded = build_homepage.apply_webmaster_hooks(
        sample,
        {"bing_site_verification": "A1B2C3D4E5F60718", "baidu_site_verification": ""},
    )
    if 'name="msvalidate.01" content="A1B2C3D4E5F60718"' not in coded:
        fail("bing meta")
    if 'name="baidu-site-verification"' in coded or "webmaster-verify" in coded:
        fail("empty baidu should stay absent")
    cleared = build_homepage.apply_webmaster_hooks(coded, {})
    if 'name="msvalidate.01"' in cleared:
        fail("cleared bing meta")
    try:
        build_homepage.verification_lines({"bing_site_verification": "not a real code"})
    except SystemExit:
        pass
    else:
        fail("bad token should be refused")

    config = json.loads((boardlib.ROOT / "seo.config.json").read_text(encoding="utf-8"))
    if config.get("bing_site_verification") != "95D87CF043D728963935C2E82EE51110":
        fail("committed bing verification token")
    if config.get("baidu_site_verification"):
        fail("baidu verification must stay empty")
    auth = (boardlib.ROOT / "BingSiteAuth.xml").read_text(encoding="utf-8")
    if "<user>95D87CF043D728963935C2E82EE51110</user>" not in auth:
        fail("BingSiteAuth.xml")

    def ok() -> int:
        return 0

    def boom() -> int:
        raise RuntimeError("indexnow down")

    publish_boards.build_weekly.main = ok
    publish_boards.build_archive_html.main = ok
    publish_boards.build_homepage.main = ok
    publish_boards.build_trust_pages.main = ok
    publish_boards.build_sitemap.main = ok
    publish_boards.indexnow_ping.main = boom
    if publish_boards.main() != 0:
        fail("publish must survive an IndexNow exception")

    html = (boardlib.ROOT / "index.html").read_text(encoding="utf-8")
    if "FAQPage" not in html or "不直接售卖" not in html:
        fail("homepage citation copy")
    if re.search(r"adultlist", html, re.I):
        fail("AdultList on homepage")
    if 'id="foot-partners" href="partners/"' not in html:
        fail("homepage partners link")
    footer = html.split("<footer", 1)[-1]
    if re.search(r"https?://[^\"']*(18\.network|pornplug|adultlist)", footer, re.I):
        fail("reciprocal link in homepage footer")
    about = (boardlib.ROOT / "about.html").read_text(encoding="utf-8")
    if 'href="partners/"' not in about or "青榜友链/合作目录页" not in about:
        fail("about partners link")
    build_trust_pages.main()
    again = build_trust_pages.main()
    if again != 0:
        fail("trust pages")
    partners = (boardlib.ROOT / "partners" / "index.html").read_text(encoding="utf-8")
    if build_trust_pages.main() != 0:
        fail("trust pages rerun")
    if partners != (boardlib.ROOT / "partners" / "index.html").read_text(encoding="utf-8"):
        fail("partners page is not idempotent")
    for needle in (
        'name="rating" content="adult"',
        'id="age-gate"',
        'class="is-gated"',
        'content="index,follow,max-snippet:-1"',
        'rel="canonical" href="https://orangexie05.github.io/qing-bestsellers-top/partners/"',
        "青榜友链/合作目录页",
        "Links we may add when directories require a reciprocal",
        "即将添加",
        "18.network",
        "PornPlug",
        "dofollow",
        'data-page="partners"',
        'data-root="../"',
        'href="../styles.css"',
        'href="../assets/app.js"',
    ):
        if needle not in partners:
            fail("partners page missing " + needle)
    if re.search(r'<a [^>]*href="https?://(?!fonts\.|www\.googletagmanager|github\.com)', partners):
        fail("unexpected outbound link on partners page")
    if re.search(r"adultlist", partners, re.I) and re.search(r'href="[^"]*adultlist', partners, re.I):
        fail("AdultList link on partners page")
    home_footer = html.split("<footer", 1)[-1]
    if home_footer.count("foot-partners") != 1:
        fail("partners footer link count")
    print("discovery ok", key, f"sitemap.txt={len(lines)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
