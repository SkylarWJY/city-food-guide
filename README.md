# city-food-guide

Build a bilingual (中文 / English) **"City Food 100"** guide website from one JSON
file — a curated restaurant list rendered as a filterable photo grid with a
check-in tracker, canvas share-cards, an interactive map, and an email-capture
gate. This is the open-sourced engine behind **[Skylar's NYC 100](https://skylar-nyc-100.netlify.app)**.

It's packaged as a **Claude Code skill** ([`SKILL.md`](SKILL.md)) so Claude can drive
the whole pipeline for you, but every script also runs standalone.

![demo](assets/demo.png)

## Quick start

```bash
pip install pillow numpy                       # for trim_borders.py
cp examples/starter.json guide.json            # edit venues + config
python3 scripts/geocode.py    guide.json --city "New York"
python3 scripts/build_guide.py guide.json dist/
#   …copy photos into dist/images/ (one <name>.png per venue)…
python3 scripts/trim_borders.py dist/images
python3 scripts/make_mymaps.py  guide.json dist/my-maps.csv
python3 scripts/make_pdf.py     dist/index.html dist/guide.pdf
python3 -m http.server -d dist 4318            # preview at localhost:4318
```

`examples/nyc-100.json` is the full worked example (100 venues). See
[`SKILL.md`](SKILL.md) for the data schema, every script, and the gotchas.

## What's in the box

```
template/guide.template.html   the generic single-file site engine
scripts/build_guide.py         guide.json -> dist/index.html
scripts/trim_borders.py        strip letterbox/black borders off card photos
scripts/geocode.py             fill lat/lng via OpenStreetMap Nominatim
scripts/make_mymaps.py         guide.json -> Google My Maps CSV
scripts/make_pdf.py            dist/index.html -> PDF lead magnet
assets/welcome-email.template.md   bilingual beehiiv welcome email
examples/                      starter.json (skeleton) + nyc-100.json (full)
```

Photos and build output are `.gitignore`d — bring your own images.

## License

MIT
