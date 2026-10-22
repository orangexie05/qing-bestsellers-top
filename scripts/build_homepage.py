#!/usr/bin/env python3
"""Rebuild the homepage and by-platform SEO shells from the latest boards.

Crawlers that do not run app.js read index.html as written. Titles, meta
descriptions, Open Graph, Twitter cards, JSON-LD dateModified /
temporalCoverage, the ItemList, and the prerendered summary must follow
data/daily-latest.json. Weekly strings follow data/weekly-latest.json.

    python3 scripts/build_homepage.py

Prefer scripts/publish_boards.py after a daily or weekly JSON publish so
archive HTML, the sitemap, llms.txt, and these shells stay on the same day.
The homepage head also keeps a link to llms.txt and the Bing/Baidu
verification hook from seo.config.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib

LANGS = ("zh-CN", "en", "ja", "es")
DATE = r"20\d\d-\d\d-\d\d"
LIST_SEP = r"(?:, and |, y | 与 | y |、|, )"
LIST_RE = re.compile(rf"{DATE}(?:(?:{LIST_SEP}){DATE})+")
PROSE_HTML = ("faq.html", "method.html", "about.html", "privacy.html", "contact.html")
INFO_HTML = PROSE_HTML + ("archive/index.html",)
OVERSEAS = ("amazon_us", "dame", "lovense", "we_vibe", "womanizer")
HONG_KONG = ("waddy_store", "sistalk_hk", "lesplay_hk", "sexconcept_hk")
LABELS = {
    "zh-CN": {
        "amazon_us": "Amazon 美国站",
        "dame": "Dame",
        "lovense": "Lovense",
        "we_vibe": "We-Vibe",
        "womanizer": "Womanizer",
        "waddy_store": "Waddy",
        "sistalk_hk": "SISTALK",
        "lesplay_hk": "Les'Play",
        "sexconcept_hk": "Sex Concept",
    },
    "en": {
        "amazon_us": "Amazon.com",
        "dame": "Dame",
        "lovense": "Lovense",
        "we_vibe": "We-Vibe",
        "womanizer": "Womanizer",
        "waddy_store": "Waddy",
        "sistalk_hk": "SISTALK",
        "lesplay_hk": "Les'Play",
        "sexconcept_hk": "Sex Concept",
    },
    "ja": {
        "amazon_us": "Amazon",
        "dame": "Dame",
        "lovense": "Lovense",
        "we_vibe": "We-Vibe",
        "womanizer": "Womanizer",
        "waddy_store": "Waddy",
        "sistalk_hk": "SISTALK",
        "lesplay_hk": "Les'Play",
        "sexconcept_hk": "Sex Concept",
    },
    "es": {
        "amazon_us": "Amazon",
        "dame": "Dame",
        "lovense": "Lovense",
        "we_vibe": "We-Vibe",
        "womanizer": "Womanizer",
        "waddy_store": "Waddy",
        "sistalk_hk": "SISTALK",
        "lesplay_hk": "Les'Play",
        "sexconcept_hk": "Sex Concept",
    },
}
SKIP_LABEL = {
    "taobao_tmall": "Taobao / Tmall",
    "gifts_18": "18 Gifts",
    "lelo": "LELO",
    "mysteryvibe": "MysteryVibe",
    "pchome_24h": "PChome 24h",
}
EN_MONTHS = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
ES_MONTHS = (
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
CN_COUNT = "零一二三四五六七八九"


def fill(template: str, values: dict) -> str:
    def repl(match: re.Match) -> str:
        value = values.get(match.group(1))
        return "" if value is None else str(value)

    return re.sub(r"\{(\w+)\}", repl, template or "")


def esc(value) -> str:
    return boardlib.html_escape("" if value is None else str(value))


def period_token(doc: dict) -> str:
    period = doc.get("period") or {}
    start, end = period.get("start"), period.get("end")
    if start and end and start != end:
        return f"{start}–{end}"
    return str(doc.get("date") or period.get("label") or start or "")


def top_item(doc: dict) -> dict | None:
    best = None
    for item in doc.get("items") or []:
        rank = item.get("overall_rank") or 9999
        if best is None or rank < (best.get("overall_rank") or 9999):
            best = item
    return best


def zh_join(items: list[str]) -> str:
    if len(items) <= 1:
        return items[0] if items else ""
    return "、".join(items[:-1]) + " 与 " + items[-1]


def en_join(items: list[str]) -> str:
    if len(items) <= 1:
        return items[0] if items else ""
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and " + items[-1]


def source_phrase(lang: str, ids: list[str]) -> str:
    present = set(ids or [])
    labels = LABELS[lang]
    overseas = [labels[key] for key in OVERSEAS if key in present]
    hong_kong = [labels[key] for key in HONG_KONG if key in present]
    extra = [key for key in ids or [] if key not in labels]
    if lang == "zh-CN":
        parts = []
        if overseas:
            parts.append("、".join(overseas))
        if hong_kong:
            parts.append("香港 " + zh_join(hong_kong))
        phrase = "，以及".join(parts)
    elif lang == "en":
        phrase = ", ".join(overseas)
        if hong_kong:
            phrase = f"{phrase}, and Hong Kong shops {en_join(hong_kong)}".strip(", ")
    elif lang == "ja":
        phrase = "、".join(overseas)
        if hong_kong:
            phrase = f"{phrase} と、香港の " + "、".join(hong_kong)
    else:
        phrase = ", ".join(overseas)
        if hong_kong:
            phrase = f"{phrase} y, en Hong Kong, {en_join(hong_kong)}".replace(" and ", " y ")
    if extra:
        phrase = (phrase + "、" if phrase else "") + "、".join(extra)
    return phrase


def footer_sources(lang: str, daily: dict) -> str:
    day = str(daily.get("date"))[:10]
    phrase = source_phrase(lang, daily.get("sources_included") or [])
    taobao = "taobao_tmall" in (daily.get("sources_included") or [])
    if lang == "zh-CN":
        tail = "淘宝 / 天猫已有商品行，以该期 JSON 为准。" if taobao else "淘宝 / 天猫仍未收录。"
        return (
            "来源以每期 JSON 为准。设计上包括淘宝 / 天猫、Amazon 和独立品牌店。"
            f"{day} 实际收录 {phrase}。{tail}"
        )
    if lang == "en":
        tail = "Taobao/Tmall rows are in that file." if taobao else "Taobao/Tmall is still absent."
        return (
            "Each issue follows its JSON. The design includes Taobao/Tmall, Amazon, and independent shops. "
            f"The {day} issue includes {phrase}. {tail}"
        )
    if lang == "ja":
        tail = "淘宝 / 天猫の行は当該 JSON にあります。" if taobao else "淘宝 / 天猫はまだありません。"
        return (
            "各回は対応する JSON に従います。設計上は淘宝 / 天猫、Amazon、インディーズ店舗を含みます。"
            f"{day} に入っているのは {phrase} です。{tail}"
        )
    tail = "Taobao/Tmall tiene filas en ese archivo." if taobao else "Taobao/Tmall sigue sin filas."
    return (
        "Cada entrega sigue su JSON. El diseño incluye Taobao/Tmall, Amazon y tiendas independientes. "
        f"La entrega del {day} incluye {phrase}. {tail}"
    )


def short_faq(lang: str, daily: dict) -> tuple[str, str]:
    day = str(daily.get("date"))[:10]
    year, month, dom = int(day[:4]), int(day[5:7]), int(day[8:10])
    phrase = source_phrase(lang, daily.get("sources_included") or [])
    taobao = "taobao_tmall" in (daily.get("sources_included") or [])
    if lang == "zh-CN":
        shop = (
            f"{day} 这一期是 {phrase}。要下单，请回到商家自己的页面核对。"
            if taobao
            else f"{day} 这一期是 {phrase}。淘宝 / 天猫没有商品行。没能收录的来源写在页面末尾，没有拿别的数据来凑数。"
        )
        opened = (
            f"不是。青榜把 {year} 年 {month} 月 {dom} 日能打开的公开热销页整理在一起，"
            "方便对照商品名称、价格和评分。要下单，请回到商家自己的页面核对。"
        )
        return opened, shop
    if lang == "en":
        opened = (
            f"No. Qing List lines up public bestseller pages that were open on {dom} {EN_MONTHS[month]} {year}, "
            "so you can compare names, prices, and ratings. Order from the merchant only after you check the live page."
        )
        tail = "Taobao/Tmall rows are in the file." if taobao else "Taobao/Tmall has no product rows."
        shop = (
            f"The {day} issue includes {phrase}. {tail} "
            "Sources that did not make the file are listed at the bottom and are not backfilled."
        )
        return opened, shop
    if lang == "ja":
        opened = (
            f"販売サイトではありません。{year}年{month}月{dom}日に開けた公開の売れ筋ページを並べ、"
            "商品名、価格、評価を見比べられるようにしたものです。購入は各店のページで在庫と価格を確認してからにしてください。"
        )
        tail = "淘宝 / 天猫の商品行は当該 JSON にあります。" if taobao else "淘宝 / 天猫の商品行はありません。"
        shop = f"{day} の回は {phrase} です。{tail}入れなかった出典はページ末尾に書き、別のデータで埋めません。"
        return opened, shop
    opened = (
        f"No. Lista Qing reúne páginas públicas de más vendidos que se pudieron abrir el {dom} de {ES_MONTHS[month]} de {year}, "
        "para comparar nombres, precios y valoraciones. El pedido se hace en la tienda, después de revisar la ficha actual."
    )
    tail = "Taobao/Tmall tiene filas." if taobao else "Taobao/Tmall no tiene filas."
    shop = f"La entrega del {day} incluye {phrase}. {tail} Lo que no entró se lista al final y no se rellena con otros datos."
    return opened, shop


def format_dates(dates: list[str], sample: str) -> str:
    if not dates:
        return sample
    if " 与 " in sample:
        if len(dates) == 1:
            return dates[0]
        return "、".join(dates[:-1]) + " 与 " + dates[-1]
    if ", and " in sample or " and " in sample:
        return en_join(dates)
    if " y " in sample:
        if len(dates) == 1:
            return dates[0]
        if len(dates) == 2:
            return f"{dates[0]} y {dates[1]}"
        return ", ".join(dates[:-1]) + " y " + dates[-1]
    if "、" in sample:
        return "、".join(dates)
    return ", ".join(dates)


def cn_count(count: int) -> str:
    if count == 2:
        return "两"
    if 0 <= count <= 9:
        return CN_COUNT[count]
    return str(count)


def refresh_string(text: str, daily: dict, weekly: dict, lang: str) -> str:
    day = str(daily.get("date") or "")[:10]
    generated = str(daily.get("generated_at") or "")
    aggregation = weekly.get("aggregation") or {}
    dates = list(aggregation.get("daily_dates") or [])
    week_id = str((weekly.get("period") or {}).get("iso_week") or "")
    phrase = source_phrase(lang, daily.get("sources_included") or [])
    if week_id and week_id in text and dates and "seed" not in weekly:
        def repl(match: re.Match) -> str:
            found = re.findall(DATE, match.group(0))
            if len(found) >= 2 and set(found) <= set(dates):
                return format_dates(dates, match.group(0))
            return match.group(0)

        text = LIST_RE.sub(repl, text)
        text = re.sub(r"[两三四五六七八九]份日榜", cn_count(len(dates)) + "份日榜", text)
    text = re.sub(rf"{DATE}(?= 实际收录)", day, text)
    text = re.sub(rf"{DATE}(?= 实际进入)", day, text)
    text = re.sub(rf"{DATE}(?= 这一期)", day, text)
    text = re.sub(rf"(?<=The ){DATE}(?= issue)", day, text)
    text = re.sub(rf"(?<=The ){DATE}(?= chart)", day, text)
    text = re.sub(rf"{DATE}(?= に入っている)", day, text)
    text = re.sub(rf"{DATE}(?= の回)", day, text)
    text = re.sub(rf"(?<=entrega del ){DATE}", day, text)
    if any(token in text for token in ("chart includes", "实际进入榜单")):
        text = re.sub(rf"(not re-fetched on ){DATE}", rf"\1{day}", text)
        text = re.sub(rf"{DATE}(?= に取り直して)", day, text)
        text = re.sub(rf"(consultar el ){DATE}", rf"\1{day}", text)
    def swap_shops(match: re.Match) -> str:
        current = match.group(2)
        if "Dame" not in current and "Lovense" not in current:
            return match.group(0)
        return match.group(1) + phrase + match.group(3)

    if phrase:
        text = re.sub(r"(实际收录 )(.*?)(。)", swap_shops, text)
        text = re.sub(r"(实际进入榜单的是 )(.*?)(。)", swap_shops, text)
        text = re.sub(r"(这一期是 )(.*?)(。)", swap_shops, text)
        text = re.sub(r"(issue includes )(.*?)(\.)", swap_shops, text)
        text = re.sub(r"(chart includes )(.*?)(\.)", swap_shops, text)
        text = re.sub(r"(に入っているのは )(.*?)( です)", swap_shops, text)
        text = re.sub(r"(の回は )(.*?)( です)", swap_shops, text)
        text = re.sub(r"(incluye )(.*?)(\.)", swap_shops, text)
    if any(token in text for token in ("当前日榜", "current daily file", "現在のデイリー", "día actual", "archivo del día actual")):
        text = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00", generated, text)
    if "were open on" in text:
        text = re.sub(
            r"\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}",
            f"{int(day[8:10])} {EN_MONTHS[int(day[5:7])]} {day[:4]}",
            text,
        )
    if "開けた" in text:
        text = re.sub(
            r"\d{4}年\d{1,2}月\d{1,2}日",
            f"{day[:4]}年{int(day[5:7])}月{int(day[8:10])}日",
            text,
        )
    if "se pudieron abrir" in text:
        text = re.sub(
            r"el \d{1,2} de [a-záéíóú]+ de \d{4}",
            f"el {int(day[8:10])} de {ES_MONTHS[int(day[5:7])]} de {day[:4]}",
            text,
        )
    if "能打开的公开热销页" in text:
        text = re.sub(
            r"\d{4} 年 \d{1,2} 月 \d{1,2} 日",
            f"{day[:4]} 年 {int(day[5:7])} 月 {int(day[8:10])} 日",
            text,
        )
    daily_path = (daily.get("publish") or {}).get("archive") or f"data/archive/daily/{day}.json"
    weekly_path = (weekly.get("publish") or {}).get("archive") or ""
    if weekly_path:
        text = re.sub(
            r"data/archive/daily/\d{4}-\d{2}-\d{2}\.json · data/archive/weekly/\d{4}-W\d{2}\.json",
            f"{daily_path} · {weekly_path}",
            text,
        )
    return text


def walk(node, daily: dict, weekly: dict, lang: str):
    if isinstance(node, dict):
        return {key: walk(value, daily, weekly, lang) for key, value in node.items()}
    if isinstance(node, list):
        return [walk(value, daily, weekly, lang) for value in node]
    if isinstance(node, str):
        return refresh_string(node, daily, weekly, lang)
    return node


def refresh_locales(daily: dict, weekly: dict) -> None:
    for code in LANGS:
        path = boardlib.ROOT / "i18n" / f"{code}.json"
        doc = walk(boardlib.load_json(path), daily, weekly, code)
        doc["ui"]["footerSources"] = footer_sources(code, daily)
        opened, shops = short_faq(code, daily)
        items = doc.get("faq", {}).get("items") or []
        if len(items) >= 2:
            items[0]["a"] = opened
            items[1]["a"] = shops
        boardlib.dump_json(path, doc)
        print(f"refreshed i18n/{code}.json")


def refresh_prose(daily: dict, weekly: dict) -> None:
    day = str(daily.get("date"))[:10]
    for name in ("faq.html", "method.html", "about.html", "README-DEPLOY.md"):
        path = boardlib.ROOT / name
        if not path.exists():
            continue
        text = refresh_string(path.read_text(encoding="utf-8"), daily, weekly, "zh-CN")
        path.write_text(text, encoding="utf-8")
        print(f"refreshed {name}")
    for name in INFO_HTML:
        path = boardlib.ROOT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r'("dateModified": ")\d{4}-\d{2}-\d{2}(")', rf"\g<1>{day}\2", text)
        path.write_text(stamp_as_of(text, day), encoding="utf-8")


def stamp_as_of(html: str, day: str) -> str:
    meta = f'<meta name="qing:as-of" content="{day}">'
    if 'name="qing:as-of"' in html:
        return re.sub(r'<meta name="qing:as-of" content="[^"]*">', meta, html, count=1)
    needle = '<meta name="rating" content="adult">'
    if needle in html:
        return html.replace(needle, needle + "\n" + meta, 1)
    return html


LLMS_LINK = '<link rel="alternate" type="text/plain" href="llms.txt" title="llms.txt">'
WEBMASTER_HOOK = (
    "<!-- webmaster-verify: paste tokens into seo.config.json. "
    "bing_site_verification -> meta name=msvalidate.01; "
    "baidu_site_verification -> meta name=baidu-site-verification. "
    "Leave both empty until Bing Webmaster Tools or Baidu Search Resource Platform issues a code. -->"
)
VERIFY_TOKEN = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
VERIFY_META_RES = (
    re.compile(r'\n?<meta name="msvalidate\.01" content="[^"]*">'),
    re.compile(r'\n?<meta name="baidu-site-verification" content="[^"]*">'),
)


def load_seo_config() -> dict:
    path = boardlib.ROOT / "seo.config.json"
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise SystemExit("seo.config.json must be an object")
    return doc


def ensure_llms_link(html: str) -> str:
    if 'type="text/plain" href="llms.txt"' in html:
        return html
    needle = '<link rel="sitemap" type="application/xml" title="Sitemap" href="sitemap.xml">'
    if needle not in html:
        raise SystemExit("homepage is missing the sitemap link")
    return html.replace(needle, needle + "\n" + LLMS_LINK, 1)


def verification_lines(config: dict) -> list[str]:
    mapping = (
        ("bing_site_verification", "msvalidate.01"),
        ("baidu_site_verification", "baidu-site-verification"),
    )
    lines = []
    for key, meta_name in mapping:
        value = str(config.get(key) or "").strip()
        if not value:
            continue
        if not VERIFY_TOKEN.fullmatch(value):
            raise SystemExit(
                f"{key} must be the verification token only (8-128 letters, digits, _ or -), or empty"
            )
        lines.append(f'<meta name="{meta_name}" content="{esc(value)}">')
    return lines


def apply_webmaster_hooks(html: str, config: dict | None = None) -> str:
    """Insert Bing/Baidu meta tags when seo.config.json has a real token.

    Empty values leave a comment and do not emit a meta tag. No placeholder
    code is invented.
    """
    if config is None:
        config = load_seo_config()
    for pattern in VERIFY_META_RES:
        html = pattern.sub("", html)
    html = html.replace("\n" + WEBMASTER_HOOK, "").replace(WEBMASTER_HOOK, "")
    lines = verification_lines(config)
    block = "\n".join(lines) if lines else WEBMASTER_HOOK
    match = re.search(r'(<meta name="google-site-verification" content="[^"]*">)', html)
    if not match:
        raise SystemExit("homepage is missing google-site-verification")
    return html[: match.end()] + "\n" + block + html[match.end() :]


def load_locales() -> dict[str, dict]:
    return {code: boardlib.load_json(boardlib.ROOT / "i18n" / f"{code}.json") for code in LANGS}


def join_sources(ids: list[str], platforms: dict, lang: str) -> str:
    sep = ", " if lang in ("en", "es") else "、"
    names = []
    for key in ids or []:
        name = (platforms.get(key) or {}).get("name") or key
        if name:
            names.append(name)
    return sep.join(names)


def week_clause(doc: dict, lang: str) -> str:
    week = (doc.get("period") or {}).get("iso_week") or ""
    if not week:
        return ""
    if lang == "zh-CN":
        return "，" + week
    if lang == "ja":
        return "、" + week
    return ", " + week


def top_sentence(page: dict, item: dict, products: dict) -> str:
    copy = products.get(item.get("id") or "", {})
    listing = item.get("name") or ""
    display = copy.get("display") or ""
    named = bool(display and display != listing)
    template = (page.get("geoTopNamed") if named else page.get("geoTop")) or ""
    return fill(template, {
        "store": item.get("store") or "",
        "listing": listing,
        "display": display,
        "price": boardlib.money(item.get("price"), item.get("currency")),
    })


def seed_sentence(page: dict, doc: dict, lang: str) -> str:
    sep = ", " if lang in ("en", "es") else "、"
    aggregation = doc.get("aggregation")
    if aggregation:
        days = list(aggregation.get("daily_dates") or [])
        return fill(page.get("geoAggregated") or "", {
            "days": sep.join(days),
            "count": str(aggregation.get("daily_count") or len(days)),
        })
    seed = doc.get("seed") or {}
    if seed:
        return fill(page.get("geoSeed") or "", {
            "snapshot": seed.get("snapshot_date") or doc.get("as_of") or "",
        })
    return page.get("geoNoSeed") or ""


def geo_lines(pack: dict, page_name: str, board: str, doc: dict, products: dict, lang: str) -> list[str]:
    page = pack["pages"][page_name][board]
    item = top_item(doc)
    values = {
        "period": period_token(doc),
        "tz": doc.get("timezone") or "Asia/Shanghai",
        "count": str(len(doc.get("items") or [])),
        "sources": join_sources(doc.get("sources_included") or [], pack.get("platforms") or {}, lang),
        "weekClause": week_clause(doc, lang),
        "top": top_sentence(page, item, products) if item else "",
        "seed": seed_sentence(page, doc, lang) if board == "weekly" else "",
    }
    lines = []
    for line in page.get("geo") or []:
        text = fill(line, values).strip()
        if text:
            lines.append(text)
    return lines


def head_pack(locales: dict[str, dict], page_name: str, daily: dict, weekly: dict) -> dict:
    packs = {"daily": {}, "weekly": {}}
    docs = {"daily": daily, "weekly": weekly}
    title_key = "platformTitle" if page_name == "platform" else "topTitle"
    desc_key = "platformDescription" if page_name == "platform" else "topDescription"
    for board, doc in docs.items():
        for code in LANGS:
            meta = locales[code]["meta"]
            board_meta = meta["boards"][board]
            period = period_token(doc)
            packs[board][code] = {
                "htmlLang": meta["htmlLang"],
                "og": meta["ogLocale"],
                "title": fill(board_meta[title_key], {"period": period}),
                "desc": fill(board_meta[desc_key], {"period": period}),
                "alt": fill(board_meta["ogImageAlt"], {"period": period}),
            }
    return packs


def set_meta(html: str, kind: str, name: str, content: str) -> str:
    pattern = re.compile(rf'(<meta {kind}="{re.escape(name)}" content=")(.*?)(">)', re.S)
    updated, count = pattern.subn(lambda match: match.group(1) + esc(content) + match.group(3), html, count=1)
    if count != 1:
        raise SystemExit(f"missing meta {kind}={name}")
    return updated


def replace_element(html: str, pattern: str, inner: str, label: str) -> str:
    updated, count = re.subn(pattern, lambda match: match.group(1) + inner + match.group(3), html, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"missing {label}")
    return updated


def replace_js_object(html: str, marker: str, payload: str) -> str:
    start = html.find(marker)
    if start < 0:
        raise SystemExit(f"missing {marker.strip()}")
    index = start + len(marker)
    while index < len(html) and html[index] in " \n\r\t":
        index += 1
    if index >= len(html) or html[index] not in "{[":
        raise SystemExit(f"{marker.strip()} is not a value")
    opening = html[index]
    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string = False
    escaped = False
    cursor = index
    while cursor < len(html):
        char = html[cursor]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == opening:
                depth += 1
            elif char == closing:
                depth -= 1
                if depth == 0:
                    cursor += 1
                    break
        cursor += 1
    else:
        raise SystemExit(f"unclosed value after {marker.strip()}")
    return html[:index] + payload + html[cursor:]


def item_list(daily: dict, products: dict) -> list[dict]:
    elements = []
    for item in daily.get("items") or []:
        elements.append({
            "@type": "ListItem",
            "position": item.get("overall_rank"),
            "item": boardlib.product_node(item, products),
        })
    return elements


def faq_entities(items: list[dict]) -> list[dict]:
    entities = []
    for item in items:
        entities.append({
            "@type": "Question",
            "name": item.get("q"),
            "acceptedAnswer": {"@type": "Answer", "text": item.get("a")},
        })
    return entities


SITE_ALT_EXTRAS = ("情趣用品排行榜", "Sex toy bestsellers", "Qing List")
ABOUT_NAME = "情趣用品公开销售排行榜"
TRUST_HTML = ("about.html", "method.html", "faq.html", "privacy.html", "contact.html")


def ranking_meta(locales: dict[str, dict]) -> tuple[str, str]:
    meta = (locales.get("zh-CN") or {}).get("meta") or {}
    return meta.get("seoKeywords") or "", meta.get("siteDescription") or ""


def apply_ranking_identity(node: dict, locales: dict[str, dict], *, chart_page: bool) -> None:
    """Stamp JSON-LD with ranking-list keywords. No HTML meta keywords tag.

    WebPage on the chart shells also gets an adults-only about Thing. WebSite
    alternateName picks up 排行榜 / bestsellers names when they are missing.
    """
    kind = node.get("@type")
    keywords, about_desc = ranking_meta(locales)
    if kind == "WebPage" and chart_page:
        if keywords:
            node["keywords"] = keywords
        if about_desc:
            node["about"] = {
                "@type": "Thing",
                "name": ABOUT_NAME,
                "description": about_desc,
            }
    elif kind == "WebSite":
        alts = node.get("alternateName") or []
        if isinstance(alts, str):
            alts = [alts]
        else:
            alts = list(alts)
        for extra in SITE_ALT_EXTRAS:
            if extra not in alts:
                alts.append(extra)
        node["alternateName"] = alts
        if keywords:
            node["keywords"] = keywords
        if about_desc:
            node["description"] = about_desc
    elif kind == "Organization" and about_desc:
        node["description"] = about_desc


def paint_visible_copy(html: str, page_name: str, locales: dict[str, dict]) -> str:
    """Write the zh-CN H1, lead, and list title into the static shell.

    app.js replaces these after it loads i18n. Crawlers that do not run
    JavaScript need the ranking-list phrasing in the HTML itself.
    """
    page = locales["zh-CN"]["pages"][page_name]["daily"]
    faq = locales["zh-CN"].get("faq") or {}
    html = replace_element(
        html,
        r'(<h1 id="hero-title">)(.*?)(</h1>)',
        esc(page.get("h1") or ""),
        "hero-title",
    )
    html = replace_element(
        html,
        r'(<p class="lead" id="hero-lead">)(.*?)(</p>)',
        esc(page.get("lead") or ""),
        "hero-lead",
    )
    if 'id="list-title"' in html and page.get("listTitle"):
        html = replace_element(
            html,
            r'(<h2 id="list-title">)(.*?)(</h2>)',
            esc(page["listTitle"]),
            "list-title",
        )
    if 'id="faq-title"' in html and faq.get("title"):
        html = replace_element(
            html,
            r'(<h2 id="faq-title">)(.*?)(</h2>)',
            esc(faq["title"]),
            "faq-title",
        )
    if 'id="faq-lead"' in html and faq.get("lead"):
        html = replace_element(
            html,
            r'(<p class="faq-lead" id="faq-lead">)(.*?)(</p>)',
            esc(faq["lead"]),
            "faq-lead",
        )
    return html


def patch_trust_jsonld(path: Path, locales: dict[str, dict]) -> None:
    if not path.exists():
        return
    html = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<script type="application/ld\+json" id="ld-json">\s*(.*?)\s*</script>',
        re.S,
    )
    match = pattern.search(html)
    if not match:
        return
    graph = json.loads(match.group(1))
    for node in graph.get("@graph") or []:
        apply_ranking_identity(node, locales, chart_page=False)
    rendered = json.dumps(graph, ensure_ascii=False, indent=2)
    block = '<script type="application/ld+json" id="ld-json">\n' + rendered + "\n</script>"
    html = pattern.sub(lambda _match: block, html, count=1)
    path.write_text(html, encoding="utf-8")
    print(f"refreshed site JSON-LD in {path.name}")


def patch_shell(path: Path, page_name: str, daily: dict, weekly: dict, locales: dict[str, dict]) -> None:
    html = path.read_text(encoding="utf-8")
    packs = head_pack(locales, page_name, daily, weekly)
    zh = packs["daily"]["zh-CN"]
    products = locales["zh-CN"].get("products") or {}
    day = str(daily.get("date"))[:10]
    html = re.sub(r"<title>.*?</title>", f"<title>{esc(zh['title'])}</title>", html, count=1, flags=re.S)
    html = paint_visible_copy(html, page_name, locales)
    for kind, name, content in (
        ("name", "description", zh["desc"]),
        ("property", "og:title", zh["title"]),
        ("property", "og:description", zh["desc"]),
        ("property", "og:image:alt", zh["alt"]),
        ("name", "twitter:title", zh["title"]),
        ("name", "twitter:description", zh["desc"]),
        ("name", "twitter:image:alt", zh["alt"]),
    ):
        html = set_meta(html, kind, name, content)
    html = stamp_as_of(html, day)
    if path.name == "index.html":
        html = ensure_llms_link(html)
        html = apply_webmaster_hooks(html)

    pattern = re.compile(
        r'<script type="application/ld\+json" id="ld-json">\s*(.*?)\s*</script>',
        re.S,
    )
    match = pattern.search(html)
    if not match:
        raise SystemExit(f"no ld-json in {path.name}")
    graph = json.loads(match.group(1))
    coverage = day
    period = daily.get("period") or {}
    if period.get("start") and period.get("end"):
        coverage = period["start"] if period["start"] == period["end"] else f"{period['start']}/{period['end']}"
    for node in graph.get("@graph") or []:
        kind = node.get("@type")
        if kind == "WebPage":
            node["name"] = zh["title"]
            node["description"] = zh["desc"]
            node["dateModified"] = day
            node["temporalCoverage"] = coverage
            node["isFamilyFriendly"] = False
            apply_ranking_identity(node, locales, chart_page=True)
        elif kind == "WebSite":
            apply_ranking_identity(node, locales, chart_page=True)
        elif kind == "Organization":
            apply_ranking_identity(node, locales, chart_page=True)
        elif kind == "ItemList":
            node["name"] = zh["title"]
            node["description"] = zh["desc"]
            node["numberOfItems"] = len(daily.get("items") or [])
            node["itemListElement"] = item_list(daily, products)
        elif kind == "FAQPage":
            node["mainEntity"] = faq_entities(locales["zh-CN"]["faq"]["items"])
            node["isFamilyFriendly"] = False
    rendered = json.dumps(graph, ensure_ascii=False, indent=2)
    block = '<script type="application/ld+json" id="ld-json">\n' + rendered + "\n</script>"
    html = pattern.sub(lambda _match: block, html, count=1)

    html = replace_js_object(html, "var COPY = ", json.dumps(packs, ensure_ascii=False, indent=2))
    summary = "\n".join(f"        <p>{esc(line)}</p>" for line in geo_lines(locales["zh-CN"], page_name, "daily", daily, products, "zh-CN"))
    html = replace_element(
        html,
        r'(<div class="geo-summary" id="geo-summary"[^>]*>\n)(.*?)(\n      </div>)',
        summary + "\n",
        "geo-summary",
    )
    weekly_lines = geo_lines(locales["zh-CN"], page_name, "weekly", weekly, products, "zh-CN")
    html = replace_js_object(html, "var lines = ", json.dumps(weekly_lines, ensure_ascii=False, indent=2))
    year, month, dom = int(day[:4]), int(day[5:7]), int(day[8:10])
    html = replace_element(
        html,
        r'(<strong id="stat-date">)(.*?)(</strong>)',
        f"{year}年{month}月{dom}日",
        "stat-date",
    )
    faq_html = []
    for item in locales["zh-CN"]["faq"]["items"]:
        faq_html.append(
            "      <div class=\"faq-item\">\n"
            f"        <h3>{esc(item.get('q'))}</h3>\n"
            f"        <p>{esc(item.get('a'))}</p>\n"
            "      </div>"
        )
    html = replace_element(
        html,
        r'(<div id="faq-list">\n)(.*?)(\n    </div>)',
        "\n".join(faq_html) + "\n",
        "faq-list",
    )
    ui = locales["zh-CN"]["ui"]
    html = replace_element(
        html,
        r'(<p id="foot-sources">)(.*?)(</p>)',
        esc(ui.get("footerSources") or ""),
        "foot-sources",
    )
    html = replace_element(
        html,
        r'(<p id="foot-links">)(.*?)(</p>)',
        esc(fill(ui.get("footerLinks") or "", {"time": daily.get("generated_at") or ""})),
        "foot-links",
    )
    archive = (daily.get("publish") or {}).get("archive") or f"data/archive/daily/{day}.json"
    html = replace_element(
        html,
        r'(<p id="foot-archive">)(.*?)(</p>)',
        esc(fill(ui.get("footerArchive") or "日期归档：{path}", {"path": archive})),
        "foot-archive",
    )
    if weekly.get("aggregation") and not weekly.get("seed"):
        seed_text = "若周榜 JSON 仍带有 seed，那一份才是某一天日榜的副本。当前这份周榜没有 seed。"
    elif weekly.get("seed"):
        seed_text = fill(ui.get("seedNote") or "", {
            "snapshot": (weekly.get("seed") or {}).get("snapshot_date") or "",
            "source": (weekly.get("seed") or {}).get("source") or "",
            "tz": weekly.get("timezone") or "Asia/Shanghai",
            "latest": (weekly.get("publish") or {}).get("latest") or "",
            "archive": (weekly.get("publish") or {}).get("archive") or "",
        })
    else:
        seed_text = "若周榜 JSON 带有 seed，页面会写明它是某一天日榜的副本。"
    html = replace_element(
        html,
        r'(<p class="seed-note" id="seed-note"[^>]*>)(.*?)(</p>)',
        esc(seed_text),
        "seed-note",
    )
    aggregation = weekly.get("aggregation") or {}
    agg_text = ""
    if aggregation:
        days = aggregation.get("daily_dates") or []
        agg_text = fill(ui.get("aggNote") or "", {
            "days": "、".join(days),
            "count": str(aggregation.get("daily_count") or len(days)),
            "week": (weekly.get("period") or {}).get("iso_week") or "",
        })
    html = replace_element(
        html,
        r'(<p class="seed-note" id="agg-note"[^>]*>)(.*?)(</p>)',
        esc(agg_text),
        "agg-note",
    )
    path.write_text(html, encoding="utf-8")
    print(f"rewrote SEO shell in {path.name} for {day}")


def write_llms(daily: dict, weekly: dict) -> None:
    day = str(daily.get("date"))[:10]
    generated = daily.get("generated_at") or ""
    period = weekly.get("period") or {}
    week_id = period.get("iso_week") or ""
    week_start = period.get("start") or ""
    week_end = period.get("end") or ""
    aggregation = weekly.get("aggregation") or {}
    dates = aggregation.get("daily_dates") or []
    date_text = ", ".join(dates[:-1]) + (", and " + dates[-1] if len(dates) > 1 else (dates[0] if dates else ""))
    phrase = source_phrase("en", daily.get("sources_included") or [])
    publish = daily.get("publish") or {}
    daily_board_day = boardlib.parse_date(day)
    daily_week = boardlib.iso_week_id(daily_board_day)
    bounds = boardlib.week_bounds(daily_board_day)
    same_week = [
        item.isoformat()
        for item, _path, _doc in boardlib.iter_daily_archives()
        if boardlib.iso_week_id(item) == daily_week
    ]
    if aggregation and not weekly.get("seed"):
        weekly_fact = (
            f"The published weekly file is {week_id} ({week_start} through {week_end}). "
            f"It aggregates {len(dates)} daily archives: {date_text}. "
            "It has no seed field. It is not a one-day copy and not a merchant-reported weekly sales total."
        )
    elif weekly.get("seed"):
        snap = (weekly.get("seed") or {}).get("snapshot_date") or weekly.get("date")
        weekly_fact = (
            f"The published weekly file {week_id} still has a seed and is a copy of the {snap} daily chart, "
            "not a separate week-long tally."
        )
    else:
        weekly_fact = f"The published weekly file is {week_id} ({week_start} through {week_end})."
    if daily_week == week_id:
        current_week = weekly_fact
    else:
        current_week = (
            f"{weekly_fact} "
            f"The latest daily date {day} falls in {daily_week} "
            f"({bounds[0].isoformat()} through {bounds[1].isoformat()}). "
            f"That ISO week currently has {len(same_week)} daily archive(s)"
            + (f" ({', '.join(same_week)})" if same_week else "")
            + ". scripts/build_weekly.py writes an aggregated week only when two or more daily archives exist, "
            f"so {daily_week} is not published as data/weekly-latest.json."
        )
    skipped = []
    for row in daily.get("sources_skipped") or []:
        label = SKIP_LABEL.get(row.get("platform") or "", row.get("platform") or "")
        status = row.get("status") or ""
        note = row.get("note") or ""
        skipped.append(f"{label} ({status}: {note})" if note else f"{label} ({status})")
    skipped_text = "; ".join(skipped) if skipped else "None recorded on this daily file."
    text = f"""# 青榜 Qing List

