#!/usr/bin/env python3
"""Write readable HTML for each archived daily and weekly JSON board."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib

BASE = boardlib.BASE
GA = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-1SF9TQS3F1"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-1SF9TQS3F1');
</script>"""


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def hreflang_links(path: str) -> str:
    alts = [("zh-CN", path), ("en", path + "?lang=en"), ("ja", path + "?lang=ja"), ("es", path + "?lang=es"), ("x-default", path)]
    return "\n".join(
        f'<link rel="alternate" hreflang="{code}" href="{BASE}{href}">' for code, href in alts
    )


def head_script(path: str, titles: dict[str, str], descriptions: dict[str, str]) -> str:
    copy = {
        "zh-CN": {"htmlLang": "zh-Hans", "og": "zh_CN", "title": titles["zh-CN"], "desc": descriptions["zh-CN"]},
        "en": {"htmlLang": "en", "og": "en_US", "title": titles["en"], "desc": descriptions["en"]},
        "ja": {"htmlLang": "ja", "og": "ja_JP", "title": titles["ja"], "desc": descriptions["ja"]},
        "es": {"htmlLang": "es", "og": "es_ES", "title": titles["es"], "desc": descriptions["es"]},
    }
    payload = json.dumps(copy, ensure_ascii=False)
    return f"""<script>
(function () {{
  var PATH = {json.dumps(path)};
  var BASE = {json.dumps(BASE)};
  var COPY = {payload};
  var lang = "zh-CN";
  try {{
    var q = new URLSearchParams(location.search).get("lang");
    if (COPY[q]) lang = q;
  }} catch (err) {{}}
  var pack = COPY[lang];
  function abs(code) {{
    return BASE + PATH + (code && code !== "zh-CN" ? "?lang=" + encodeURIComponent(code) : "");
  }}
  var url = abs(lang);
  document.documentElement.lang = pack.htmlLang;
  document.title = pack.title;
  function meta(attr, name, value) {{
    var node = document.querySelector("meta[" + attr + "=\\"" + name + "\\"]");
    if (node) node.setAttribute("content", value);
  }}
  meta("name", "description", pack.desc);
  meta("property", "og:title", pack.title);
  meta("property", "og:description", pack.desc);
  meta("property", "og:url", url);
  meta("property", "og:locale", pack.og);
  meta("name", "twitter:title", pack.title);
  meta("name", "twitter:description", pack.desc);
  var canon = document.querySelector('link[rel="canonical"]');
  if (canon) canon.setAttribute("href", url);
  ["zh-CN", "en", "ja", "es", "x-default"].forEach(function (code) {{
    var node = document.querySelector('link[rel="alternate"][hreflang="' + code + '"]');
    if (!node) return;
    var target = code === "x-default" || code === "zh-CN" ? "zh-CN" : code;
    node.setAttribute("href", abs(target));
  }});
}})();
</script>"""


