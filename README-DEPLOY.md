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

## IndexNow、Bing、Baidu

站点在项目路径 `/qing-bestsellers-top/` 下，不能把 IndexNow 密钥放到 `orangexie05.github.io` 的主机根。密钥文件是仓库根目录的 `16223717d1613cd89fa259593e9f7efd.txt`（文件内容只有这串密钥）。线上地址：

`https://orangexie05.github.io/qing-bestsellers-top/16223717d1613cd89fa259593e9f7efd.txt`

`python3 scripts/publish_boards.py` 写完榜单页、`llms.txt`、`sitemap.xml` 和 `sitemap.txt` 之后，向 `https://api.indexnow.org/indexnow` 提交本次会变的 URL。`host` 是 `orangexie05.github.io`，`keyLocation` 指向上面这个项目路径里的密钥文件。IndexNow 失败只记日志，不让榜单发布失败。本地不想发请求时：

```bash
QING_SKIP_INDEXNOW=1 python3 scripts/publish_boards.py
```

密钥文件进 GitHub Pages 之前，第一次提交可能被 IndexNow 拒绝。部署完成后可以再跑 `python3 scripts/indexnow_ping.py`。

`robots.txt` 保持 `User-agent: *` / `Allow: /`，并点名允许 Bingbot、DuckDuckBot、Slurp、Baiduspider、Yandex，以及 GPT、Claude、Perplexity、Google-Extended、Applebot-Extended 等回答引擎爬虫。页面仍是 `rating=adult`，年龄确认门不变。

`sitemap.txt` 与 `sitemap.xml` 同一批 URL，只保留 HTML（含语言和周榜参数），不收录 JSON。`robots.txt` 里有第二条 `Sitemap:`。

Bing Webmaster Tools 和百度搜索资源平台的验证码先留空，写在 `seo.config.json`：

- `bing_site_verification`：只填 content，对应 `<meta name="msvalidate.01" content="...">`
- `baidu_site_verification`：只填 content，对应 `<meta name="baidu-site-verification" content="...">`

然后重新跑 `python3 scripts/build_homepage.py`（或整次 `publish_boards.py`）。空字符串不会输出这两条 meta，首页只留一段 HTML 注释说明钩子位置。不要编造验证码。

还要在站长平台手工做的事：Bing Webmaster Tools 添加站点并提交 `sitemap.xml`（Yahoo、DuckDuckGo、Copilot 走 Bing 的索引）；Yandex Webmaster 提交 sitemap；百度搜索资源平台提交 `sitemap.txt` 或 `sitemap.xml`，验证通过后把验证码写入 `seo.config.json`。Google Search Console 的验证码已经在首页。

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

周一（或有新日榜时）在仓库根目录跑这一条。它会重算够天数的周榜，重写归档 HTML、首页和分平台页的 SEO 壳（title、description、Open Graph、Twitter、JSON-LD 的 dateModified / temporalCoverage、ItemList、页面上的摘要）、`llms.txt`、信任页、`sitemap.xml` 和 `sitemap.txt`，并通知 IndexNow。不要只改 JSON 就停：`scripts/refresh_jsonld.py` 现在会调用首页壳重建，但完整发布用下面的命令，否则 sitemap 或信任页仍可能停在旧日期。

```bash
python3 scripts/publish_boards.py
```

等价的分步命令（日榜 JSON 已经写入 `data/daily-latest.json` 和 `data/archive/daily/` 之后）：

```bash
python3 scripts/apply_source_extracts.py   # 仅当 data/sources/*-YYYY-MM-DD.json 已有 status ok
python3 scripts/build_weekly.py
python3 scripts/build_archive_html.py
python3 scripts/build_homepage.py          # 首页 / 分平台 SEO 壳和 llms.txt，必须跑
python3 scripts/build_sitemap.py           # sitemap.xml 和 sitemap.txt
python3 scripts/build_trust_pages.py       # 隐私 / 联系文案；日期取自 daily-latest
python3 scripts/indexnow_ping.py           # 可选；publish_boards.py 已经会调用
```

`scripts/refresh_jsonld.py` 与 `scripts/build_homepage.py` 是同一步，留下旧文件名是为了已经写在说明里的命令不会再只改 ItemList。

信任页：`privacy.html`、`contact.html`。给抓取器用的说明：`llms.txt`。联系方式只有 GitHub Issues，没有另写邮箱。

## 本地预览

```bash
python3 -m http.server 8080
# 浏览器打开 http://127.0.0.1:8080/
```