> Adults-only (18+) charts of publicly listed intimate-product bestsellers. This site does not sell products, take payment, or ship orders. It is a static GitHub Pages snapshot, not a store and not medical advice.

青榜把若干店铺当天或当周能打开的公开热销页整理成日榜和周榜，保留商品名称、价格、评分、图片和链接，方便对照。页面默认简体中文，同一 URL 可用 ?lang=en、?lang=ja、?lang=es。不带 lang 的网址是 zh-CN，也是 hreflang 的 x-default。

## Search intents this site answers

- Chinese: 情趣用品排行榜, 情趣用品销量排行榜, 情趣用品热销榜, 情趣用品日榜, 情趣用品周榜, 成人用品排行榜
- English: sex toy bestsellers, sex toys ranking, intimate product bestsellers chart, best selling sex toys
- Japanese: アダルトグッズ売れ筋ランキング, アダルトグッズ売上ランキング, 大人のおもちゃランキング
- Spanish: juguetes sexuales más vendidos, ranking juguetes sexuales

Answers are public-list snapshots (names, prices, ratings, links), not a store and not invented sales totals.

## Adult-only

The charts are for adults aged 18 or older. An age gate asks the visitor to confirm that before the product cards are shown. Content is sexual-wellness / adult-product retail data. Do not present it to minors. It is not a recommendation to buy or use any product.

