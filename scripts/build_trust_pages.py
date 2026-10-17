#!/usr/bin/env python3
"""Write privacy.html and contact.html from i18n/zh-CN.json, with hreflang head copy."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boardlib

BASE = boardlib.BASE
LANGS = ("zh-CN", "en", "ja", "es")
HTML_LANG = {"zh-CN": "zh-Hans", "en": "en", "ja": "ja", "es": "es"}
OG = {"zh-CN": "zh_CN", "en": "en_US", "ja": "ja_JP", "es": "es_ES"}
SCHEMA = {"privacy": "PrivacyPolicy", "contact": "ContactPage"}
RELATED = {
    "daily": "index.html",
    "weekly": "index.html?board=weekly",
    "platform": "by-platform.html",
    "about": "about.html",
    "method": "method.html",
    "faq": "faq.html",
    "privacy": "privacy.html",
    "contact": "contact.html",
    "archive": "archive/index.html",
}
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


def packs(page_id: str) -> dict:
    out = {}
    for code in LANGS:
        info = boardlib.load_json(boardlib.ROOT / "i18n" / f"{code}.json")["pages"][page_id]
        out[code] = {
            "htmlLang": HTML_LANG[code],
            "og": OG[code],
            "title": info["title"],
            "desc": info["description"],
            "alt": info.get("ogImageAlt") or info["title"],
        }
    return out


def head_script(path: str, copy: dict) -> str:
    payload = json.dumps(copy, ensure_ascii=False, indent=2)
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
  function abs(langCode) {{
    return BASE + PATH + (langCode && langCode !== "zh-CN" ? "?lang=" + encodeURIComponent(langCode) : "");
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
  meta("property", "og:image:alt", pack.alt);
  meta("name", "twitter:title", pack.title);
  meta("name", "twitter:description", pack.desc);
  meta("name", "twitter:image:alt", pack.alt);
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


def sections_html(info: dict) -> str:
    blocks = []
    for section in info.get("sections") or []:
        parts = [f"    <section class=\"prose-block\">\n      <h2>{esc(section.get('h2'))}</h2>"]
        for paragraph in section.get("paragraphs") or []:
            parts.append(f"      <p>{esc(paragraph)}</p>")
        for link in section.get("links") or []:
            href = link.get("href") or ""
            extra = ""
            if href.startswith("http"):
                extra = ' target="_blank" rel="noopener noreferrer"'
            parts.append(f"      <p><a href=\"{esc(href)}\"{extra}>{esc(link.get('label') or href)}</a></p>")
        parts.append("    </section>")
        blocks.append("\n".join(parts))
    return "\n".join(blocks)


def related_html(info: dict) -> str:
    bits = []
    for item in info.get("related") or []:
        href = RELATED.get(item.get("page"), "index.html")
        bits.append(f"<a href=\"{esc(href)}\">{esc(item.get('label'))}</a>")
    return " · ".join(bits)


def write_page(page_id: str) -> None:
    zh = boardlib.load_json(boardlib.ROOT / "i18n" / "zh-CN.json")
    info = zh["pages"][page_id]
    ui = zh["ui"]
    copy = packs(page_id)
    path = f"/{page_id}.html"
    page_url = BASE + path
    title = info["title"]
    description = info["description"]
    alt = info.get("ogImageAlt") or title
    schema_type = SCHEMA[page_id]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": BASE + "/#website",
                "url": BASE + "/",
                "name": "青榜",
                "alternateName": ["Qing List", "情趣用品销售榜"],
                "inLanguage": ["zh-Hans", "en", "ja", "es"],
                "isFamilyFriendly": False,
                "description": zh["meta"].get("siteDescription") or description,
            },
            {
                "@type": schema_type,
                "@id": page_url + "#webpage",
                "url": page_url,
                "name": title,
                "description": description,
                "inLanguage": "zh-Hans",
                "isFamilyFriendly": False,
                "dateModified": "2026-10-17",
                "isPartOf": {"@id": BASE + "/#website"},
                "audience": {"@type": "PeopleAudience", "requiredMinAge": 18},
            },
        ],
    }
    ld = json.dumps(graph, ensure_ascii=False, indent=2)
    current = {
        "privacy": ' aria-current="page"' if page_id == "privacy" else "",
        "contact": ' aria-current="page"' if page_id == "contact" else "",
    }
    alts = "\n".join(
        f'<link rel="alternate" hreflang="{code}" href="{page_url if code in ("zh-CN", "x-default") else page_url + "?lang=" + code}">'
        for code in ("zh-CN", "en", "ja", "es", "x-default")
    )
    doc = f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
{GA}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="7BUcqMUjtgmsXPcFlCGDMy5D-SxcqcEuFna2_NjYATE">
<meta name="rating" content="adult">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-snippet:-1">
<link rel="canonical" href="{page_url}">
{alts}
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{page_url}">
<meta property="og:locale" content="zh_CN">
<meta property="og:locale:alternate" content="en_US">
<meta property="og:locale:alternate" content="ja_JP">
<meta property="og:locale:alternate" content="es_ES">
<meta property="og:image" content="{BASE}/assets/og-share.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{BASE}/assets/og-share.png">
<meta name="twitter:image:alt" content="{esc(alt)}">
<meta name="theme-color" content="#1b1216">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="sitemap" type="application/xml" title="Sitemap" href="sitemap.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" href="styles.css" as="style">
<link rel="stylesheet" href="styles.css">
<link rel="preload" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,640&amp;family=Noto+Sans+JP:wght@400;500;700&amp;family=Noto+Sans+SC:wght@400;500;700&amp;family=Outfit:wght@400;500;600;700&amp;display=swap" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,640&amp;family=Noto+Sans+JP:wght@400;500;700&amp;family=Noto+Sans+SC:wght@400;500;700&amp;family=Outfit:wght@400;500;600;700&amp;display=swap"></noscript>
<link rel="preload" href="assets/app.js" as="script">
<script type="application/ld+json" id="ld-json">
{ld}
</script>
{head_script(path, copy)}
</head>
<body class="is-gated" data-page="{page_id}">
<a class="skip" id="skip-link" href="#main">跳到主要内容</a>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="index.html">
      <span class="brand-mark" aria-hidden="true">18+</span>
      <span>
        <span class="brand-name" id="brand-name">青榜</span>
        <span class="brand-sub" id="brand-sub">成人热销快照</span>
      </span>
    </a>
    <nav class="site-nav" id="site-nav" aria-label="页面">
      <a href="index.html" id="nav-daily">日榜</a>
      <a href="index.html?board=weekly" id="nav-weekly">周榜</a>
      <a href="by-platform.html" id="nav-platform">分平台</a>
      <a href="archive/index.html" id="nav-archive">归档</a>
      <a href="about.html" id="nav-about">关于</a>
      <a href="method.html" id="nav-method">方法</a>
      <a href="faq.html" id="nav-faq">FAQ</a>
      <a href="privacy.html" id="nav-privacy"{current['privacy']}>隐私</a>
      <a href="contact.html" id="nav-contact"{current['contact']}>联系</a>
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
</div>
<div class="wrap">
<main id="main">
  <header class="hero-copy page-intro">
    <p class="kicker" id="page-kicker">{esc(info.get('kicker'))}</p>
    <h1 id="page-title">{esc(info.get('h1'))}</h1>
    <p class="lead" id="page-lead">{esc(info.get('lead'))}</p>
    <p class="cross related" id="related-links">{related_html(info)}</p>
  </header>
  <div id="page-sections" class="page-sections">
{sections_html(info)}
  </div>
</main>
</div>
<footer class="site-footer">
  <div class="wrap">
    <p id="foot-age"><strong>仅供年满 18 周岁的成年人浏览。</strong></p>
    <p id="foot-sources">{esc(ui.get('footerSources'))}</p>
    <p id="foot-cadence">{esc(ui.get('footerCadence'))}</p>
    <p id="foot-snapshot">本页是各平台公开热销榜的整理快照，不是医疗或健康建议，也不代表推荐购买。价格、库存和名次都会变，下单前请回到商家页面核对。</p>
    <p id="foot-links">外链使用 nofollow。数据时区 Asia/Shanghai。</p>
    <p id="foot-pages"><a id="foot-daily" href="index.html">日榜</a> · <a id="foot-weekly" href="index.html?board=weekly">周榜</a> · <a id="foot-platform" href="by-platform.html">分平台</a> · <a id="foot-archive-page" href="archive/index.html">归档</a> · <a id="foot-about" href="about.html">关于本站</a> · <a id="foot-method" href="method.html">数据方法</a> · <a id="foot-faq" href="faq.html">常见问题</a> · <a id="foot-privacy" href="privacy.html">隐私政策</a> · <a id="foot-contact" href="contact.html">联系</a></p>
    <p><a id="foot-data" href="data/daily-latest.json">查看当前榜单 JSON</a> · <a id="foot-snapshot-data" href="data.json">综合快照</a></p>
    <p id="foot-archive">日期归档：data/archive/daily/2026-10-17.json · data/archive/weekly/2026-W42.json</p>
  </div>
</footer>
<div id="live" class="skip" aria-live="polite"></div>
<script src="assets/app.js" defer></script>
</body>
</html>
"""
    dest = boardlib.ROOT / f"{page_id}.html"
    dest.write_text(doc, encoding="utf-8")
    print(f"wrote {dest.name}")


def main() -> int:
    write_page("privacy")
    write_page("contact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
