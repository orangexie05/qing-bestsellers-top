# 部署说明 · Adult Bestsellers Static Site

本目录是纯静态站点（HTML/CSS/JSON），无需构建。部署前把所有文件里的占位域名 `https://PLACEHOLDER_HOST` 换成真实地址（含 `index.html` / `by-platform.html` 的 canonical / OG，以及 `robots.txt`、`sitemap.xml`）。

可用命令批量替换：

```bash
cd site
# 例：https://yourname.github.io/adult-top
find . -type f \( -name '*.html' -o -name '*.xml' -o -name 'robots.txt' \) -exec sed -i 's|https://PLACEHOLDER_HOST|https://YOUR_REAL_HOST|g' {} +
```

## GitHub Pages（推荐）

1. 新建空仓库（Public），例如 `adult-bestsellers-top`。
2. 把本 `site/` 目录内容推到仓库根目录，或 `docs/` 分支/目录。
3. Settings → Pages → Source：Deploy from branch → `main` / `/ (root)` 或 `/docs`。
4. 等待 1–2 分钟，打开 `https://<user>.github.io/<repo>/`。
5. 用上面的 `sed` 把 `PLACEHOLDER_HOST` 换成该 URL（无尾斜杠）。
6. Google Search Console 添加资源，提交 `sitemap.xml`。

## Cloudflare Pages

1. [dash.cloudflare.com](https://dash.cloudflare.com) → Workers & Pages → Create → Pages → Upload assets。
2. 直接上传本 `site/` 文件夹，或连接 Git 仓库，Build 命令留空，Output directory 填 `site`（若仓库根是上级项目）。
3. 绑定自定义域名（可选），再替换 `PLACEHOLDER_HOST`。
4. Search Console 提交 sitemap。

## Netlify

1. [app.netlify.com](https://app.netlify.com) → Add new site → Deploy manually，拖入 `site/`。
2. 或 CLI：`npx netlify deploy --prod --dir=site`（需先 `netlify login`）。
3. 替换 `PLACEHOLDER_HOST` 为 `https://<site>.netlify.app`。

## SEO 提醒

- 站点含成人内容：部分国家/地区与 SafeSearch 可能限制展示；仍可被索引，但流量受政策影响。
- 外链已加 `rel="nofollow noopener"`。
- 上线后在 Search Console 验证并提交 sitemap；可请求对首页 URL 编入索引。

## 日榜 / 周榜数据

页面默认打开日榜，用页首切换到周榜（地址栏加上 `?board=weekly`，语言参数仍是 `?lang=`）。

例行任务整份覆盖这两个文件，并另存一份日期归档（不要和旧条目合并，也不要编造商品）：

- 日榜最新：`data/daily-latest.json`
- 日榜归档：`data/archive/daily/YYYY-MM-DD.json`（Asia/Shanghai 的日期）
- 周榜最新：`data/weekly-latest.json`
- 周榜归档：`data/archive/weekly/YYYY-Www.json`（上海时间，周一到周日，ISO 周）
- 可读归档页：`archive/daily/YYYY-MM-DD.html`、`archive/weekly/YYYY-Www.html`，目录在 `archive/index.html`

`date` / `as_of` 是数据截止日，`period` 是日榜当天或周榜那一周，时区都是 `Asia/Shanghai`。

2026-10-16 的日榜来自当天打开的公开页面：Amazon Sex Toys 热销、Dame bestsellers、Lovense 首页旗舰轮播、We-Vibe /us/bestsellers、Womanizer /us/bestseller、Waddy 首页男士 TOP 10，以及当天能解析的香港公开分类 SISTALK 热卖、Les'Play 畅销、Sex Concept 畅销。同一份内容写在 `data/daily-2026-10-16.json`、`data/daily-latest.json` 和 `data/archive/daily/2026-10-16.json`。这份日榜没有 `seed`。

2026-10-17 的日榜已上线，来自当天公开页面的实抓，没有 `seed`。同一份内容写在 `data/daily-2026-10-17.json`、`data/daily-latest.json` 和 `data/archive/daily/2026-10-17.json`。

2026-10-18 的日榜已上线，来自当天公开页面的实抓，没有 `seed`。同一份内容写在 `data/daily-2026-10-18.json`、`data/daily-latest.json` 和 `data/archive/daily/2026-10-18.json`。

2026-10-19 的日榜已上线，来自当天公开页面的实抓，没有 `seed`。同一份内容写在 `data/daily-2026-10-19.json`、`data/daily-latest.json` 和 `data/archive/daily/2026-10-19.json`。

`data.json` 和 `data/archive/daily/2026-10-15.json` 仍是 2026-10-15 的综合快照，文件里带有 `seed`。不要把 10-16 的香港新行写回 10-15。

### 周榜怎么来

同一 ISO 周在 `data/archive/daily/` 里有两份或更多日榜时，`scripts/build_weekly.py` 按商品链接去重，按出现天数、平均店内名次、最好店内名次、评分、评价数排序，写出没有 `seed` 的周榜。每店最多 6 条，综合最多 20 条。

只有一份日榜时，脚本不改已有周榜。那份周榜若仍带 `seed`，页面会写明它是某一天日榜的副本，不是单独统计的一周销量。

2026-W42（2026-10-12–2026-10-18）由 2026-10-15、2026-10-16、2026-10-17 与 2026-10-18 四份日榜汇总，不是 seed。

淘宝 / 天猫仍未收录。2026-10-16 打开 `https://s.taobao.com/search` 只得到需要 JavaScript 的搜索壳，静态 HTML 里没有商品链接、商品 id 或价格，所以没有编造行。空结构在 `data/sources/taobao_tmall.placeholder.json`。18 Gifts 被 Cloudflare 拦住，LELO `/best-sellers` 返回 404，MysteryVibe 在 429 之后没有重试，PChome 24h 的响应不是确认过的热销榜。2026-10-17 没有重抓这几家；当天 `sources_skipped` 只记了淘宝 / 天猫、18 Gifts 和 LELO。

周一（或有新日榜时）在仓库根目录：

```bash
python3 scripts/apply_source_extracts.py   # 仅当 data/sources/*-YYYY-MM-DD.json 已有 status ok
python3 scripts/build_weekly.py
python3 scripts/build_archive_html.py
python3 scripts/build_sitemap.py
python3 scripts/refresh_jsonld.py
python3 scripts/build_trust_pages.py       # 隐私 / 联系文案改了 i18n 之后
```

信任页：`privacy.html`、`contact.html`。给抓取器用的说明：`llms.txt`。联系方式只有 GitHub Issues，没有另写邮箱。

## 本地预览

```bash
python3 -m http.server 8080
# 浏览器打开 http://127.0.0.1:8080/
```
