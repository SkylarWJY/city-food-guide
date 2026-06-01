#!/usr/bin/env python3
"""
trim_borders.py — strip uniform/black letterbox borders off card photos.

    python3 scripts/trim_borders.py dist/images            # trim every image in place
    python3 scripts/trim_borders.py dist/images/VESTRY.png  # one file
    python3 scripts/trim_borders.py dist/images --dry-run    # report only

Cards render with object-fit:cover at aspect-ratio 4/5, so leftover IG-story
bands or black frames show as side stripes. This detects edge rows/columns that
are either near-uniform (low colour variance) OR near-black, peels them off from
all four sides, and leaves a 2px safety inset. Originals are backed up to
<dir>/_orig/ unless --no-backup.

Requires: pillow, numpy   (pip install pillow numpy)
"""
import sys, pathlib
import numpy as np
from PIL import Image

UNIFORM_STD = 6      # a line this flat (per channel std) is a border
BLACK_MAX   = 32     # ...or this dark everywhere
INSET       = 2      # safety margin kept after trimming
EXTS = {".png", ".jpg", ".jpeg", ".webp"}

def line_is_border(line):
    # line: (W,3) or (H,3) uint8
    if line.std(axis=0).mean() < UNIFORM_STD:
        return True
    if line.max() < BLACK_MAX:
        return True
    return False

def trim_one(path, dry=False, backup_dir=None):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im)
    h, w = a.shape[:2]
    top, bot, left, right = 0, h, 0, w
    while top < bot and line_is_border(a[top, :, :]):       top += 1
    while bot - 1 > top and line_is_border(a[bot - 1, :, :]): bot -= 1
    while left < right and line_is_border(a[:, left, :]):    left += 1
    while right - 1 > left and line_is_border(a[:, right-1, :]): right -= 1
    if (top, left) == (0, 0) and (bot, right) == (h, w):
        return 0  # nothing trimmed
    top = min(top + INSET, h); left = min(left + INSET, w)
    bot = max(bot - INSET, top + 1); right = max(right - INSET, left + 1)
    cut = (top, h - bot, left, w - right)
    if dry:
        print(f"  would trim {path.name}: T{cut[0]} B{cut[1]} L{cut[2]} R{cut[3]}")
        return 1
    if backup_dir:
        backup_dir.mkdir(parents=True, exist_ok=True)
        if not (backup_dir / path.name).exists():
            im.save(backup_dir / path.name)
    im.crop((left, top, right, bot)).save(path)
    print(f"  trimmed {path.name}: T{cut[0]} B{cut[1]} L{cut[2]} R{cut[3]}  ({w}x{h} -> {right-left}x{bot-top})")
    return 1

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    dry = "--dry-run" in sys.argv
    backup = "--no-backup" not in sys.argv
    if not args:
        print(__doc__); sys.exit(1)
    target = pathlib.Path(args[0])
    files = ([target] if target.is_file()
             else sorted(p for p in target.iterdir() if p.suffix.lower() in EXTS))
    bdir = (target.parent if target.is_file() else target) / "_orig" if backup else None
    changed = sum(trim_one(p, dry, bdir) for p in files)
    print(f"{'would trim' if dry else 'trimmed'} {changed}/{len(files)} image(s)")

if __name__ == "__main__":
    main()
