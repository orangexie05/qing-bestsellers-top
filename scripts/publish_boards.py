#!/usr/bin/env python3
"""Publish a daily or weekly board without leaving the homepage shell behind.

From the repo root, after data/daily-latest.json and the matching
data/archive/daily/YYYY-MM-DD.json are in place:

    python3 scripts/publish_boards.py

The command rebuilds an aggregated weekly file when an ISO week has two or
more daily archives, then rewrites archive HTML, the homepage and by-platform
SEO shells, llms.txt, trust pages, and sitemap.xml. A daily publish that stops
before the homepage step is how index.html kept an older date.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_archive_html
import build_homepage
import build_sitemap
import build_trust_pages
import build_weekly


def main() -> int:
    build_weekly.main()
    build_archive_html.main()
    code = build_homepage.main()
    build_trust_pages.main()
    build_sitemap.main()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
