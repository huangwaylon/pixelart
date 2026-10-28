"""Transcribe a HAND-PAINTED target grid (text, palette codes) into explicit px.py overrides.

The grid file is authored by the pixel artist pixel by pixel (see pixel/work/<DIR>/*.txt); this tool
does not invent any pixel. It diffs the grid against the base frame and calls `px.py set` with one
reason per named region (regions + reasons come from a JSON sidecar written by the artist).

Usage (project root):
  .venv/bin/python tools/pixel/grid2px.py GRID.txt --dir E --frame 0 --regions REGIONS.json [--x0 46 --x1 81] [--dry]
  .venv/bin/python tools/pixel/grid2px.py GRID.txt --preview out.png        # render the grid at 8x

Grid format: lines "y x0: c c c ..." (codes as asciidump: # . s0 h1 r2 l1 d1 t2 e0 p1 v0 ...).
Cells inside the window [x0..x1] x [ymin..ymax] that are not written are transparent.
Regions JSON: [{"box":[x0,y0,x1,y1], "reason":"R34 ..."}, ...] first match wins; a final catch-all is required.
"""
import argparse, json, os, subprocess, sys
from PIL import Image

CODE2NAME = {"#": "outline", ".": "clear", "l1": "leather_1", "l2": "leather_2", "d1": "dark_1", "v0": "purple_0"}
for p, n in (("s", "skin"), ("h", "hair"), ("r", "red"), ("t", "steel"), ("e", "eye"), ("p", "pink")):
    for i in range(4):
        CODE2NAME[f"{p}{i}"] = f"{n}_{i}"


def parse(path):
    cells = {}
    for ln in open(path):
        ln = ln.split("#!", 1)[0].rstrip()
        if not ln or ln.startswith("# ") or ln == "#":
            continue
        head, body = ln.split(":", 1)
        y, x0 = map(int, head.split())
        for i, c in enumerate(body.split()):
            if c not in CODE2NAME:
                raise SystemExit(f"bad code {c!r} at y{y}")
            cells[(x0 + i, y)] = CODE2NAME[c]
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("grid")
    ap.add_argument("--dir"); ap.add_argument("--frame", type=int); ap.add_argument("--anim", default="idle")
    ap.add_argument("--regions"); ap.add_argument("--x0", type=int, default=46); ap.add_argument("--x1", type=int, default=81)
    ap.add_argument("--y0", type=int, default=44); ap.add_argument("--y1", type=int, default=113)
    ap.add_argument("--dx", type=int, default=0); ap.add_argument("--dy", type=int, default=0)
    ap.add_argument("--dry", action="store_true"); ap.add_argument("--preview")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(__file__))
    from pxlib import Palette, load_rgba, frame_path  # noqa
    pal = Palette()
    cells = parse(a.grid)
    if a.preview:
        im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        for (x, y), n in cells.items():
            if n != "clear":
                im.putpixel((x, y), pal.rgba(n))
        im.crop((a.x0, a.y0, a.x1 + 1, a.y1)).resize(((a.x1 + 1 - a.x0) * 8, (a.y1 - a.y0) * 8), Image.NEAREST).save(a.preview)
        return
    regions = json.load(open(a.regions))
    base = load_rgba(frame_path("base", a.anim, a.dir, a.frame))
    groups = {}
    for y in range(a.y0, a.y1):
        for x in range(a.x0, a.x1 + 1):
            want = cells.get((x - a.dx, y - a.dy), "clear")
            have = pal.name_of(base[y, x]) or "OFF"
            if want == have:
                continue
            for r in regions:
                bx0, by0, bx1, by1 = r["box"]
                if bx0 <= x - a.dx <= bx1 and by0 <= y - a.dy <= by1:
                    groups.setdefault(r["reason"], []).append(f"{x},{y},{want}")
                    break
            else:
                raise SystemExit(f"no region for ({x},{y})")
    tot = sum(len(v) for v in groups.values())
    print(f"{a.dir} f{a.frame:02d}: {tot} px differ from base in {len(groups)} regions")
    for reason, px in groups.items():
        cmd = [sys.executable, "tools/pixel/px.py", "set", "--anim", a.anim, "--dir", a.dir, "--frame", str(a.frame), *px, "--reason", reason]
        if a.dry:
            print(f"  [{len(px):3d}] {reason}")
        else:
            subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
