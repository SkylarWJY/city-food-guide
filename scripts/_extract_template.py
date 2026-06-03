#!/usr/bin/env python3
"""
One-time tool: turn the working single-file guide (the NYC-100 master) into a
data-driven template by replacing the per-city data structures and the
deploy-specific strings with {{PLACEHOLDERS}}.

Run once to (re)generate template/guide.template.html from a source HTML.
Not part of the normal build loop — build_guide.py consumes the template.
"""
import re, sys, pathlib

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    "/Users/jiayiwang/Desktop/2026/自媒体/吃饭/纽约美食100-pro.html"
OUT = pathlib.Path(__file__).resolve().parent.parent / "template" / "guide.template.html"

html = pathlib.Path(SRC).read_text(encoding="utf-8")

def sub_once(pattern, replacement, label, flags=re.DOTALL):
    global html
    new, n = re.subn(pattern, lambda m: replacement, html, count=1, flags=flags)
    if n != 1:
        print(f"  !! {label}: matched {n} times (expected 1) — check pattern", file=sys.stderr)
    else:
        print(f"  ok {label}")
    html = new

# --- per-city data structures (multi-line blocks) ---
sub_once(r"const data = \[.*?\n\];", "const data = {{DATA_JSON}};", "data[]")
sub_once(r"const imgMap = \{.*?\n\};", "const imgMap = {{IMGMAP_JSON}};", "imgMap")
sub_once(r"const extraImg = \{.*?\n\};", "const extraImg = {{EXTRAIMG_JSON}};", "extraImg")
sub_once(r"const typeEn=\{.*?\n\};", "const typeEn={{TYPEEN_JSON}};", "typeEn")

# --- single-line data structures ---
sub_once(r"const featured=\[.*?\];", "const featured={{FEATURED_JSON}};", "featured")
sub_once(r"const groupZh=\[.*?\];", "const groupZh={{GROUPZH_JSON}};", "groupZh")
sub_once(r"const groupEn=\{.*?\};", "const groupEn={{GROUPEN_JSON}};", "groupEn")
sub_once(r"const GEO = \{.*?\};", "const GEO = {{GEO_JSON}};", "GEO")

# --- deploy-specific strings ---
sub_once(r"const SHARE_LINK='[^']*';", "const SHARE_LINK='{{SHARE_LINK}}';", "SHARE_LINK")
sub_once(r'data-beehiiv-form="[^"]*"', 'data-beehiiv-form="{{BEEHIIV_FORM_ID}}"', "beehiiv id")
# lead-magnet links delivered on the page right after subscribe
sub_once(r'const MYMAPS_URL="[^"]*";', 'const MYMAPS_URL="{{MYMAPS_URL}}";', "MYMAPS_URL")
sub_once(r'const PDF_URL="[^"]*";', 'const PDF_URL="{{PDF_URL}}";', "PDF_URL")

# --- brand / identity strings (replace ALL occurrences; order matters) ---
def repl_all(old, new, label):
    global html
    n = html.count(old)
    html = html.replace(old, new)
    print(f"  {'ok' if n else '!!'} {label}: {n} occurrence(s)")

# og image must run before the bare site URL (it's a longer superstring)
repl_all("https://skylar-nyc-100.netlify.app/og.png", "{{OG_IMAGE}}", "OG_IMAGE")
# full site title before brand_sub (title contains the sub substring)
repl_all("Skylar's NYC 100 · 纽约好吃榜", "{{SITE_TITLE}}", "SITE_TITLE")
repl_all("https://skylar-nyc-100.netlify.app/", "{{SITE_URL}}", "SITE_URL (trailing slash)")
repl_all("skylar-nyc-100.netlify.app", "{{SITE_DISPLAY_URL}}", "SITE_DISPLAY_URL")
repl_all("<em>Skylar's</em> NYC 100", "{{BRAND_WORDMARK}}", "BRAND_WORDMARK")
repl_all("· 纽约好吃榜", "{{BRAND_SUB}}", "BRAND_SUB")
repl_all("https://instagram.com/skylarwjy", "{{IG_URL}}", "IG_URL")
repl_all("https://xhslink.com/m/8QM3DnmS1H9", "{{XHS_URL}}", "XHS_URL")
repl_all("@skylarwjy", "{{IG_HANDLE}}", "IG_HANDLE")
repl_all("@Skylar创业版", "{{XHS_HANDLE}}", "XHS_HANDLE")
# caption brand phrases (inside JS template literals)
repl_all("Skylar 私藏纽约好吃榜", "{{CAPTION_BRAND_ZH}}", "CAPTION_BRAND_ZH")
repl_all("Skylar's NYC 100", "{{CAPTION_BRAND_EN}}", "CAPTION_BRAND_EN")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"\nwrote {OUT} ({len(html)} bytes)")
# report any leftover real share link / form id (sanity)
for needle in ["460499a5", "skylar-nyc-100.netlify"]:
    if needle in html:
        print(f"  warning: '{needle}' still present in template", file=sys.stderr)