def chrome(root: str, current: str, archive_self: bool = False) -> str:
    def href(name: str) -> str:
        if archive_self and name == "archive/index.html":
            return "index.html"
        return root + name

    cur = {
        "daily": ' aria-current="page"' if current == "daily" else "",
        "weekly": ' aria-current="page"' if current == "weekly" else "",
        "archive": ' aria-current="page"' if current == "archive" else "",
    }
    return f"""<a class="skip" id="skip-link" href="#main">跳到主要内容</a>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{esc(href('index.html'))}">
      <span class="brand-mark" aria-hidden="true">18+</span>
      <span>
        <span class="brand-name" id="brand-name">青榜</span>
        <span class="brand-sub" id="brand-sub">成人热销快照</span>
      </span>
    </a>
    <nav class="site-nav" id="site-nav" aria-label="页面">
      <a href="{esc(href('index.html'))}" id="nav-daily"{cur['daily']}>日榜</a>
      <a href="{esc(href('index.html?board=weekly'))}" id="nav-weekly"{cur['weekly']}>周榜</a>
      <a href="{esc(href('by-platform.html'))}" id="nav-platform">分平台</a>
      <a href="{esc(href('archive/index.html'))}" id="nav-archive"{cur['archive']}>归档</a>
      <a href="{esc(href('about.html'))}" id="nav-about">关于</a>
      <a href="{esc(href('method.html'))}" id="nav-method">方法</a>
      <a href="{esc(href('faq.html'))}" id="nav-faq">FAQ</a>
      <a href="{esc(href('privacy.html'))}" id="nav-privacy">隐私</a>
      <a href="{esc(href('contact.html'))}" id="nav-contact">联系</a>
    </nav>
    <div class="lang" id="lang-switch" role="group" aria-label="语言">
      <button type="button" data-lang="zh-CN" aria-pressed="true">简体中文</button>
      <button type="button" data-lang="en" aria-pressed="false">English</button>
      <button type="button" data-lang="ja" aria-pressed="false">日本語</button>
      <button type="button" data-lang="es" aria-pressed="false">Español</button>
    </div>
  </div>
</header>
<div id="age-gate" class="age-gate" role="dialog" aria-modal="true" aria-labelledby="age-title" aria-describedby="age-body">
  <div class="age-card">
    <span class="badge">18+</span>
    <p class="age-title" id="age-title">此页面仅面向成年人</p>
    <p id="age-body">这里整理的是成人情趣用品的公开热销快照。未满 18 周岁，请离开。继续即表示你确认已达到所在地的法定成人年龄。</p>
    <div class="age-actions">
      <button type="button" class="age-enter" id="age-enter">我已年满 18 周岁</button>
      <button type="button" class="age-leave" id="age-leave">离开</button>
    </div>
  </div>
</div>"""


def footer(root: str, json_href: str, archive_line: str, archive_self: bool = False) -> str:
    def href(name: str) -> str:
        if archive_self and name == "archive/index.html":
            return "index.html"
        return root + name

    return f"""<footer class="site-footer">
  <div class="wrap">
    <p id="foot-age"><strong>仅供年满 18 周岁的成年人浏览。</strong></p>
    <p id="foot-sources">来源以每期 JSON 为准。设计上包括淘宝 / 天猫、Amazon 和独立品牌店。淘宝 / 天猫若仍在 sources_skipped，榜上就没有淘宝商品。</p>
    <p id="foot-cadence">更新频率：日榜按上海时间每天整份更新；周榜在同一 ISO 周有两份或更多日榜时由日榜汇总，只有一份日榜时可能仍是带 seed 的副本。</p>
    <p id="foot-snapshot">本页是各平台公开热销榜的整理快照，不是医疗或健康建议，也不代表推荐购买。价格、库存和名次都会变，下单前请回到商家页面核对。</p>
    <p id="foot-links">外链使用 nofollow。数据时区 Asia/Shanghai。</p>
    <p id="foot-pages"><a id="foot-daily" href="{esc(href('index.html'))}">日榜</a> · <a id="foot-weekly" href="{esc(href('index.html?board=weekly'))}">周榜</a> · <a id="foot-platform" href="{esc(href('by-platform.html'))}">分平台</a> · <a id="foot-archive-page" href="{esc(href('archive/index.html'))}">归档</a> · <a id="foot-about" href="{esc(href('about.html'))}">关于本站</a> · <a id="foot-method" href="{esc(href('method.html'))}">数据方法</a> · <a id="foot-faq" href="{esc(href('faq.html'))}">常见问题</a> · <a id="foot-privacy" href="{esc(href('privacy.html'))}">隐私政策</a> · <a id="foot-contact" href="{esc(href('contact.html'))}">联系</a></p>
    <p id="foot-secondary"><a id="foot-partners" href="{esc(href('partners/'))}">友链</a></p>
    <p><a id="foot-data" href="{esc(json_href)}">查看这份归档 JSON</a> · <a id="foot-snapshot-data" href="{esc(href('data.json'))}">综合快照</a></p>
    <p id="foot-archive">{esc(archive_line)}</p>
  </div>
</footer>"""


