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
        "{{XHS_HANDLE}}":        cfg.get("xhs_handle", ""),
        "{{CAPTION_BRAND_ZH}}":  cfg.get("caption_brand_zh", cfg.get("site_title", "")),
        "{{CAPTION_BRAND_EN}}":  cfg.get("caption_brand_en", cfg.get("site_title", "")),
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
    n_geo = len(geo); n = len(venues)
    print(f"built {out_dir/'index.html'}  ({n} venues, {n_geo} mapped, "
          f"{len(featured)} featured, {len(type_en)} type labels)")
    if n_geo < n:
        print(f"  note: {n-n_geo} venue(s) have no lat/lng — run geocode.py to add map pins")
    print(f"  next: copy photos into {out_dir/'images'}/  (one <img>.png per venue)")

if __name__ == "__main__":
    main()
