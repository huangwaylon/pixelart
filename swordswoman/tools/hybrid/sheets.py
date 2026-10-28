"""Contact sheets for holistic review of a hybrid sprite set.

  .venv/bin/python tools/hybrid/sheets.py contact SPRITES_OR_DIRS... --out sheet.png [--guide-dir G] [--cols 4]
  .venv/bin/python tools/hybrid/sheets.py dirs    SPRITES_OR_DIRS... --out dirs8.png [--zoom 4] [--bg grey|grass]
  .venv/bin/python tools/hybrid/sheets.py set     SPRITES_OR_DIRS... --out set.png  [--zoom 4] [--bg grey|grass]

contact : one card per sprite = 1x | 4x | hi-res source (<stem>_hires.png / _src.png) | guide
          (guide colour sprite, else silhouette, with the sprite's outline in cyan over it), all on
          one fixed crop so sizes compare; the card title carries h / body h / IoU.
dirs    : the 8 turn_<DIR> keys as a 2x4 grid at 4x (+ 1x row underneath), labelled.
set     : the whole set at once: row 1 = 8 directions, then one row per sequence (anim_DIR) with
          per-frame key + ms (timing from hylib.timing_for), at --zoom, plus a 1x strip.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hylib as H  # noqa: E402
from gifs import TURN_ORDER, Stage, union_crop  # noqa: E402

BG = (30, 24, 36)
TXT = (240, 236, 220)


def text(im, xy, s, fill=TXT):
    ImageDraw.Draw(im).text(xy, s, fill=fill)


def on_grey(a, c=(150, 150, 150)):
    out = np.zeros(a.shape[:2] + (3,), np.uint8)
    out[:] = c
    m = a[..., 3] > 0
    out[m] = a[..., :3][m]
    return out


def contact(paths, out, guide_dir=None, cols=4, z=4):
    imgs = {p: H.load_rgba(p) for p in paths}
    y0, y1, x0, x1 = union_crop(list(imgs.values()), 3)
    ch, cw = y1 - y0, x1 - x0
    tiles_w = cw + cw * z * 3 + 4 * 6
    card_h = ch * z + 18
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tiles_w + 8) + 8, rows * (card_h + 8) + 8), BG)
    for i, p in enumerate(paths):
        a = imgs[p]
        cx, cy = 8 + (i % cols) * (tiles_w + 8), 8 + (i // cols) * (card_h + 8)
        crop = a[y0:y1, x0:x1]
        F = H.features(a)
        gp = H.find_guide(p, guide_dir)
        g = H.load_guide(gp) if gp else None
        title = f"{os.path.basename(p)[:-4]}  h{F.get('height', '-')} b{F.get('body_height', '-')}"
        if g is not None:
            u = ((a[..., 3] > 0) | g.mask).sum()
            title += f" IoU {((a[..., 3] > 0) & g.mask).sum() / max(u, 1):.2f}"
        text(sheet, (cx, cy), title)
        x = cx
        t1 = Image.fromarray(on_grey(crop))
        sheet.paste(t1, (x, cy + 16))
        x += cw + 6
        sheet.paste(Image.fromarray(H.up(on_grey(crop), z)), (x, cy + 16))
        x += cw * z + 6
        hp = H.hires_of(p)
        if hp:
            hi = Image.open(hp).convert("RGBA")
            k = hi.width / H.CELL
            hi = hi.crop((int(x0 * k), int(y0 * k), int(x1 * k), int(y1 * k))).resize((cw * z, ch * z), Image.LANCZOS)
            bgi = Image.new("RGBA", hi.size, (150, 150, 150, 255))
            bgi.alpha_composite(hi)
            sheet.paste(bgi.convert("RGB"), (x, cy + 16))
        else:
            text(sheet, (x + 4, cy + 30), "no hi-res", (160, 150, 150))
        x += cw * z + 6
        if g is not None:
            gimg = g.color if g.color is not None else np.dstack([np.full(g.mask.shape + (3,), 90, np.uint8), g.mask * 255]).astype(np.uint8)
            gv = H.up(on_grey(gimg[y0:y1, x0:x1], (120, 120, 120)), z)
            sm = a[..., 3] > 0
            e = sm & ~(H.shift(sm, -1, 0, False) & H.shift(sm, 1, 0, False) & H.shift(sm, 0, -1, False) & H.shift(sm, 0, 1, False))
            gv[H.up(e[y0:y1, x0:x1], z)] = (0, 230, 255)
            sheet.paste(Image.fromarray(gv), (x, cy + 16))
        else:
            text(sheet, (x + 4, cy + 30), "no guide", (160, 150, 150))
    sheet.save(out)
    return out


def dirs(paths, out, z=4, bg="grey"):
    imgs = {os.path.basename(p): H.load_rgba(p) for p in paths}
    names = [f"turn_{d}.png" for d in TURN_ORDER]
    have = [n for n in names if n in imgs]
    if not have:
        raise SystemExit("no turn_<DIR>.png sprites")
    st = Stage([imgs[n] for n in have], True)
    tiles = []
    for n in names:
        f = st.frame(imgs[n], bg) if n in imgs else st.bgs[bg]
        t = Image.fromarray(H.up(f, z))
        text(t, (3, 2), n[5:-4] if n in imgs else n[5:-4] + " (missing)")
        tiles.append(t)
    W, Ht = tiles[0].width, tiles[0].height
    ones = [Image.fromarray(st.frame(imgs[n], bg) if n in imgs else st.bgs[bg]) for n in names]
    sheet = Image.new("RGB", (4 * W + 5 * 4, 2 * Ht + 3 * 4 + st.h + 8), BG)
    for i, t in enumerate(tiles):
        sheet.paste(t, (4 + (i % 4) * (W + 4), 4 + (i // 4) * (Ht + 4)))
    for i, t in enumerate(ones):
        sheet.paste(t, (4 + i * (st.w + 2), 2 * Ht + 12))
    sheet.save(out)
    return out


def set_sheet(paths, out, z=4, bg="grey"):
    imgs = {os.path.basename(p): H.load_rgba(p) for p in paths}
    seqs = H.group_sequences(list(imgs))
    rows = []
    turn = [f"turn_{d}.png" for d in TURN_ORDER if f"turn_{d}.png" in imgs]
    if turn:
        rows.append(("turn (8 dirs)", turn, [None] * len(turn)))
    for (anim, d), names in sorted(seqs.items()):
        if anim == "turn":
            continue
        keys = [H.parse_name(n)[2] for n in names]
        ms, src = H.timing_for(anim, d, len(names), keys)
        rows.append((f"{anim}_{d}  ({src})", names, [f"{k} {m}ms" for k, m in zip(keys, ms)]))
    st = Stage(list(imgs.values()), True)
    W, Ht = st.w * z, st.h * z
    ncol = max(len(r[1]) for r in rows)
    sheet = Image.new("RGB", (ncol * (W + 4) + 8 + ncol * (st.w + 2) + 12, len(rows) * (Ht + 22) + 8), BG)
    for r, (title, names, labs) in enumerate(rows):
        y = 4 + r * (Ht + 22)
        text(sheet, (6, y), title)
        for c, n in enumerate(names):
            t = Image.fromarray(H.up(st.frame(imgs[n], bg), z))
            text(t, (3, 2), labs[c] or n[5:-4])
            sheet.paste(t, (6 + c * (W + 4), y + 14))
            sheet.paste(Image.fromarray(st.frame(imgs[n], bg)), (ncol * (W + 4) + 14 + c * (st.w + 2), y + 14))
    sheet.save(out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["contact", "dirs", "set"])
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--guide-dir")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--zoom", type=int, default=4)
    ap.add_argument("--bg", default="grey", choices=["grey", "grass"])
    a = ap.parse_args()
    paths = H.collect(a.inputs)
    if not paths:
        sys.exit("no sprites")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if a.cmd == "contact":
        contact(paths, a.out, a.guide_dir, a.cols, a.zoom)
    elif a.cmd == "dirs":
        dirs(paths, a.out, a.zoom, a.bg)
    else:
        set_sheet(paths, a.out, a.zoom, a.bg)
    print(f"sheets {a.cmd}: {len(paths)} sprites -> {a.out}")


if __name__ == "__main__":
    main()