def item_list_ld(doc: dict, page_url: str, title: str, description: str) -> str:
    products = {}
    zh = boardlib.ROOT / "i18n" / "zh-CN.json"
    if zh.exists():
        products = boardlib.load_json(zh).get("products") or {}
    elements = []
    for item in doc.get("items") or []:
        elements.append({
            "@type": "ListItem",
            "position": item.get("overall_rank"),
            "item": boardlib.product_node(item, products),
        })
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": page_url + "#webpage",
                "url": page_url,
                "name": title,
                "description": description,
                "inLanguage": "zh-Hans",
                "isFamilyFriendly": False,
                "dateModified": (doc.get("as_of") or doc.get("date") or "")[:10],
                "isPartOf": {"@id": BASE + "/#website"},
                "audience": {"@type": "PeopleAudience", "requiredMinAge": 18},
            },
            {
                "@type": "ItemList",
                "@id": page_url + "#itemlist",
                "name": title,
                "numberOfItems": len(elements),
                "itemListOrder": "https://schema.org/ItemListOrderAscending",
                "itemListElement": elements,
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=2)


def honesty_paragraph(doc: dict) -> str:
    if doc.get("aggregation"):
        dates = "、".join(doc["aggregation"].get("daily_dates") or [])
        return (
            f"这份周榜由 {dates} 的日榜按商品链接去重后汇总，不是商家申报的一周销量，也不是单日副本。"
            "出现天数多的靠前。文件里没有 seed。"
        )
    seed = doc.get("seed") or {}
    if doc.get("board") == "weekly" and seed:
        return (
            f"这份周榜带有 seed：它是 {seed.get('snapshot_date') or ''} 日榜的副本，"
            "不是单独统计的一周销量。商品、价格、评分和名次与该日榜相同。"
        )
    if seed:
        return (
            f"这份日榜文件带有 seed，来源是 {seed.get('source') or '较早的快照'}"
            f"（{seed.get('snapshot_date') or doc.get('date')}）。商品与那份快照相同。"
        )
    return "商品、价格、评分和名次以这一份归档 JSON 为准，没有用别的日期填补。"


def board_copy(doc: dict) -> tuple[dict[str, str], dict[str, str]]:
    period = doc.get("period") or {}
    label = period.get("label") or doc.get("date")
    week = period.get("iso_week") or ""
    count = len(doc.get("items") or [])
    if doc.get("board") == "weekly":
        titles = {
            "zh-CN": f"归档周榜 · {label}｜情趣用品销售 Top {count}",
            "en": f"Archived weekly chart · {label} | intimate-product top {count}",
            "ja": f"週間アーカイブ · {label}｜アダルトグッズ売上 Top {count}",
            "es": f"Archivo semanal · {label} | top {count} de productos íntimos",
        }
        if doc.get("aggregation"):
            days = ", ".join(doc["aggregation"].get("daily_dates") or [])
            descriptions = {
                "zh-CN": f"仅限 18 周岁以上。归档周榜 {label}（{week}，Asia/Shanghai）。由 {days} 的日榜汇总，不是单日副本，也不是淘宝官方总榜。",
                "en": f"Adults 18+ only. Archived weekly chart {label} ({week}, Asia/Shanghai), aggregated from the daily files {days}. Not a one-day copy and not a Taobao official chart.",
                "ja": f"18歳以上。アーカイブ週間 {label}（{week}、Asia/Shanghai）。{days} のデイリーをまとめたもので、ある日の写しでも淘宝の公式総榜でもありません。",
                "es": f"Solo mayores de 18. Archivo semanal {label} ({week}, Asia/Shanghai), agregado con los diarios {days}. No es una copia de un solo día ni el ranking oficial de Taobao.",
            }
        else:
            snap = (doc.get("seed") or {}).get("snapshot_date") or doc.get("date")
            descriptions = {
                "zh-CN": f"仅限 18 周岁以上。归档周榜 {label}（{week}）。文件带有 seed，是 {snap} 日榜的副本，不是单独统计的一周销量。",
                "en": f"Adults 18+ only. Archived weekly chart {label} ({week}). The file is seeded from the {snap} daily chart, not a separate week-long tally.",
                "ja": f"18歳以上。アーカイブ週間 {label}（{week}）。seed 付きで、{snap} のデイリーの写しです。一週間を別に集計したものではありません。",
                "es": f"Solo mayores de 18. Archivo semanal {label} ({week}). El archivo tiene seed: es una copia del día {snap}, no un recuento aparte de toda la semana.",
            }
        return titles, descriptions
    day = doc.get("date")
    titles = {
        "zh-CN": f"归档日榜 · {day}｜情趣用品销售 Top {count}",
        "en": f"Archived daily chart · {day} | intimate-product top {count}",
        "ja": f"デイリーアーカイブ · {day}｜アダルトグッズ売上 Top {count}",
        "es": f"Archivo del día · {day} | top {count} de productos íntimos",
    }
    descriptions = {
        "zh-CN": f"仅限 18 周岁以上。{day}（Asia/Shanghai）情趣用品销售日榜归档，共 {count} 款。价格和名次以该日 JSON 为准。",
        "en": f"Adults 18+ only. Archived intimate-product daily chart for {day} (Asia/Shanghai), {count} rows. Prices and ranks are that day's file.",
        "ja": f"18歳以上。{day}（Asia/Shanghai）のアダルトグッズ売上デイリーのアーカイブ、{count} 件。価格と順位はその日の JSON です。",
        "es": f"Solo mayores de 18. Archivo diario de productos íntimos del {day} (Asia/Shanghai), {count} filas. Precios y puestos son los de ese JSON.",
    }
    return titles, descriptions


