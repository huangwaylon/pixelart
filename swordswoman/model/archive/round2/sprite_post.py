"""Sprite post pass for the model preview cells (stand-in for the pixel pipeline's outline pass).

  .venv/bin/python model/sprite_post.py <render_dir>

For every _masks/raw_*_64.png:
  * adds a closed 1 px exterior outline (4-neighbour).  Selective colour per bible section 5:
    shadow side (bottom/right) = outline #1a1220; lit side (top/left) = darkest tone of the
    neighbouring ramp (skin -> skin[0], red -> red[1], steel -> steel[0]; others -> outline).
  * writes <render_dir>/<name>.
Then runs automated checks on the 8 iso cells and writes checks.json:
  palette-exact, no semi-alpha, colour count, sword pixel count, blade pixels outside the body
  silhouette, fraction of blade pixels inside a 2x2 block (= >= 2 px wide), character height.
"""
import os, sys, json, glob
import numpy as np
from PIL import Image

D = sys.argv[1]
M = os.path.join(D, "_masks")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAL = json.load(open(os.path.join(ROOT, "docs", "palette.json")))


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


OUTL = hx(PAL["outline"])
ALLC = {OUTL}
RAMP_OF = {}
for rn, cols in PAL["ramps"].items():
    for c in cols:
        ALLC.add(hx(c))
        RAMP_OF.setdefault(hx(c), rn)
LIT = {"skin": hx(PAL["ramps"]["skin"][0]), "red": hx(PAL["ramps"]["red"][1]),
       "steel": hx(PAL["ramps"]["steel"][0])}


def outline(im):
    a = np.array(im.convert("RGBA"))
    op = a[..., 3] > 127
    a[..., 3] = np.where(op, 255, 0)
    out = a.copy()
    H, W = op.shape
    for y in range(H):
        for x in range(W):
            if op[y, x]:
                continue
            nb = []
            for dy, dx, lit in ((0, 1, True), (1, 0, True), (0, -1, False), (-1, 0, False)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and op[yy, xx]:
                    nb.append((tuple(a[yy, xx, :3]), lit))
            if not nb:
                continue
            col = OUTL
            if all(l for _, l in nb):     # outline pixel lies above/left of the body = lit side
                r = RAMP_OF.get(nb[0][0])
                col = LIT.get(r, OUTL)
            out[y, x, :3] = col
            out[y, x, 3] = 255
    return Image.fromarray(out, "RGBA")


for raw in sorted(glob.glob(os.path.join(M, "raw_*.png"))):
    name = os.path.basename(raw)[4:]
    outline(Image.open(raw)).save(os.path.join(D, name))

checks = {}
for d in ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]:
    p = os.path.join(D, f"iso_{d}_64.png")
    if not os.path.exists(p):
        continue
    a = np.array(Image.open(os.path.join(M, f"raw_iso_{d}_64.png")).convert("RGBA"))
    alpha = a[..., 3]
    semi = int(((alpha > 0) & (alpha < 255)).sum())
    cols = {tuple(c) for c in a[alpha == 255][:, :3]}
    off = [c for c in cols if c not in ALLC]
    sw = np.array(Image.open(os.path.join(M, f"iso_{d}_sword.png")).convert("RGBA"))[..., 3] > 127
    bd = np.array(Image.open(os.path.join(M, f"iso_{d}_body.png")).convert("RGBA"))[..., 3] > 127
    vis = sw & ~bd        # sword pixels outside the body silhouette
    # 2-px test: pixel belongs to at least one fully-sword 2x2 block
    blk = sw[:-1, :-1] & sw[1:, :-1] & sw[:-1, 1:] & sw[1:, 1:]
    in2 = np.zeros_like(sw)
    in2[:-1, :-1] |= blk
    in2[1:, :-1] |= blk
    in2[:-1, 1:] |= blk
    in2[1:, 1:] |= blk
    ys = np.where((alpha == 255).any(axis=1))[0]
    checks[d] = dict(
        colours=len(cols), off_palette=len(off), semi_alpha=semi,
        sword_px=int(sw.sum()), sword_px_outside_body=int(vis.sum()),
        sword_frac_2px=round(float(in2[sw].mean()) if sw.any() else 0.0, 3),
        char_height_px=int(ys.max() - ys.min() + 1) if len(ys) else 0,
        blade_outside_ok=bool(vis.sum() >= 12),
    )
json.dump(checks, open(os.path.join(D, "checks.json"), "w"), indent=1)
for d, c in checks.items():
    print(d, c)
