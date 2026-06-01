#!/usr/bin/env python3
"""
make_mymaps.py — turn a guide.json into a Google My Maps import CSV.

    python3 scripts/make_mymaps.py examples/nyc-100.json dist/my-maps.csv

Import the CSV at https://www.google.com/mymaps → Create map → Import.
Use 纬度/经度 (lat/lng) as the position columns and 店名 as the marker title.
Venues without lat/lng are skipped (run geocode.py first to fill them).
"""
import json, csv, sys, pathlib

def main():
    if len(sys.argv) < 2:
        print("usage: make_mymaps.py <guide.json> [out.csv=dist/my-maps.csv]", file=sys.stderr)
        sys.exit(1)
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "dist/my-maps.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    rows, skipped = [], 0
    for i, v in enumerate(spec.get("venues", []), 1):
        if v.get("lat") is None or v.get("lng") is None:
            skipped += 1
            continue
        lat, lng = float(v["lat"]), float(v["lng"])
        nav = f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lng:.6f}"
        rows.append([i, v["name"], v.get("type", ""), v.get("group", ""),
                     v.get("addr", ""), f"{lat:.6f}", f"{lng:.6f}", nav])

    # utf-8-sig so Google/Excel read CJK headers correctly
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["编号", "店名", "菜系", "分类", "地址", "纬度", "经度", "导航链接"])
        w.writerows(rows)

    print(f"wrote {out}: {len(rows)} pins" + (f" ({skipped} skipped, no coords)" if skipped else ""))

if __name__ == "__main__":
    main()