def static_items(doc: dict) -> str:
    rows = []
    for item in doc.get("items") or []:
        price = boardlib.money(item.get("price"), item.get("currency"))
        appearances = ""
        if item.get("appearances"):
            appearances = f" · 出现 {item['appearances']} 天"
        rows.append(
            "<li>"
            f"<span class=\"rank\">{esc(item.get('overall_rank'))}</span>"
            "<div>"
            f"<a rel=\"nofollow noopener noreferrer\" href=\"{esc(item.get('product_url'))}\">{esc(item.get('name'))}</a>"
            f"<p class=\"meta\">{esc(item.get('store'))} · 店内第 {esc(item.get('rank'))} 名{esc(appearances)} · {esc(price)}</p>"
            "</div></li>"
        )
    return "\n".join(rows)


def write_board(kind: str, stem: str, doc: dict) -> None:
    root = "../../"
    path = f"/archive/{kind}/{stem}.html"
    titles, descriptions = board_copy(doc)
    page_url = BASE + path
    json_rel = f"../../data/archive/{kind}/{stem}.json"
    archive_line = f"日期归档：data/archive/{kind}/{stem}.json"
    hint = "这是已归档的日榜，不会被下一次日榜整份覆盖改写。" if kind == "daily" else "这是已归档的周榜。最新一周仍以周榜页为准。"
    note = honesty_paragraph(doc)
    note_id = "agg-note" if doc.get("aggregation") else "seed-note"
    other_hidden = "seed-note" if note_id == "agg-note" else "agg-note"
    ld = item_list_ld(doc, page_url, titles["zh-CN"], descriptions["zh-CN"])
    board = "weekly" if kind == "weekly" else "daily"
    html_doc = f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
{GA}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="rating" content="adult">
<title>{esc(titles['zh-CN'])}</title>
<meta name="description" content="{esc(descriptions['zh-CN'])}">
<meta name="robots" content="index,follow,max-snippet:-1">
<link rel="canonical" href="{page_url}">
{hreflang_links(path)}
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(titles['zh-CN'])}">
<meta property="og:description" content="{esc(descriptions['zh-CN'])}">
<meta property="og:url" content="{page_url}">
<meta property="og:locale" content="zh_CN">
<meta property="og:locale:alternate" content="en_US">
<meta property="og:locale:alternate" content="ja_JP">
<meta property="og:locale:alternate" content="es_ES">
<meta property="og:image" content="{BASE}/assets/og-share.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(titles['zh-CN'])}">
<meta name="twitter:description" content="{esc(descriptions['zh-CN'])}">
<meta name="twitter:image" content="{BASE}/assets/og-share.png">
<meta name="theme-color" content="#1b1216">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="sitemap" type="application/xml" title="Sitemap" href="{root}sitemap.xml">
<link rel="stylesheet" href="{root}styles.css">
<script type="application/ld+json" id="ld-json">
{ld}
</script>
{head_script(path, titles, descriptions)}
</head>
<body class="is-gated" data-page="archive" data-board="{board}" data-board-file="data/archive/{kind}/{stem}.json" data-path="{path}" data-root="{root}">
{chrome(root, "archive")}
<div class="wrap">
<main id="main">
  <div class="board-bar">
    <p class="board-hint" id="board-hint">{esc(hint)}</p>
    <p class="cross"><a id="archive-back-daily" href="{root}index.html">最新日榜</a> · <a id="archive-back-weekly" href="{root}index.html?board=weekly">最新周榜</a> · <a id="archive-back-index" href="../index.html">全部归档</a></p>
  </div>
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-copy">
      <p class="kicker" id="hero-kicker">归档 · 仅限 18 周岁以上</p>
      <h1 id="hero-title">{esc(titles['zh-CN'])}</h1>
      <div class="geo-summary" id="geo-summary" aria-label="本页摘要">
        <p>{esc(descriptions['zh-CN'])}</p>
        <p>{esc(note)}</p>
      </div>
      <p class="lead" id="hero-lead">下面先列出这一份归档里的商品名称、店铺、店内名次和标价。打开页面并确认年龄后，会换成与最新榜相同的卡片。</p>
      <p class="seed-note" id="{note_id}">{esc(note)}</p>
      <p class="seed-note" id="{other_hidden}" hidden></p>
    </div>
    <aside class="hero-side">
      <p class="stat"><span id="date-label">榜单日期</span><strong id="stat-date">{esc(doc.get('date'))}</strong><span class="stat-sub" id="stat-period-sub" hidden></span></p>
      <p class="stat"><span id="tz-label">时区</span><strong id="stat-tz">Asia/Shanghai</strong></p>
    </aside>
  </section>
  <section class="list-section" aria-labelledby="list-title">
    <h2 id="list-title">归档中的 {len(doc.get('items') or [])} 款</h2>
    <div class="sources"><span class="sources-label" id="sources-label">这份榜收录了</span> <span id="sources"></span></div>
    <div class="filters" role="toolbar" aria-labelledby="filters-label"><span class="filters-label" id="filters-label">按店铺看</span> <span id="filters"></span></div>
    <p class="count-line" id="result-count"></p>
    <p class="status" id="empty" hidden>这个范围里暂时没有商品。</p>
    <div id="catalog">
    <ol class="static-board">
{static_items(doc)}
    </ol>
    </div>
  </section>
  <section class="skipped" aria-labelledby="skipped-title">
    <h2 id="skipped-title">这次没能收录的来源</h2>
    <p id="skipped-lead">下面几家没有进入这一份归档。没有用别的数据填补。</p>
    <ul id="skipped-list">
{skipped_html(doc)}
    </ul>
  </section>
