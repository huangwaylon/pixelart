"""Silhouette overlay: concept art vs a guide mask, normalised on crown->sole height and feet centre.
  .venv/bin/python tools/hybrid/sil_compare.py --ref concept/chibi_turnaround_v6.png --ref-box 0,150,390,900 \
      --ref-crown 270 --ref-sole 860 --ref-cx 223 [--ref-mirror] \
      --mask hybrid/guide/ortho_front/front/f00_mask.png --crown 147 --sole 937 --cx 512 \
      [--id f00_id.png --auto]  (auto: crown = top hair-id row, sole = bottom shoe-id row, cx = shoe centre)
      --out overlay.png [--label text]
Prints JSON: IoU, ref/guide row-width profiles (in crown->sole units), centroid offsets.
Colours: red = concept only, blue = guide only, grey = both."""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

a = sys.argv[1:]


def opt(n, d=None):
    return a[a.index(n) + 1] if n in a else d


def ref_mask(path, box, mirror):
    im = Image.open(path).convert("RGB")
    if box:
        im = im.crop(tuple(int(v) for v in box.split(",")))
    arr = np.array(im).astype(int)
    mx, mn = arr.max(-1), arr.min(-1)
    white = mn > 228
    flatgrey = ((mx - mn) < 10) & (mn > 150) & (mx < 215)          # drop shadow ellipse
    m = ~(white | flatgrey)
    # remove specks: keep pixels with >= 3 mask neighbours
    p = np.pad(m, 1)
    nb = sum(p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    m = m & (nb >= 4)
    if mirror:
        m = m[:, ::-1]
    return m


ref_box = opt("--ref-box")
mirror = "--ref-mirror" in a
R = ref_mask(opt("--ref"), ref_box, mirror)
x0 = int(ref_box.split(",")[0]) if ref_box else 0
y0 = int(ref_box.split(",")[1]) if ref_box else 0
rc, rs = float(opt("--ref-crown")) - y0, float(opt("--ref-sole")) - y0
rcx = float(opt("--ref-cx")) - x0
if mirror:
    rcx = R.shape[1] - 1 - rcx

G = np.array(Image.open(opt("--mask")))
G = (G[..., 3] if G.ndim == 3 and G.shape[2] == 4 else (G if G.ndim == 2 else G[..., 0])) > 127
if "--auto" in a:
    leg = json.load(open(opt("--legend")))["parts"] if opt("--legend") else None
    idim = np.array(Image.open(opt("--id")))
    ids = np.where(idim[..., 3] > 127, (idim[..., 0].astype(int) + 5) // 10, 0)
    hair = [leg["hair"]["id"]]
    shoes = [leg["shoe_L"]["id"], leg["shoe_R"]["id"]]
    ys = np.where(np.isin(ids, hair).any(1))[0]
    gc = float(ys.min())
    sy, sx = np.where(np.isin(ids, shoes))
    gs = float(sy.max())
    gcx = float(sx.mean())
else:
    gc, gs, gcx = float(opt("--crown")), float(opt("--sole")), float(opt("--cx"))

# scale ref into guide pixel space
k = (gs - gc) / (rs - rc)
Rs = Image.fromarray((R * 255).astype(np.uint8)).resize((max(1, int(R.shape[1] * k)), max(1, int(R.shape[0] * k))), Image.BILINEAR)
Rs = np.array(Rs) > 127
H, W = G.shape
RR = np.zeros_like(G)
ox = int(round(gcx - rcx * k))
oy = int(round(gs - rs * k))
ys0, xs0 = max(0, oy), max(0, ox)
ys1, xs1 = min(H, oy + Rs.shape[0]), min(W, ox + Rs.shape[1])
RR[ys0:ys1, xs0:xs1] = Rs[ys0 - oy:ys1 - oy, xs0 - ox:xs1 - ox]
inter, uni = (RR & G).sum(), (RR | G).sum()
Hh = gs - gc


def prof(m):
    out = {}
    for f in np.arange(0.0, 1.3001, 0.05):
        r = int(round(gs - f * Hh))
        if r < 0 or r >= H:
            continue
        cols = np.where(m[r])[0]
        out[f"{f:.2f}"] = round(float((cols[-1] - cols[0]) / Hh), 3) if len(cols) else 0.0
    return out


res = {"iou": round(float(inter / max(1, uni)), 4), "ref_only_px": int((RR & ~G).sum()), "guide_only_px": int((G & ~RR).sum()),
       "ref_profile": prof(RR), "guide_profile": prof(G), "crown_sole_px": Hh,
       "guide_top": float(np.where(G.any(1))[0].min()), "ref_top": float(np.where(RR.any(1))[0].min())}
res["top_above_crown_ref"] = round((gc - res["ref_top"]) / Hh, 3)
res["top_above_crown_guide"] = round((gc - res["guide_top"]) / Hh, 3)
im = np.full((H, W, 3), 255, np.uint8)
im[RR & ~G] = (230, 60, 60)
im[G & ~RR] = (60, 90, 230)
im[RR & G] = (150, 150, 150)
out = Image.fromarray(im)
d = ImageDraw.Draw(out)
for f in (0.0, 0.25, 0.5, 0.6, 0.75, 1.0):
    y = gs - f * Hh
    d.line([(0, y), (W, y)], fill=(0, 170, 0))
    d.text((3, y - 11), f"{f:.2f}", fill=(0, 120, 0))
d.text((3, 3), f"{opt('--label', '')} IoU {res['iou']:.3f}  red=concept blue=guide", fill=(0, 0, 0))
out.save(opt("--out"))
print(json.dumps(res))
