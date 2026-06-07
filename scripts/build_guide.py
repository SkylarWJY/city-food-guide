#!/usr/bin/env python3
"""
build_guide.py — render a bilingual city food-guide site from one JSON file.

    python3 scripts/build_guide.py examples/nyc-100.json dist/

Reads a guide spec (config + venues), injects it into template/guide.template.html,
and writes <out>/index.html. Copy your photos into <out>/images/ separately
(filenames must match each venue's "img" / "extra_imgs", as <img>.png).

Venue schema (one object per restaurant):
  {
    "name": "Sushi Blossoms",        # required, unique — also the image-map key
    "type": "寿司 · Omakase",         # required, shown on the card (primary language)
    "type_en": "Sushi · Omakase",    # optional, English label for the type
    "group": "日料",                  # required, must match a config.groups[].zh
    "addr": "334 8th Ave, Chelsea",  # required, used for Google Maps + the map pin
    "img": "IMG_5988",               # required, images/IMG_5988.png
    "extra_imgs": ["IMG_5988b"],     # optional, extra photos for the lightbox
    "featured_rank": 3,              # optional, lower = nearer the top of the grid
    "lat": 40.7474, "lng": -73.9968, # optional, omit to drop the pin from the map
    "view": 1                        # optional, flags a "best view" badge
  }
"""
import json, sys, pathlib

def die(msg):
    print(f"build_guide: {msg}", file=sys.stderr); sys.exit(1)

# ---- analytics: optional GA4 + GoatCounter, injected into <head> (empty if neither configured) ----
def build_analytics(cfg):
    """Render the <head> analytics snippet. Both are optional — set
    config.ga4_id ("G-XXXXXXXXXX") and/or config.goatcounter_code (a subdomain
    slug, e.g. "skylarnyc"). GA4 also installs window.track(name, params), a
    tiny safe wrapper the template's click handlers call to fire custom events
    (click_directions / click_reserve / share_store / share_score / coffee_poke).
    Returns "" when neither is set, so sites without analytics build cleanly."""
    ga4 = (cfg.get("ga4_id") or "").strip()
    gc  = (cfg.get("goatcounter_code") or "").strip()
    out = []
    if gc:
        out.append('<!-- analytics: GoatCounter (privacy-friendly, cookie-less, ~3KB) -->')
        out.append(f'<script data-goatcounter="https://{gc}.goatcounter.com/count" '
                   'async src="//gc.zgo.at/count.js"></script>')
    if ga4:
        out.append(f'<!-- Google Analytics 4 ({ga4}) -->')
        out.append(f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga4}"></script>')
        out.append('<script>')
        out.append('  window.dataLayer = window.dataLayer || [];')
        out.append('  function gtag(){dataLayer.push(arguments);}')
        out.append("  gtag('js', new Date());")
        out.append(f"  gtag('config', '{ga4}');")
        out.append('  // tiny helper so click handlers can fire custom events safely')
        out.append("  window.track=function(name,params){try{gtag('event',name,params||{});}catch(e){}};")
        out.append('</script>')
    return "\n".join(out)

# ---- SEO / GEO: structured data + crawler files (drives Google rich results + AI-engine citations) ----
def build_jsonld(cfg, venues):
    site = cfg.get("site_url", "/").rstrip("/")
    idb  = site if site.startswith("http") else ""
    home = (idb + "/") if idb else "/"
    loc  = cfg.get("locality", ""); reg = cfg.get("region", ""); ctry = cfg.get("country", "")
    items = []
    for i, v in enumerate(venues):
        addr = {"@type": "PostalAddress", "streetAddress": v.get("addr", "")}
        if loc:  addr["addressLocality"] = loc
        if reg:  addr["addressRegion"]   = reg
        if ctry: addr["addressCountry"]  = ctry
        r = {"@type": "Restaurant", "name": v["name"],
             "servesCuisine": v.get("type_en") or v.get("type"), "address": addr}
        if v.get("lat") is not None and v.get("lng") is not None:
            r["geo"] = {"@type": "GeoCoordinates", "latitude": v["lat"], "longitude": v["lng"]}
        items.append({"@type": "ListItem", "position": i + 1, "item": r})
    graph = [
        {"@type": "WebSite", "@id": idb + "/#website",
         "name": cfg.get("caption_brand_en") or cfg.get("site_title", ""),
         "url": home, "inLanguage": ["zh-CN", "en"]},
        {"@type": "ItemList", "@id": idb + "/#list", "name": cfg.get("site_title", ""),
         "url": home, "numberOfItems": len(items),
         "itemListOrder": "https://schema.org/ItemListOrderAscending",
         "itemListElement": items},
    ]
    ld = {"@context": "https://schema.org", "@graph": graph}
    return '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False, separators=(",", ":")) + "</script>"

AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "PerplexityBot",
           "ClaudeBot", "Claude-Web", "Google-Extended", "Applebot-Extended"]

def build_robots(cfg):
    site = cfg.get("site_url", "/").rstrip("/")
    lines = ["User-agent: *", "Allow: /", "",
             "# AI / answer engines — explicitly welcome (we want to be cited)"]
    for b in AI_BOTS:
        lines += [f"User-agent: {b}", "Allow: /"]
    if site.startswith("http"):
        lines += ["", f"Sitemap: {site}/sitemap.xml"]
    return "\n".join(lines) + "\n"

def build_sitemap(cfg):
    site = cfg.get("site_url", "/").rstrip("/") or ""
    home = (site + "/") if site.startswith("http") else "/"
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f'  <url><loc>{home}</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>\n'
            '</urlset>\n')

def build_llms(cfg, venues, groups_zh):
    title = cfg.get("site_title", "City Food Guide")
    site = cfg.get("site_url", "").rstrip("/")
    cats = " · ".join(g for g in groups_zh if g != "全部")
    return (f"# {title}\n\n"
            f"> A curated, hand-tested city food guide. Bilingual (中文 / English). "
            f"{len(venues)} venues, each personally checked; cuisines and addresses verified.\n\n"
            f"## About\n- {len(venues)} venues, updated monthly\n- Categories: {cats}\n"
            f"- Each listing has cuisine, address, and a one-tap Google Maps link\n"
            f"- Full schema.org structured data (ItemList + Restaurant) is embedded in the homepage as JSON-LD\n"
            + (f"\n## Links\n- Site: {site}\n" if site.startswith("http") else ""))

