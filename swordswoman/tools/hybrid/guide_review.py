"""Guide review: clay renders (tools/hybrid/render_guides.py output) -> 128-cell clay cells with the
smear-helper sweep in pink, clay GIFs (hi-res, 8 directions, real timing), and the STANDARD TEST SET
contact sheet.  Guide only: never art.

  .venv/bin/python tools/hybrid/guide_review.py cells  ROOT          # ROOT = hybrid/guide/<pass>
  .venv/bin/python tools/hybrid/guide_review.py gifs   ROOT --tag p1 [--gif-dir hybrid/gifs]
  .venv/bin/python tools/hybrid/guide_review.py sheet  ROOT --out hybrid/guide/test_set_p1.png
  .venv/bin/python tools/hybrid/guide_review.py strips ROOT --anim slash --out x.png [--frames 1,2,3]
  .venv/bin/python tools/hybrid/guide_review.py all    ROOT --tag p1

ROOT layout: <ROOT>/<anim>/<DIR>/fNN_{clay,mask,mask_smear}.png.  Test-set anims (render names):
turn (f00 x 8 dirs), walk_SE_keys (SE f00-03), slash_SE_keys (SE f00-03), jump_E_keys (E f00-02).
cells -> <ROOT>/cells/<standard name>.png (turn_<DIR>, walk_SE_k0.., slash_SE_k0.., jump_E_crouch..,
<anim>_<DIR>_fNN for sequences) so tools/hybrid/gifs.py / metrics.py / sheets.py can read them.
"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hylib as H  # noqa: E402

sys.path.insert(0, os.path.join(H.ROOT, "tools", "pixel"))
from gif import save_gif  # noqa: E402

DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
BG = (92, 98, 112)
SMEAR = (248, 181, 200)          # palette pink_1 (#f8b5c8) so metrics.py counts it as smear
TEST = {"walk_SE_keys": ("walk", "SE", ["k0", "k1", "k2", "k3"]),
        "slash_SE_keys": ("slash", "SE", ["k0", "k1", "k2", "k3"]),
        "jump_E_keys": ("jump", "E", ["crouch", "apex", "land"])}
KEY_TIMING = {"walk_SE": "walk_SE", "slash_SE": "slash_SE", "jump_E": "jump_E"}
SEQS = ["idle", "walk", "run", "slash"]


def opt(a, n, d=None):
    return a[a.index(n) + 1] if n in a else d


def rel(p):
    return p if os.path.isabs(p) else os.path.join(H.ROOT, p)


def load(path):
    return np.array(Image.open(path).convert("RGBA"))


def composite(clay_path, bg=BG, smear=True):
    """RGBA clay + pink smear behind -> RGB on bg, full res"""
    a = load(clay_path)
    out = np.empty(a.shape[:2] + (3,), np.float32)
    out[:] = bg
    sp = clay_path.replace("_clay.png", "_mask_smear.png")
    if smear and os.path.exists(sp):
        s = load(sp)[..., 3] > 100
        out[s] = SMEAR
    al = a[..., 3:4] / 255.0
    out = out * (1 - al) + a[..., :3] * al
    return out.astype(np.uint8)


def to_cell(clay_path):
    """box-reduce to the 128 cell; alpha binarized at 50 %; smear (pink) behind"""
    a = load(clay_path).astype(np.float32)
    k = a.shape[0] // H.CELL
    r = a.reshape(H.CELL, k, H.CELL, k, 4)
    al = r[..., 3].mean(axis=(1, 3))
    rgb = (r[..., :3] * r[..., 3:4]).sum(axis=(1, 3)) / np.maximum(r[..., 3].sum(axis=(1, 3)), 1e-6)[..., None]
    cell = np.zeros((H.CELL, H.CELL, 4), np.uint8)
    body = al > 127
    cell[body, :3] = (np.round(rgb[body] / 8) * 8).clip(0, 255)
    cell[body, 3] = 255
    sp = clay_path.replace("_clay.png", "_mask_smear.png")
    if os.path.exists(sp):
        s = load(sp)[..., 3].astype(np.float32).reshape(H.CELL, k, H.CELL, k).mean(axis=(1, 3)) > 90
        s &= ~body
        cell[s, :3] = SMEAR
        cell[s, 3] = 255
    return cell


def jobs(root):
    """(standard name, clay path, sequence key, order)"""
    out = []
    for d in DIRS:
        p = os.path.join(root, "turn", d, "f00_clay.png")
        if os.path.exists(p):
            out.append((f"turn_{d}", p, "turn", DIRS.index(d)))
    for anim, (a, d, keys) in TEST.items():
        for i, k in enumerate(keys):
            p = os.path.join(root, anim, d, f"f{i:02d}_clay.png")
            if os.path.exists(p):
                out.append((f"{a}_{d}_{k}", p, f"{a}_{d}", i))
    for a in SEQS:
        for d in DIRS:
            for p in sorted(glob.glob(os.path.join(root, a, d, "f*_clay.png"))):
                i = int(os.path.basename(p)[1:3])
                out.append((f"{a}_{d}_f{i:02d}", p, f"{a}:{d}", i))
    return out


def cmd_cells(root):
    od = os.path.join(root, "cells")
    os.makedirs(od, exist_ok=True)
    n = 0
    for name, p, _, _ in jobs(root):
        Image.fromarray(to_cell(p), "RGBA").save(os.path.join(od, name + ".png"))
        n += 1
    print("cells:", n, "->", od)


def crop_box(paths, pad=0.03):
    m = None
    for p in paths:
        a = load(p)[..., 3] > 0
        sp = p.replace("_clay.png", "_mask_smear.png")
        if os.path.exists(sp):
            a |= load(sp)[..., 3] > 0
        m = a if m is None else (m | a)
    ys, xs = np.nonzero(m)
    W = m.shape[0]
    pd = int(W * pad)
    return max(xs.min() - pd, 0), max(ys.min() - pd, 0), min(xs.max() + pd, W), min(ys.max() + pd, W)


def stamp(img, text):
    im = Image.fromarray(img)
    ImageDraw.Draw(im).text((4, 3), text, fill=(235, 235, 235))
    return np.array(im)


def tile_frames(rows, cols_n):
    """rows: list of HxWx3 (same size) -> grid"""
    h, w = rows[0].shape[:2]
    nr = (len(rows) + cols_n - 1) // cols_n
    g = np.zeros((nr * h + (nr - 1) * 2, cols_n * w + (cols_n - 1) * 2, 3), np.uint8)
    g[:] = (30, 26, 36)
    for i, f in enumerate(rows):
        r, c = divmod(i, cols_n)
        g[r * (h + 2):r * (h + 2) + h, c * (w + 2):c * (w + 2) + w] = f
    return g


def scaled(img, box, size):
    x0, y0, x1, y1 = box
    im = Image.fromarray(img[y0:y1, x0:x1])
    s = size / max(x1 - x0, y1 - y0)
    return np.array(im.resize((max(1, int((x1 - x0) * s)), max(1, int((y1 - y0) * s))), Image.LANCZOS))


def pad_to(img, w, h, bg=BG):
    out = np.zeros((h, w, 3), np.uint8)
    out[:] = bg
    oy, ox = (h - img.shape[0]) // 2, (w - img.shape[1]) // 2
    out[oy:oy + img.shape[0], ox:ox + img.shape[1]] = img
    return out


def cmd_gifs(root, tag, gif_dir):
    os.makedirs(gif_dir, exist_ok=True)
    J = jobs(root)
    written = []
    # 8-direction grids, hi-res clay, real timing (+ a 4x slow version with frame/ms stamps)
    for a in SEQS:
        per = {d: sorted([(i, p) for n, p, k, i in J if k == f"{a}:{d}"]) for d in DIRS}
        per = {d: v for d, v in per.items() if v}
        if not per:
            continue
        nfr = min(len(v) for v in per.values())
        allp = [p for v in per.values() for _, p in v]
        box = crop_box(allp)
        ms, _ = H.timing_for(a, "SE", nfr)
        frames, slow = [], []
        for i in range(nfr):
            tiles = [stamp(pad_to(scaled(composite(per[d][i][1]), box, 200), 200, 200), d) for d in DIRS if d in per]
            g = tile_frames(tiles, 4)
            frames.append(g)
            slow.append(stamp(g.copy(), f"   {a} f{i}  {ms[i]} ms"))
        path = os.path.join(gif_dir, f"guide_{tag}_{a}_dirs8.gif")
        save_gif(frames, ms, path)
        save_gif(slow, [m * 4 for m in ms], path.replace(".gif", "_slow4.gif"))
        written += [path, path.replace(".gif", "_slow4.gif")]
        # single direction, bigger: SE and E (look + timing review directions)
        for d in ("SE", "E"):
            if d not in per:
                continue
            fr = [pad_to(scaled(composite(per[d][i][1]), box, 360), 360, 360) for i in range(nfr)]
            p2 = os.path.join(gif_dir, f"guide_{tag}_{a}_{d}.gif")
            save_gif(fr, ms, p2)
            written.append(p2)
    # standard test set key GIFs
    for anim, (a, d, keys) in TEST.items():
        ps = [p for n, p, k, i in sorted(J, key=lambda j: j[3]) if k == f"{a}_{d}"]
        if not ps:
            continue
        box = crop_box(ps)
        ms, _ = H.timing_for(a, d, len(ps), keys)
        fr = [stamp(pad_to(scaled(composite(p), box, 360), 360, 360), f"{a}_{d}_{keys[i]}") for i, p in enumerate(ps)]
        p2 = os.path.join(gif_dir, f"guide_{tag}_{a}_{d}_keys.gif")
        save_gif(fr, ms, p2)
        written.append(p2)
    tp = [p for n, p, k, i in sorted(J, key=lambda j: j[3]) if k == "turn"]
    if tp:
        box = crop_box(tp)
        fr = [stamp(pad_to(scaled(composite(p), box, 300), 300, 300), DIRS[i]) for i, p in enumerate(tp)]
        p2 = os.path.join(gif_dir, f"guide_{tag}_turntable.gif")
        save_gif(fr, [250] * len(fr), p2)
        written.append(p2)
    for w in written:
        print("gif:", w)
    return written


def cmd_sheet(root, out):
    """STANDARD TEST SET: rows turn x8 / walk_SE k0-3 / slash_SE k0-3 / jump_E; each tile = hi-res clay
    (+ pink smear) over the 1x and 2x cell silhouettes"""
    J = jobs(root)
    rows = [("turn", [(n, p) for n, p, k, i in sorted(J, key=lambda j: j[3]) if k == "turn"])]
    for anim, (a, d, keys) in TEST.items():
        rows.append((f"{a}_{d}", [(n, p) for n, p, k, i in sorted(J, key=lambda j: j[3]) if k == f"{a}_{d}"]))
    rows = [r for r in rows if r[1]]
    T = 250
    CX = 64
    allp = [p for _, r in rows for _, p in r]
    box = crop_box(allp)
    W = 120 + 8 * (T + 6)
    Hh = len(rows) * (T + 200 + 14) + 30
    S = Image.new("RGB", (W, Hh), (34, 30, 40))
    dr = ImageDraw.Draw(S)
    dr.text((8, 8), f"STANDARD TEST SET guide ({os.path.relpath(root, H.ROOT)}): clay + smear-helper sweep (pink); "
                    "below: 128-cell clay at 2x and 1x (crop 80x96 around the pivot). GUIDE ONLY, never art.", fill=(230, 230, 230))
    y = 30
    for label, items in rows:
        dr.text((8, y + T // 2), label, fill=(230, 230, 230))
        for j, (n, p) in enumerate(items):
            x = 120 + j * (T + 6)
            S.paste(Image.fromarray(pad_to(scaled(composite(p), box, T), T, T)), (x, y))
            c = Image.fromarray(to_cell(p), "RGBA")
            bgc = Image.new("RGBA", c.size, BG + (255,))
            bgc.alpha_composite(c)
            cc = bgc.convert("RGB").crop((CX - 40, 30, CX + 40, 126))          # 80 x 96 around the pivot
            S.paste(cc.resize((160, 192), Image.NEAREST), (x, y + T + 4))
            S.paste(cc, (x + 164, y + T + 4))
            dr.text((x + 2, y + 2), n, fill=(240, 240, 240))
        y += T + 200 + 14
    S.save(out)
    print("sheet:", out)


def cmd_strips(root, anim, out, dirs=DIRS):
    J = jobs(root)
    per = {d: sorted([(i, p) for n, p, k, i in J if k == f"{anim}:{d}"]) for d in dirs}
    per = {d: v for d, v in per.items() if v}
    box = crop_box([p for v in per.values() for _, p in v])
    tiles = []
    n = max(len(v) for v in per.values())
    for d in dirs:
        for i, p in per.get(d, []):
            tiles.append(stamp(pad_to(scaled(composite(p), box, 220), 220, 220), f"{anim} {d} f{i}"))
    Image.fromarray(tile_frames(tiles, n)).save(out)
    print("strip:", out)


def main():
    a = sys.argv[1:]
    cmd, root = a[0], rel(a[1])
    tag = opt(a, "--tag", os.path.basename(root.rstrip("/")))
    gif_dir = rel(opt(a, "--gif-dir", "hybrid/gifs"))
    if cmd in ("cells", "all"):
        cmd_cells(root)
    if cmd in ("gifs", "all"):
        cmd_gifs(root, tag, gif_dir)
    if cmd in ("sheet", "all"):
        cmd_sheet(root, rel(opt(a, "--out", f"hybrid/guide/test_set_{tag}.png")))
    if cmd == "strips":
        cmd_strips(root, opt(a, "--anim"), rel(opt(a, "--out")), (opt(a, "--dirs") or ",".join(DIRS)).split(","))


if __name__ == "__main__":
    main()