## Update cadence

Time zone for every board date is Asia/Shanghai.

- Daily: one calendar day. A routine publish replaces data/daily-latest.json in full and writes the same document to data/daily-YYYY-MM-DD.json and data/archive/daily/YYYY-MM-DD.json. Older rows are not merged into that file, and products are not invented to fill a Top 20.
- The latest daily file is {day}, generated at {generated}. Paths: {publish.get("latest") or "data/daily-latest.json"}, {publish.get("dated") or "data/daily-" + day + ".json"}, {publish.get("archive") or "data/archive/daily/" + day + ".json"}.
- Weekly: Monday through Sunday (ISO week). When data/archive/daily/ contains two or more daily files for that week, scripts/build_weekly.py dedupes by product URL and ranks by how many of those days the product appeared, then mean source rank, then best source rank, then rating, then review count. It writes data/weekly-latest.json and data/archive/weekly/YYYY-Www.json and does not mark that file as a seed.
- If a week has only one daily archive, the script leaves the weekly file alone. A weekly JSON that still has a seed object is a copy of one day's chart, not a separate week-long tally. The page says so.
- {current_week}

Prices, ratings, and ranks match the file's date. They are not a live quote.

Every publish also runs scripts/build_homepage.py (via scripts/publish_boards.py) so the homepage title, description, Open Graph, Twitter, JSON-LD dates, ItemList, and prerendered summary match these files.

