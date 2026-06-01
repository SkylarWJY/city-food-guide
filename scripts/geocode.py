#!/usr/bin/env python3
"""
geocode.py — fill missing lat/lng on a guide.json using OpenStreetMap Nominatim.

    python3 scripts/geocode.py examples/nyc-100.json --city "New York"

Only venues missing lat/lng are looked up (so it's safe to re-run). Results are
cached in <guide>.geocache.json. Nominatim's usage policy asks for <=1 req/sec
and a real User-Agent, both of which this respects. For a whole new city expect
a couple of minutes. Always eyeball the pins on the map afterwards — a handful
will land on the wrong "123 Main St" and need a manual lat/lng in the JSON.

Requires: requests   (pip install requests)
"""
import json, sys, time, pathlib, urllib.parse, urllib.request

UA = "skylar-city-food-guide/1.0 (https://github.com/SkylarWJY)"

def geocode_one(query):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 1})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        out = json.loads(r.read().decode())
    if out:
        return round(float(out[0]["lat"]), 6), round(float(out[0]["lon"]), 6)
    return None

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print("usage: geocode.py <guide.json> [--city \"New York\"]", file=sys.stderr); sys.exit(1)
    spec_path = pathlib.Path(args[0])
    city = ""
    if "--city" in sys.argv:
        city = sys.argv[sys.argv.index("--city") + 1]
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    cache_path = spec_path.with_suffix(".geocache.json")
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}

    todo = [v for v in spec["venues"] if v.get("lat") is None or v.get("lng") is None]
    print(f"{len(todo)} venue(s) need coords")
    found = fail = 0
    for v in todo:
        key = f"{v['name']} {v.get('addr','')} {city}".strip()
        if key in cache:
            coord = cache[key]
        else:
            try:
                coord = geocode_one(f"{v.get('addr','')} {city}".strip()) \
                        or geocode_one(f"{v['name']} {city}".strip())
            except Exception as e:
                print(f"  ! {v['name']}: {e}"); coord = None
            cache[key] = coord
            cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
            time.sleep(1.1)  # Nominatim: <=1 req/sec
        if coord:
            v["lat"], v["lng"] = coord; found += 1
            print(f"  ok {v['name']}: {coord}")
        else:
            fail += 1
            print(f"  ?? {v['name']}: not found — add lat/lng by hand")

    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"done: {found} geocoded, {fail} unresolved. Updated {spec_path}")

if __name__ == "__main__":
    main()
