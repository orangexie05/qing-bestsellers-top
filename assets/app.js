(function () {
  "use strict";

  var LANGS = ["zh-CN", "en", "ja", "es"];
  var LANG_KEY = "qbt-lang";
  var AGE_KEY = "qbt-age";
  var BASE = "https://orangexie05.github.io/qing-bestsellers-top";
  var PLATFORM_ORDER = ["dame", "amazon_us", "we_vibe", "womanizer", "lovense", "waddy_store"];
  var PAGE = document.body.getAttribute("data-page") || "top";

  var state = {
    lang: "zh-CN",
    dict: null,
    data: null,
    filter: "all",
    ageOk: false
  };

  var dictCache = {};
  var gate = document.getElementById("age-gate");
  var live = document.getElementById("live");

  function allowedLang(value) {
    return LANGS.indexOf(value) !== -1 ? value : null;
  }

  function readLang() {
    var query = allowedLang(new URLSearchParams(location.search).get("lang"));
    if (query) return query;
    try {
      return allowedLang(localStorage.getItem(LANG_KEY)) || "zh-CN";
    } catch (err) {
      return "zh-CN";
    }
  }

  function localeFor(lang) {
    if (lang === "zh-CN") return "zh-CN";
    if (lang === "ja") return "ja-JP";
    if (lang === "es") return "es";
    return "en-US";
  }

  function fill(template, vars) {
    return String(template).replace(/\{(\w+)\}/g, function (_, key) {
      return vars[key] == null ? "" : String(vars[key]);
    });
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function clear(node) {
    if (node) node.replaceChildren();
  }

  function pagePath() {
    return PAGE === "platform" ? "/by-platform.html" : "/";
  }

  function pageUrl(lang) {
    var path = pagePath();
    var url = BASE + path;
    if (lang && lang !== "zh-CN") {
      url += (path.indexOf("?") === -1 ? "?" : "&") + "lang=" + encodeURIComponent(lang);
    }
    return url;
  }

  function withLang(href) {
    var hash = "";
    var base = href;
    var cut = href.indexOf("#");
    if (cut !== -1) {
      hash = href.slice(cut);
      base = href.slice(0, cut);
    }
    if (state.lang === "zh-CN") return base + hash;
    var join = base.indexOf("?") === -1 ? "?" : "&";
    return base + join + "lang=" + encodeURIComponent(state.lang) + hash;
  }

  function absoluteImage(src) {
    if (!src) return BASE + "/assets/og-share.png";
    if (/^https?:\/\//i.test(src)) return src;
    return BASE + "/" + String(src).replace(/^\//, "");
  }

  function priceString(price) {
    var n = Number(price);
    if (!isFinite(n)) return null;
    return n.toFixed(2);
  }

  function asinFrom(url) {
    var match = String(url || "").match(/\/dp\/([A-Z0-9]{10})(?:[/?#]|$)/);
    return match ? match[1] : null;
  }

  function writeUrl(lang) {
    var url = new URL(location.href);
    if (lang === "zh-CN") url.searchParams.delete("lang");
    else url.searchParams.set("lang", lang);
    var next = url.pathname + url.search + url.hash;
    if (next !== location.pathname + location.search + location.hash) {
      history.replaceState(null, "", next);
    }
  }

  function setBackgroundInert(on) {
    document.querySelectorAll(".site-header, .wrap, .site-footer").forEach(function (node) {
      if (on) node.setAttribute("inert", "");
      else node.removeAttribute("inert");
    });
  }

  function setPressedLang(lang) {
    document.querySelectorAll("[data-lang]").forEach(function (button) {
      button.setAttribute("aria-pressed", button.getAttribute("data-lang") === lang ? "true" : "false");
    });
  }

  function applyHead(dict, lang) {
    var meta = dict.meta;
    var pageMeta = PAGE === "platform"
      ? { title: meta.platformTitle, description: meta.platformDescription }
      : { title: meta.topTitle, description: meta.topDescription };
    document.title = pageMeta.title;
    document.documentElement.lang = meta.htmlLang;
    setMeta("description", pageMeta.description);
    setMeta("og:title", pageMeta.title, true);
    setMeta("og:description", pageMeta.description, true);
    setMeta("og:locale", meta.ogLocale, true);
    setMeta("og:url", pageUrl(lang), true);
    setMeta("twitter:title", pageMeta.title);
    setMeta("twitter:description", pageMeta.description);
    if (meta.ogImageAlt) {
      setMeta("og:image:alt", meta.ogImageAlt, true);
      setMeta("twitter:image:alt", meta.ogImageAlt);
    }
    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) canonical.setAttribute("href", pageUrl(lang));
  }

  function setMeta(name, content, property) {
    var selector = property ? 'meta[property="' + name + '"]' : 'meta[name="' + name + '"]';
    var node = document.querySelector(selector);
    if (node) node.setAttribute("content", content);
  }

  function text(id, value) {
    var node = document.getElementById(id);
    if (node && value != null) node.textContent = value;
  }

  function formatDate(isoDate, lang) {
    var date = new Date(isoDate + "T12:00:00+08:00");
    try {
      return new Intl.DateTimeFormat(localeFor(lang), {
        year: "numeric",
        month: "long",
        day: "numeric",
        timeZone: "Asia/Shanghai"
      }).format(date);
    } catch (err) {
      return isoDate;
    }
  }

  function formatPrice(price, currency, lang) {
    try {
      return new Intl.NumberFormat(localeFor(lang), {
        style: "currency",
        currency: currency,
        maximumFractionDigits: 2
      }).format(price);
    } catch (err) {
      return currency + " " + price;
    }
  }

  function formatRating(reviews, ui, lang) {
    if (!reviews || reviews.rating == null) return ui.noRating;
    var rating;
    var count;
    try {
      rating = new Intl.NumberFormat(localeFor(lang), {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(reviews.rating);
      count = reviews.count == null ? null : new Intl.NumberFormat(localeFor(lang)).format(reviews.count);
    } catch (err) {
      rating = String(reviews.rating);
      count = reviews.count == null ? null : String(reviews.count);
    }
    if (count == null) return fill(ui.ratingOnly, { rating: rating });
    return fill(ui.ratingCount, { rating: rating, count: count });
  }

  function copyFor(item) {
    var products = state.dict.products || {};
    return products[item.id] || {
      display: item.name,
      blurb: "",
      alt: item.name
    };
  }

  function platformCopy(id) {
    var platforms = state.dict.platforms || {};
    return platforms[id] || { name: id, blurb: "" };
  }

  function paintChrome() {
    var dict = state.dict;
    var ui = dict.ui;
    var page = dict.pages[PAGE] || dict.pages.top;
    var data = state.data;
    text("brand-name", ui.brand);
    text("brand-sub", ui.brandSub);
    text("skip-link", ui.skip);
    text("nav-top", ui.navTop);
    text("nav-platform", ui.navPlatform);
    text("nav-data", ui.navData);
    text("hero-kicker", ui.heroKicker);
    text("hero-title", page.h1);
    text("hero-lead", page.lead);
    text("date-label", ui.dateLabel);
    text("tz-label", ui.tzLabel);
    text("sort-label", ui.sortLabel);
    text("sort-rule", ui.sortRule);
    text("sources-label", ui.sourcesLabel);
    text("filters-label", ui.filtersLabel);
    text("jump-label", ui.jumpLabel);
    text("age-title", ui.ageTitle);
    text("age-body", ui.ageBody);
    text("age-enter", ui.ageEnter);
    text("age-leave", ui.ageLeave);
    var ageLine = document.getElementById("foot-age");
    if (ageLine && ui.footerAge) ageLine.replaceChildren(el("strong", null, ui.footerAge));
    text("foot-snapshot", ui.footerSnapshot);
    text("foot-data", ui.footerData);
    text("skipped-title", ui.skippedTitle);
    text("skipped-lead", ui.skippedLead);
    if (data) {
      text("stat-date", formatDate(data.date, state.lang));
      text("stat-tz", data.timezone || "Asia/Shanghai");
      text("foot-links", fill(ui.footerLinks, { time: data.generated_at }));
    }
    text("list-title", page.listTitle);
    text("faq-title", dict.faq && dict.faq.title);
    text("faq-lead", dict.faq && dict.faq.lead);
    var nav = document.getElementById("site-nav");
    if (nav) nav.setAttribute("aria-label", ui.navLabel);
    var langGroup = document.getElementById("lang-switch");
    if (langGroup) langGroup.setAttribute("aria-label", ui.langLabel);
    var jump = document.getElementById("jump-nav");
    if (jump) jump.setAttribute("aria-label", ui.jumpLabel);
    var brand = document.querySelector(".brand");
    if (brand) brand.setAttribute("href", withLang("index.html"));
    var navTop = document.getElementById("nav-top");
    if (navTop) navTop.setAttribute("href", withLang("index.html"));
    var navPlatform = document.getElementById("nav-platform");
    if (navPlatform) navPlatform.setAttribute("href", withLang("by-platform.html"));
    var cross = document.getElementById("cross-link");
    if (cross && page.cross) {
      cross.textContent = page.cross;
      cross.setAttribute("href", withLang(PAGE === "platform" ? "index.html" : "by-platform.html"));
    }
    paintSources();
    paintSkipped();
    paintFaq();
    setPressedLang(state.lang);
  }

  function paintFaq() {
    var host = document.getElementById("faq-list");
    var faq = state.dict && state.dict.faq;
    if (!host || !faq) return;
    clear(host);
    (faq.items || []).forEach(function (item) {
      var block = el("div", "faq-item");
      block.appendChild(el("h3", null, item.q));
      block.appendChild(el("p", null, item.a));
      host.appendChild(block);
    });
  }

  function productNode(item) {
    var copy = copyFor(item);
    var node = {
      "@type": "Product",
      "name": item.name,
      "url": item.product_url,
      "image": absoluteImage(item.image),
      "brand": { "@type": "Brand", "name": item.store }
    };
    if (copy.display && copy.display !== item.name) node.alternateName = copy.display;
    var sku = asinFrom(item.product_url);
    if (sku) node.sku = sku;
    var price = priceString(item.price);
    if (price && item.currency) {
      node.offers = {
        "@type": "Offer",
        "url": item.purchase_url || item.product_url,
        "priceCurrency": item.currency,
        "price": price
      };
    }
    var reviews = item.reviews || {};
    if (typeof reviews.rating === "number" && typeof reviews.count === "number" && reviews.count > 0) {
      node.aggregateRating = {
        "@type": "AggregateRating",
        "ratingValue": reviews.rating,
        "bestRating": 5,
        "ratingCount": reviews.count
      };
    }
    return node;
  }

  function writeStructuredData() {
    var dict = state.dict;
    var data = state.data;
    var slot = document.getElementById("ld-json");
    if (!dict || !data || !slot) return;
    var meta = dict.meta;
    var pageMeta = PAGE === "platform"
      ? { title: meta.platformTitle, description: meta.platformDescription }
      : { title: meta.topTitle, description: meta.topDescription };
    var page = pageUrl(state.lang);
    var items = data.items || [];
    var faqEntities = ((dict.faq && dict.faq.items) || []).map(function (item) {
      return {
        "@type": "Question",
        "name": item.q,
        "acceptedAnswer": { "@type": "Answer", "text": item.a }
      };
    });
    var graph = {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "WebPage",
          "@id": page + "#webpage",
          "url": page,
          "name": pageMeta.title,
          "description": pageMeta.description,
          "inLanguage": meta.htmlLang,
          "isFamilyFriendly": false,
          "dateModified": data.date,
          "audience": { "@type": "PeopleAudience", "requiredMinAge": 18 },
          "primaryImageOfPage": {
            "@type": "ImageObject",
            "url": BASE + "/assets/og-share.png",
            "width": 1200,
            "height": 630
          }
        },
        {
          "@type": "ItemList",
          "@id": page + "#itemlist",
          "name": pageMeta.title,
          "description": pageMeta.description,
          "url": page,
          "numberOfItems": items.length,
          "itemListOrder": "https://schema.org/ItemListOrderAscending",
          "itemListElement": items.map(function (item, index) {
            return {
              "@type": "ListItem",
              "position": item.overall_rank || index + 1,
              "item": productNode(item)
            };
          })
        }
      ]
    };
    if (faqEntities.length) {
      graph["@graph"].push({
        "@type": "FAQPage",
        "@id": page + "#faq",
        "inLanguage": meta.htmlLang,
        "isFamilyFriendly": false,
        "mainEntity": faqEntities
      });
    }
    slot.textContent = JSON.stringify(graph);
  }

  function paintSources() {
    var host = document.getElementById("sources");
    if (!host || !state.data) return;
    clear(host);
    (state.data.sources_included || []).forEach(function (id) {
      var info = platformCopy(id);
      var chip = el("a", "chip", info.name);
      chip.href = withLang(PAGE === "platform" ? "#" + id : "by-platform.html#" + id);
      host.appendChild(chip);
    });
  }

  function paintSkipped() {
    var list = document.getElementById("skipped-list");
    if (!list || !state.data) return;
    clear(list);
    var notes = state.dict.skipped || {};
    (state.data.sources_skipped || []).forEach(function (item) {
      var li = el("li");
      var strong = el("strong", null, item.platform);
      li.appendChild(strong);
      li.appendChild(document.createTextNode(" — " + (notes[item.platform] || item.note || "")));
      list.appendChild(li);
    });
  }

  function paintFilters() {
    var host = document.getElementById("filters");
    if (!host || !state.data) return;
    clear(host);
    var ui = state.dict.ui;
    var all = el("button", null, ui.filterAll);
    all.type = "button";
    all.setAttribute("aria-pressed", state.filter === "all" ? "true" : "false");
    all.addEventListener("click", function () {
      state.filter = "all";
      paintFilters();
      paintCatalog();
    });
    host.appendChild(all);
    PLATFORM_ORDER.forEach(function (id) {
      if ((state.data.sources_included || []).indexOf(id) === -1) return;
      var info = platformCopy(id);
      var button = el("button", null, info.name);
      button.type = "button";
      button.setAttribute("aria-pressed", state.filter === id ? "true" : "false");
      button.addEventListener("click", function () {
        state.filter = id;
        paintFilters();
        paintCatalog();
      });
      host.appendChild(button);
    });
  }

  function makeCard(item, rankLabel) {
    var ui = state.dict.ui;
    var copy = copyFor(item);
    var shop = platformCopy(item.platform);
    var article = el("article", "card");
    article.id = "item-" + item.id;

    var media = el("a", "card-media");
    media.href = item.product_url;
    media.target = "_blank";
    media.rel = "nofollow noopener noreferrer";
    var badge = el("span", "rank-badge", String(rankLabel));
    badge.setAttribute("aria-hidden", "true");
    var img = document.createElement("img");
    img.src = item.image;
    img.alt = copy.alt || copy.display;
    img.decoding = "async";
    var eager = item.overall_rank <= 3 && state.filter === "all" && PAGE === "top";
    img.loading = eager ? "eager" : "lazy";
    if (eager) img.setAttribute("fetchpriority", "high");
    img.referrerPolicy = "no-referrer";
    img.addEventListener("error", function () {
      if (img.getAttribute("data-fallback") === "1") return;
      img.setAttribute("data-fallback", "1");
      img.src = "assets/products/fallback.svg";
      img.alt = ui.placeholderCaption;
    });
    media.appendChild(badge);
    media.appendChild(img);
    article.appendChild(media);

    var body = el("div", "card-body");
    body.appendChild(el("p", "store-line", shop.name + " · " + fill(ui.storeRank, { n: item.rank })));
    var heading = el("h3", null, copy.display);
    body.appendChild(heading);
    if (copy.display !== item.name) {
      var original = el("p", "original");
      var sep = state.lang === "zh-CN" ? "：" : ": ";
      original.appendChild(el("strong", null, ui.originalLabel + sep));
      original.appendChild(document.createTextNode(item.name));
      body.appendChild(original);
    }
    if (copy.blurb) body.appendChild(el("p", "blurb", copy.blurb));
    if (item.note_key && state.dict.notes && state.dict.notes[item.note_key]) {
      body.appendChild(el("p", "note", state.dict.notes[item.note_key]));
    }
    if (item.image_kind === "placeholder") {
      body.appendChild(el("p", "ph-note", ui.placeholderCaption));
    }
    var facts = el("div", "facts");
    facts.appendChild(el("span", "price", formatPrice(item.price, item.currency, state.lang)));
    var rating = el("span", "rating", formatRating(item.reviews, ui, state.lang));
    facts.appendChild(rating);
    body.appendChild(facts);
    var cta = el("a", "cta", ui.cta);
    cta.href = item.purchase_url || item.product_url;
    cta.target = "_blank";
    cta.rel = "nofollow noopener noreferrer";
    body.appendChild(cta);
    article.appendChild(body);
    return article;
  }

  function visibleItems() {
    var items = (state.data && state.data.items) || [];
    if (PAGE !== "top" || state.filter === "all") return items;
    return items.filter(function (item) { return item.platform === state.filter; });
  }

  function paintCatalog() {
    var host = document.getElementById("catalog");
    var empty = document.getElementById("empty");
    var count = document.getElementById("result-count");
    if (!host || !state.dict || !state.data) return;
    clear(host);
    var ui = state.dict.ui;
    if (PAGE === "platform") {
      PLATFORM_ORDER.forEach(function (id) {
        var group = (state.data.items || []).filter(function (item) { return item.platform === id; });
        if (!group.length) return;
        var info = platformCopy(id);
        var section = el("section", "platform-block");
        section.id = id;
        var heading = el("h2");
        heading.appendChild(document.createTextNode(info.name + " "));
        heading.appendChild(el("span", null, fill(ui.inList, { n: group.length })));
        section.appendChild(heading);
        if (info.blurb) section.appendChild(el("p", "platform-blurb", info.blurb));
        var grid = el("div", "grid");
        group.forEach(function (item) { grid.appendChild(makeCard(item, item.rank)); });
        section.appendChild(grid);
        host.appendChild(section);
      });
      if (empty) empty.hidden = true;
      return;
    }
    var items = visibleItems();
    if (count) count.textContent = fill(ui.resultCount, { n: items.length });
    if (!items.length) {
      if (empty) {
        empty.hidden = false;
        empty.textContent = ui.empty;
      }
      return;
    }
    if (empty) empty.hidden = true;
    var grid = el("div", "grid");
    items.forEach(function (item) { grid.appendChild(makeCard(item, item.overall_rank)); });
    host.appendChild(grid);
  }

  function showStatus(message, isError) {
    var host = document.getElementById("catalog");
    if (!host) return;
    clear(host);
    var node = el("p", "status", message);
    if (isError) node.setAttribute("role", "alert");
    host.appendChild(node);
  }

  function loadDict(lang) {
    if (dictCache[lang]) return Promise.resolve(dictCache[lang]);
    return fetch("i18n/" + lang + ".json", { credentials: "same-origin" }).then(function (res) {
      if (!res.ok) throw new Error("dict");
      return res.json();
    }).then(function (json) {
      dictCache[lang] = json;
      return json;
    });
  }

  function loadData() {
    if (state.data) return Promise.resolve(state.data);
    return fetch("data.json", { credentials: "same-origin" }).then(function (res) {
      if (!res.ok) throw new Error("data");
      return res.json();
    }).then(function (json) {
      state.data = json;
      return json;
    });
  }

  function render() {
    paintChrome();
    writeStructuredData();
    if (!state.ageOk) return;
    if (PAGE === "top") paintFilters();
    paintCatalog();
  }

  function applyLanguage(lang, announce) {
    state.lang = lang;
    try { localStorage.setItem(LANG_KEY, lang); } catch (err) {}
    writeUrl(lang);
    return loadDict(lang).then(function (dict) {
      state.dict = dict;
      applyHead(dict, lang);
      render();
      if (announce && live) {
        live.textContent = dict.ui.langChanged;
      }
    });
  }

  function openGate() {
    document.body.classList.add("is-gated");
    setBackgroundInert(true);
    var enter = document.getElementById("age-enter");
    if (enter) enter.focus();
  }

  function closeGate() {
    state.ageOk = true;
    try { localStorage.setItem(AGE_KEY, "ok"); } catch (err) {}
    document.body.classList.remove("is-gated");
    setBackgroundInert(false);
    var title = document.getElementById("hero-title");
    if (title) title.setAttribute("tabindex", "-1");
    if (title) title.focus();
    render();
  }

  function bind() {
    document.querySelectorAll("[data-lang]").forEach(function (button) {
      button.addEventListener("click", function () {
        var next = button.getAttribute("data-lang");
        if (next && next !== state.lang) applyLanguage(next, true).catch(fail);
      });
    });
    var enter = document.getElementById("age-enter");
    var leave = document.getElementById("age-leave");
    if (enter) enter.addEventListener("click", closeGate);
    if (leave) leave.addEventListener("click", function () { location.href = "https://www.wikipedia.org/"; });
    if (gate) {
      gate.addEventListener("keydown", function (event) {
        if (event.key !== "Tab") return;
        var buttons = gate.querySelectorAll("button");
        if (!buttons.length) return;
        var first = buttons[0];
        var last = buttons[buttons.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      });
    }
  }

  function fail() {
    var message = (state.dict && state.dict.ui && state.dict.ui.loadError) || "The list data did not load.";
    if (state.ageOk) showStatus(message, true);
  }

  function boot() {
    bind();
    try { state.ageOk = localStorage.getItem(AGE_KEY) === "ok"; } catch (err) { state.ageOk = false; }
    if (!state.ageOk) openGate();
    else {
      document.body.classList.remove("is-gated");
      setBackgroundInert(false);
    }
    var lang = readLang();
    try { localStorage.setItem(LANG_KEY, lang); } catch (err) {}
    writeUrl(lang);
    Promise.all([loadDict(lang), loadData()]).then(function (result) {
      state.lang = lang;
      state.dict = result[0];
      applyHead(result[0], lang);
      render();
      if (!state.ageOk) {
        var enter = document.getElementById("age-enter");
        if (enter) enter.focus();
      }
    }).catch(fail);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