## What is and is not included

The {day} daily chart includes {phrase}. Hong Kong ranks follow the order on that shop's public category page. Each source contributes at most 6 rows to the combined Top 20.

Not on the {day} daily chart: {skipped_text} Rows were not invented. The empty Taobao / Tmall placeholder remains data/sources/taobao_tmall.placeholder.json.

## Key URLs

- Home, daily chart: https://orangexie05.github.io/qing-bestsellers-top/
- Weekly chart: https://orangexie05.github.io/qing-bestsellers-top/?board=weekly
- By shop: https://orangexie05.github.io/qing-bestsellers-top/by-platform.html
- Archive index: https://orangexie05.github.io/qing-bestsellers-top/archive/index.html
- Example daily archive: https://orangexie05.github.io/qing-bestsellers-top/archive/daily/{day}.html
- Example weekly archive: https://orangexie05.github.io/qing-bestsellers-top/archive/weekly/{week_id}.html
- About: https://orangexie05.github.io/qing-bestsellers-top/about.html
- Methodology: https://orangexie05.github.io/qing-bestsellers-top/method.html
- FAQ: https://orangexie05.github.io/qing-bestsellers-top/faq.html
- Privacy: https://orangexie05.github.io/qing-bestsellers-top/privacy.html
- Contact: https://orangexie05.github.io/qing-bestsellers-top/contact.html
- Latest JSON: https://orangexie05.github.io/qing-bestsellers-top/data/daily-latest.json and https://orangexie05.github.io/qing-bestsellers-top/data/weekly-latest.json
- Sitemap: https://orangexie05.github.io/qing-bestsellers-top/sitemap.xml
- Plain-text sitemap (HTML URLs only): https://orangexie05.github.io/qing-bestsellers-top/sitemap.txt

