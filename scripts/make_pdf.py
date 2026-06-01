#!/usr/bin/env python3
"""
make_pdf.py — render the built guide to a PDF (the lead-magnet you email subscribers).

    python3 scripts/make_pdf.py dist/index.html dist/guide.pdf

Drives headless Chrome's --print-to-pdf. Needs Google Chrome (or Chromium)
installed; set CHROME env var to override the binary path. Run build_guide.py
first and make sure dist/images/ holds the photos, or the PDF will show blank
cards. A short settle delay lets the Leaflet map and images paint before capture.
"""
import os, sys, shutil, subprocess, pathlib

CANDIDATES = [
    os.environ.get("CHROME"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome"), shutil.which("chromium"),
    shutil.which("chromium-browser"), shutil.which("chrome"),
]

def find_chrome():
    for c in CANDIDATES:
        if c and pathlib.Path(c).exists():
            return c
    sys.exit("make_pdf: Chrome not found — install it or set CHROME=/path/to/chrome")

def main():
    if len(sys.argv) < 2:
        print("usage: make_pdf.py <index.html> [out.pdf=dist/guide.pdf]", file=sys.stderr); sys.exit(1)
    src = pathlib.Path(sys.argv[1]).resolve()
    if not src.exists():
        sys.exit(f"make_pdf: {src} not found — run build_guide.py first")
    out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "dist/guide.pdf").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
        "--virtual-time-budget=8000", "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={out}", src.as_uri(),
    ]
    print(f"rendering {src.name} -> {out} via {pathlib.Path(chrome).name} ...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not out.exists() or out.stat().st_size == 0:
        sys.stderr.write(r.stderr[-800:] + "\n")
        sys.exit("make_pdf: Chrome produced no PDF")
    print(f"wrote {out} ({out.stat().st_size//1024} KB)")

if __name__ == "__main__":
    main()