def main():
    if len(sys.argv) < 2:
        die("usage: build_guide.py <guide.json> [out_dir=dist]")
    spec_path = pathlib.Path(sys.argv[1])
    out_dir = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "dist")
    root = pathlib.Path(__file__).resolve().parent.parent
    tpl_path = root / "template" / "guide.template.html"

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    cfg = spec.get("config", {})
    venues = spec.get("venues", [])
    if not venues:
        die("no venues in spec")

    # --- validate ---
    group_zh = [g["zh"] for g in cfg.get("groups", [])]
    seen = set()
    for i, v in enumerate(venues):
        for k in ("name", "type", "group", "addr", "img"):
            if not v.get(k):
                die(f"venue #{i} ({v.get('name','?')}) missing '{k}'")
        if v["name"] in seen:
            die(f"duplicate venue name: {v['name']}")
        seen.add(v["name"])
        if group_zh and v["group"] not in group_zh:
            die(f"venue '{v['name']}' group '{v['group']}' not in config.groups")

    # --- derive the JS structures the template expects ---
    data = []
    for v in venues:
        d = {"name": v["name"], "type": v["type"], "group": v["group"], "addr": v["addr"]}
        if v.get("view"):
            d["view"] = v["view"]
        data.append(d)

    img_map   = {v["name"]: v["img"] for v in venues}
    extra_img = {v["name"]: v["extra_imgs"] for v in venues if v.get("extra_imgs")}
    type_en   = {v["type"]: v["type_en"] for v in venues if v.get("type_en")}
    geo       = {v["name"]: [v["lat"], v["lng"]] for v in venues
                 if v.get("lat") is not None and v.get("lng") is not None}
    featured  = [v["name"] for v in sorted(
                    (v for v in venues if v.get("featured_rank") is not None),
                    key=lambda v: v["featured_rank"])]

    group_zh_full = group_zh or ["全部"] + sorted({v["group"] for v in venues})
    group_en = {g["zh"]: g["en"] for g in cfg.get("groups", [])} or {"全部": "All"}

    def js(obj):  # compact, UTF-8 literal valid in <script>
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

    # --- fill the template ---
    html = tpl_path.read_text(encoding="utf-8")
    repl = {
        "{{DATA_JSON}}":     js(data),
        "{{IMGMAP_JSON}}":   js(img_map),
        "{{EXTRAIMG_JSON}}": js(extra_img),
        "{{TYPEEN_JSON}}":   js(type_en),
        "{{FEATURED_JSON}}": js(featured),
        "{{GROUPZH_JSON}}":  js(group_zh_full),
        "{{GROUPEN_JSON}}":  js(group_en),
        "{{GEO_JSON}}":      js(geo),
        "{{SHARE_LINK}}":        cfg.get("share_link", cfg.get("site_url", "")),
        "{{BEEHIIV_FORM_ID}}":   cfg.get("beehiiv_form_id", ""),
        "{{SITE_TITLE}}":        cfg.get("site_title", "City Food Guide"),
        "{{SITE_URL}}":          cfg.get("site_url", "/"),
        "{{OG_IMAGE}}":          cfg.get("og_image", ""),
        "{{SITE_DISPLAY_URL}}":  cfg.get("site_display_url", ""),
        "{{BRAND_WORDMARK}}":    cfg.get("brand_wordmark", "City Food Guide"),
        "{{BRAND_SUB}}":         cfg.get("brand_sub", ""),
        "{{IG_URL}}":            cfg.get("ig_url", "#"),
        "{{IG_HANDLE}}":         cfg.get("ig_handle", ""),
        "{{XHS_URL}}":           cfg.get("xhs_url", "#"),
        "{{XHS_HANDLE}}":        cfg.get("xhs_handle", ""),
        # lead-magnet links shown on the page right after subscribe (B-plan delivery)
        "{{MYMAPS_URL}}":        cfg.get("mymaps_url", ""),
        "{{PDF_URL}}":           cfg.get("pdf_url", ""),
        "{{CAPTION_BRAND_ZH}}":  cfg.get("caption_brand_zh", cfg.get("site_title", "")),
        "{{CAPTION_BRAND_EN}}":  cfg.get("caption_brand_en", cfg.get("site_title", "")),
        "{{JSONLD}}":            build_jsonld(cfg, venues),
        "{{ANALYTICS}}":         build_analytics(cfg),
    }
    missing = [k for k in repl if k not in html]
    if missing:
        die(f"template is missing placeholders: {missing} — re-run _extract_template.py?")
    for k, val in repl.items():
        html = html.replace(k, val)

    left = [seg.split("}}")[0] + "}}" for seg in html.split("{{")[1:]]
    if left:
        die(f"unfilled placeholders remain: {sorted(set(left))}")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    # SEO / GEO sidecar files
    (out_dir / "robots.txt").write_text(build_robots(cfg), encoding="utf-8")
    (out_dir / "sitemap.xml").write_text(build_sitemap(cfg), encoding="utf-8")
    (out_dir / "llms.txt").write_text(build_llms(cfg, venues, group_zh), encoding="utf-8")
    n_geo = len(geo); n = len(venues)
    print(f"built {out_dir/'index.html'}  ({n} venues, {n_geo} mapped, "
          f"{len(featured)} featured, {len(type_en)} type labels)")
    if n_geo < n:
        print(f"  note: {n-n_geo} venue(s) have no lat/lng — run geocode.py to add map pins")
    print(f"  next: copy photos into {out_dir/'images'}/  (one <img>.png per venue)")

if __name__ == "__main__":
    main()