</main>
</div>
{footer(root, json_rel, archive_line, archive_self=False)}
<div id="live" class="skip" aria-live="polite"></div>
<script src="{root}assets/app.js" defer></script>
</body>
</html>
"""
    dest = boardlib.ROOT / "archive" / kind / f"{stem}.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html_doc, encoding="utf-8")
    print(f"wrote {dest.relative_to(boardlib.ROOT)}")


def skipped_html(doc: dict) -> str:
    rows = []
    for item in doc.get("sources_skipped") or []:
        rows.append(f"<li><strong>{esc(item.get('platform'))}</strong> — {esc(item.get('status'))}. {esc(item.get('note'))}</li>")
    return "\n".join(rows)


def write_index(entries: list[tuple[str, str, str]]) -> None:
    root = "../"
    path = "/archive/index.html"
    title = "归档｜情趣用品日榜与周榜"
    description = "仅限 18 周岁以上。青榜已归档的情趣用品销售日榜和周榜，每期都有可读 HTML 和原始 JSON。不编造商品。"
    daily = [(stem, label) for kind, stem, label in entries if kind == "daily"]
    weekly = [(stem, label) for kind, stem, label in entries if kind == "weekly"]

    def group(kind: str, rows: list[tuple[str, str]]) -> str:
        items = []
        for stem, label in rows:
            items.append(
                f"<li><a href=\"{kind}/{esc(stem)}.html\">{esc(label)}</a> · "
                f"<a href=\"../data/archive/{kind}/{esc(stem)}.json\">JSON</a></li>"
            )
        return "\n".join(items)

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
{GA}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="rating" content="adult">
<meta name="qing:as-of" content="{boardlib.load_json(boardlib.ROOT / "data" / "daily-latest.json").get("date", "")[:10]}">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="index,follow,max-snippet:-1">
<link rel="canonical" href="{BASE}{path}">
{hreflang_links(path)}
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:locale" content="zh_CN">
<meta property="og:image" content="{BASE}/assets/og-share.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{BASE}/assets/og-share.png">
<meta name="theme-color" content="#1b1216">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}styles.css">
{head_script(path, {"zh-CN": title, "en": "Archive | daily and weekly intimate-product charts", "ja": "アーカイブ｜デイリーと週間の売上ランキング", "es": "Archivo | rankings diarios y semanales de productos íntimos"}, {"zh-CN": description, "en": "Adults 18+ only. Readable HTML and JSON for each archived daily and weekly intimate-product chart. No invented products.", "ja": "18歳以上。アーカイブしたデイリーと週間のそれぞれに、読める HTML と JSON があります。商品は作っていません。", "es": "Solo mayores de 18. HTML legible y JSON de cada ranking diario y semanal archivado. No hay productos inventados."})}
</head>
<body class="is-gated" data-page="archive-index" data-path="{path}" data-root="{root}">
{chrome(root, "archive", archive_self=True)}
<div class="wrap">
<main id="main">
  <header class="hero-copy page-intro">
    <p class="kicker" id="page-kicker">已保存的各期 · 仅限 18 周岁以上</p>
    <h1 id="page-title">归档</h1>
    <p class="lead" id="page-lead">每一期日榜和周榜都有一页可读的 HTML，旁边是当时的 JSON。页面只列出文件里的商品。</p>
    <p class="cross related" id="related-links"><a href="{root}index.html">最新日榜</a> · <a href="{root}index.html?board=weekly">最新周榜</a> · <a href="{root}method.html">数据方法</a></p>
  </header>
  <div id="page-sections" class="page-sections">
    <section class="prose-block">
      <h2>怎么读</h2>
      <p>日榜文件名是上海时间的日期。周榜文件名是 ISO 周，周一到周日。若周榜 JSON 带有 seed，那一页会写明它是某一天日榜的副本。若写明由多份日榜汇总，就不是 seed。</p>
    </section>
  </div>
  <div id="archive-catalog" class="archive-groups">
    <section class="prose-block">
      <h2 id="archive-daily-heading">日榜</h2>
      <ul class="archive-index">
{group("daily", daily)}
      </ul>
    </section>
    <section class="prose-block">
      <h2 id="archive-weekly-heading">周榜</h2>
      <ul class="archive-index">
{group("weekly", weekly)}
      </ul>
    </section>
  </div>
</main>
</div>
{footer(root, root + "data/daily-latest.json", "日期归档见上方列表。", archive_self=True)}
<div id="live" class="skip" aria-live="polite"></div>
<script src="{root}assets/app.js" defer></script>
</body>
</html>
"""
    dest = boardlib.ROOT / "archive" / "index.html"
    dest.write_text(html_doc, encoding="utf-8")
    print(f"wrote {dest.relative_to(boardlib.ROOT)}")


def main() -> int:
    entries = []
    for day, path, doc in boardlib.iter_daily_archives():
        stem = path.stem
        write_board("daily", stem, doc)
        entries.append(("daily", stem, day.isoformat()))
    for path in sorted((boardlib.ROOT / "data" / "archive" / "weekly").glob("*.json")):
        doc = boardlib.load_json(path)
        label = (doc.get("period") or {}).get("label") or path.stem
        week = (doc.get("period") or {}).get("iso_week") or path.stem
        write_board("weekly", path.stem, doc)
        entries.append(("weekly", path.stem, f"{week} · {label}"))
    write_index(entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
