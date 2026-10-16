#!/usr/bin/env python3
"""Replace ItemList entries in the live board pages from daily-latest.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib

PAGES = [
    boardlib.ROOT / "index.html",
    boardlib.ROOT / "by-platform.html",
]


def main() -> int:
    products = boardlib.load_json(boardlib.ROOT / "i18n" / "zh-CN.json").get("products") or {}
    daily = boardlib.load_json(boardlib.ROOT / "data" / "daily-latest.json")
    elements = []
    for item in daily.get("items") or []:
        elements.append({
            "@type": "ListItem",
            "position": item.get("overall_rank"),
            "item": boardlib.product_node(item, products),
        })
    pattern = re.compile(
        r'(<script type="application/ld\+json" id="ld-json">\s*)(.*?)(\s*</script>)',
        re.S,
    )
    for path in PAGES:
        html = path.read_text(encoding="utf-8")
        match = pattern.search(html)
        if not match:
            raise SystemExit(f"no ld-json in {path}")
        graph = json.loads(match.group(2))
        found = False
        for node in graph.get("@graph", []):
            if node.get("@type") == "ItemList":
                node["itemListElement"] = elements
                node["numberOfItems"] = len(elements)
                found = True
        if not found:
            raise SystemExit(f"no ItemList in {path}")
        rendered = json.dumps(graph, ensure_ascii=False, indent=2)
        html = html[: match.start(2)] + "\n" + rendered + "\n" + html[match.end(2) :]
        path.write_text(html, encoding="utf-8")
        print(f"updated ItemList in {path.name} ({len(elements)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
