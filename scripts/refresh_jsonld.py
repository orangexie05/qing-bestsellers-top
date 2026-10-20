#!/usr/bin/env python3
"""Rebuild live board SEO shells from data/daily-latest.json.

This used to replace only ItemList entries. That left <title>, descriptions,
Open Graph, Twitter, and WebPage dateModified / temporalCoverage on an older
day. It now runs scripts/build_homepage.py, which rewrites those fields and
llms.txt as well. A full publish is scripts/publish_boards.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_homepage import main


if __name__ == "__main__":
    raise SystemExit(main())