Outbound product links use rel="nofollow". Corrections go to GitHub issues: https://github.com/orangexie05/qing-bestsellers-top/issues

## Discovery

Search and answer-engine crawlers may fetch the public HTML. robots.txt allows User-agent: * and explicitly allows Bingbot, DuckDuckBot, Slurp, Baiduspider, YandexBot, Applebot, GPTBot, ChatGPT-User, OAI-SearchBot, ClaudeBot, Claude-SearchBot, Anthropic-AI, PerplexityBot, Google-Extended, and Applebot-Extended. That allow list does not change the adults-only rule: pages use rating=adult and an age gate before product cards. The site does not sell products, take payment, or ship orders.

- robots.txt: https://orangexie05.github.io/qing-bestsellers-top/robots.txt
- Homepage also links rel="alternate" type="text/plain" to llms.txt.

## Privacy in short

Google Analytics 4 measurement ID G-1SF9TQS3F1 may receive page-view data. The site has no accounts, no checkout, and no sale of personal data. Age confirmation and language choice stay in the browser (localStorage keys qbt-age and qbt-lang). Details are on the privacy page.
"""
    dest = boardlib.ROOT / "llms.txt"
    dest.write_text(text, encoding="utf-8")
    print(f"wrote llms.txt daily={day} weekly={week_id}")


def main() -> int:
    daily_path = boardlib.ROOT / "data" / "daily-latest.json"
    weekly_path = boardlib.ROOT / "data" / "weekly-latest.json"
    if not daily_path.exists():
        raise SystemExit("missing data/daily-latest.json")
    daily = boardlib.load_json(daily_path)
    weekly = boardlib.load_json(weekly_path) if weekly_path.exists() else {}
    day = str(daily.get("date") or daily.get("as_of") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise SystemExit("daily-latest.json has no date")
    refresh_locales(daily, weekly)
    refresh_prose(daily, weekly)
    locales = load_locales()
    patch_shell(boardlib.ROOT / "index.html", "top", daily, weekly, locales)
    patch_shell(boardlib.ROOT / "by-platform.html", "platform", daily, weekly, locales)
    for name in TRUST_HTML:
        patch_trust_jsonld(boardlib.ROOT / name, locales)
    write_llms(daily, weekly)
    title = re.search(r"<title>(.*?)</title>", (boardlib.ROOT / "index.html").read_text(encoding="utf-8"), re.S)
    if not title or day not in title.group(1):
        raise SystemExit("homepage title does not contain the daily date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
