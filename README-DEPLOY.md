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

## 本地预览

```bash
cd site && python3 -m http.server 8080
# 浏览器打开 http://127.0.0.1:8080/
```
