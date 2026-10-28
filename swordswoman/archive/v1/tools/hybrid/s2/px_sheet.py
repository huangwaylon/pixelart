#!/usr/bin/env python3
"""Pixelize every panel of ONE Gemini sheet at ONE shared scale (keeps the squash/stretch Gemini drew).

  px_sheet.py --slice-dir S --names a,b,c --out-dir O [--head-px 26] [--ref NAME] [--scale-from NAMES]
              [--pix-args "..."]

Scale: s = head_px / median(head width in hi-res over --scale-from panels) (head width = widest
sword-free row in the skull band, 14-38 % down from the figure top). Each panel is then pixelized
with --guide none and height = s * its own body height, feet centre on the pivot, bottom on 104.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pixelize as P  # noqa
import hylib as H  # noqa
from scipy import ndimage as ndi


def my_body(rgb, mask):
    """sword-free body: drop long thin low-chroma (silver blade) components + their dark outline."""
    a = rgb.astype(float); mx = a.max(-1); mn = a.min(-1)
    inner = ndi.binary_erosion(mask, iterations=3)
    steel = inner & (mx - mn < 34) & (mx > 105)
    lab, n = ndi.label(steel, structure=np.ones((3, 3)))
    blade = np.zeros_like(mask)
    tot = mask.sum()
    for i in range(1, n + 1):
        yy, xx = np.nonzero(lab == i)
        if len(yy) < 0.0015 * tot:
            continue
        ev = np.sort(np.linalg.eigvalsh(np.cov(np.stack([xx, yy]).astype(float)) + 1e-6 * np.eye(2)))
        if np.sqrt(ev[1] / max(ev[0], 1e-6)) >= 3.0:
            blade |= lab == i
    blade = ndi.binary_dilation(blade, iterations=7)
    body = mask & ~blade
    body = ndi.binary_opening(body, iterations=2)
    lb, nb = ndi.label(body)
    if nb > 1:
        sz = ndi.sum(body, lb, range(1, nb + 1))
        body = np.isin(lb, 1 + np.nonzero(sz >= 0.08 * sz.max())[0])   # drop blade-tip slivers, keep big parts
    ys, xs = np.nonzero(body)
    y1 = ys.max(); h = ys.max() - ys.min() + 1
    band = body[y1 - max(3, int(0.03 * h)): y1 + 1]
    fx = np.nonzero(band.any(0))[0]
    return dict(top=int(ys.min()), bottom=int(y1), feet_cx=float(fx.mean()), body=body)


def retone_hair(out, hi, shares=(0.58, 0.34, 0.08), sheen_cap=12):
    """hair reads DARK (STYLE_TARGET 2.2): rank hair px by the aligned hi-res luminance."""
    pal = H.palette(); idx = H.index_of(out)
    hn = [pal.index[pal.resolve(f"hair_{i}")] for i in range(3)]
    m = np.isin(idx, hn)
    if m.sum() < 10:
        return out
    hl = np.asarray(Image.fromarray(hi).convert("RGB")).astype(float).mean(-1)
    lum = hl.reshape(128, 4, 128, 4).mean((1, 3))
    v = lum[m]; order = np.argsort(np.argsort(v)) / max(len(v) - 1, 1)
    new = np.where(order < shares[0], hn[0], np.where(order < shares[0] + shares[1], hn[1], hn[2]))
    # cap the sheen
    ys, xs = np.nonzero(m)
    sh = np.nonzero(new == hn[2])[0]
    if len(sh) > sheen_cap:
        keep = sh[np.argsort(-v[sh])[:sheen_cap]]
        new[np.setdiff1d(sh, keep)] = hn[1]
    idx2 = idx.copy(); idx2[ys, xs] = new
    o = H.rgba_of(np.where(idx2 < 0, 0, idx2)); o[idx2 == -1] = 0
    return o

def corset_fix(out):
    """no-guide quantization calls the corset hair (README known limit): hair-tone clusters that sit
    in the lower half of the figure become leather."""
    pal = H.palette(); idx = H.index_of(out)
    hn = [pal.index[pal.resolve(f"hair_{i}")] for i in range(3)]
    lt = [pal.index[pal.resolve(n)] for n in ("leather_1", "leather_1", "leather_2")]
    op = idx >= 0
    ys = np.nonzero(op.any(1))[0]; top, bot = ys.min(), ys.max()
    m = np.isin(idx, hn)
    lab, n = ndi.label(m)
    for i in range(1, n + 1):
        cy = np.nonzero(lab == i)[0].mean()
        if cy > top + 0.52 * (bot - top):
            for h, l in zip(hn, lt):
                idx[(lab == i) & (idx == h)] = l
    o = H.rgba_of(np.where(idx < 0, 0, idx)); o[idx == -1] = 0
    return o


ap = argparse.ArgumentParser()
ap.add_argument("--slice-dir", required=True); ap.add_argument("--names", required=True)
ap.add_argument("--out-dir", required=True); ap.add_argument("--head-px", type=float, default=26)
ap.add_argument("--scale-from", default=None); ap.add_argument("--scale", type=float, default=None)
ap.add_argument("--down", default="box"); ap.add_argument("--baseline", type=int, default=104)
ap.add_argument("--suffix", default="_genflat.png")
ap.add_argument("--no-retone", action="store_true"); ap.add_argument("--keep-x", action="store_true")
ap.add_argument("--fixed-height", type=int, default=None, help="per-panel height (turn sheets)")
a = ap.parse_args()
os.makedirs(a.out_dir, exist_ok=True)
names = a.names.split(",")
geo = {}
for n in names:
    img = Image.open(os.path.join(a.slice_dir, n + a.suffix))
    rgb, mask, _ = P.remove_bg(img, "auto", 11.0)
    g = P.body_rows(rgb, mask)
    b = g["body"]; h = g["bottom"] - g["top"] + 1
    rows = b[g["top"] + int(0.14 * h): g["top"] + int(0.38 * h)]
    w = 0
    for r in rows:
        xs = np.nonzero(r)[0]
        if len(xs):
            w = max(w, xs.max() - xs.min() + 1)
    geo[n] = dict(h=h, headw=int(w))
src = (a.scale_from.split(",") if a.scale_from else names)
s = a.scale or a.head_px / float(np.median([geo[n]["headw"] for n in src]))
print("scale", round(s, 5), {n: geo[n] for n in names})
for n in names:
    hgt = int(round(s * geo[n]["h"]))
    if a.fixed_height:
        img = Image.open(os.path.join(a.slice_dir, n + a.suffix)); rgb, mask, _ = P.remove_bg(img, "auto", 11.0)
        mb = my_body(rgb, mask); hgt = int(round(a.fixed_height * geo[n]["h"] / (mb["bottom"] - mb["top"] + 1)))
    path = os.path.join(a.slice_dir, n + a.suffix)
    out, cls, meta, hi = P.pixelize(path, None, height=hgt, fit="none",
                                    down=a.down, baseline=a.baseline, verbose=False)
    # re-place with the blade-free feet (pixelize's own measure lets a Gemini blade tip set the bottom)
    rgb, mask, _ = P.remove_bg(Image.open(path), "auto", 11.0)
    mb = my_body(rgb, mask)
    ys, xs = np.nonzero(mask); bx0, by0 = xs.min(), ys.min()
    sc = meta["scale"]; ox, oy = meta["offset"]
    feet_row = oy + (mb["bottom"] + 1 - by0) * sc - 1
    feet_x = ox + (mb["feet_cx"] + 0.5 - bx0) * sc - 0.5
    dy = int(round(a.baseline - feet_row)); dx = int(round(64 - feet_x)) if not a.keep_x else 0
    out = np.roll(np.roll(out, dy, 0), dx, 1)
    hi = np.roll(np.roll(hi, dy * 4, 0), dx * 4, 1)
    meta["post_shift"] = [dx, dy]
    if not a.no_retone:
        out = retone_hair(out, hi)
    out = corset_fix(out)
    F = H.features(out); meta.update(height=F.get("height"), baseline=F.get("baseline"), feet_cx=F.get("feet_cx"))
    meta["sheet_scale"] = s; meta["head_w_src"] = geo[n]["headw"]
    P.write_outputs(os.path.join(a.out_dir, n + ".png"), out, cls, meta, hi, None)
    print(n, "h", meta["height"], "body_h", meta["body_height"], "base", meta["baseline"], "feet", meta["feet_cx"])
