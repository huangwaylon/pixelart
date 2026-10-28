"""Preview GIFs for an animation (nearest-neighbour scaling, exact colours, no dithering).

  .venv/bin/python tools/pixel/gif.py --anim idle [--src clean|base] [--no-shadow]

Writes pixel/gifs/<anim>_<src>/:
  <DIR>_1x_grey.gif  <DIR>_4x_grey.gif  <DIR>_1x_grass.gif  <DIR>_4x_grass.gif   per direction
  all8_4x_grey.gif  all8_4x_grass.gif         8 directions, 2x4 grid at 4x, labelled
  before_after_<DIR>_4x.gif  before_after_all8_2x.gif   base | clean side by side (always written)
Frame durations from docs/anim_spec.json (if the spec frame count differs from the rendered count,
every frame gets the spec's mean duration; a warning is printed).  The cell is cropped to the union
bounding box of all frames/directions (same crop for every GIF so the pivot never moves).  A soft
ground shadow (#1a1220 @ 35 %, engine layer per palette.json roles) is drawn under the pivot.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxlib import DIRS, PIVOT, PIXEL, anim_ms, dirs_of, frame_path, frames_of, load_rgba, rel  # noqa: E402

GREY = (128, 128, 128)
LABEL = (240, 240, 240)


def grass_tile(w, h, seed=7):
    """deterministic grass ground: 3 greens, small tufts."""
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 3), np.uint8)
    a[:] = (74, 122, 58)
    n = rng.random((h, w))
    a[n > 0.82] = (92, 142, 66)
    a[n < 0.10] = (60, 102, 50)
    for _ in range(w * h // 60):
        x, y = int(rng.integers(0, w)), int(rng.integers(1, h))
        a[y, x] = (110, 160, 74)
        a[y - 1, x] = (110, 160, 74)
    return a


def shadow_layer(w, h, cx, cy, rx=8, ry=3):
    m = np.zeros((h, w), bool)
    yy, xx = np.mgrid[0:h, 0:w]
    m |= ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1.0
    return m


def frame_on(bg, sprite, shadow_mask):
    """bg HxWx3 uint8, sprite HxWx4 (binary alpha) -> HxWx3"""
    out = bg.copy().astype(float)
    if shadow_mask is not None:
        out[shadow_mask] = out[shadow_mask] * 0.65 + np.array((0x1a, 0x12, 0x20)) * 0.35
    out = out.astype(np.uint8)
    m = sprite[..., 3] > 0
    out[m] = sprite[..., :3][m]
    return out


def up(a, s):
    return np.repeat(np.repeat(a, s, axis=0), s, axis=1)


def save_gif(frames, ms, path):
    """frames: list of HxWx3 uint8.  Exact palette from the union of colours (<= 256)."""
    cols = np.unique(np.concatenate([f.reshape(-1, 3) for f in frames]), axis=0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if len(cols) <= 256:
        pal = cols.astype(np.uint8)
        key = (pal[:, 0].astype(np.int64) << 16) | (pal[:, 1].astype(np.int64) << 8) | pal[:, 2]
        order = np.argsort(key)
        ims = []
        for f in frames:
            k = (f[..., 0].astype(np.int64) << 16) | (f[..., 1].astype(np.int64) << 8) | f[..., 2]
            ix = order[np.searchsorted(key[order], k)]
            im = Image.fromarray(ix.astype(np.uint8), "P")
            flat = pal.flatten().tolist()
            im.putpalette(flat + [0] * (768 - len(flat)))
            ims.append(im)
    else:
        ims = [Image.fromarray(f, "RGB").quantize(256, dither=Image.Dither.NONE) for f in frames]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=1, optimize=False)


def label(a, text, xy=(3, 2)):
    im = Image.fromarray(a, "RGB")
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    try:
        f = ImageFont.load_default(11)
    except TypeError:
        f = ImageFont.load_default()
    x, y = xy
    d.text((x + 1, y + 1), text, fill=(20, 16, 24), font=f)
    d.text((x, y), text, fill=LABEL, font=f)
    return np.array(im)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anim", default="idle")
    ap.add_argument("--src", default="clean", choices=["clean", "base"])
    ap.add_argument("--no-shadow", action="store_true")
    a = ap.parse_args()
    src = a.src
    if not dirs_of(a.anim, src):
        print(f"no {src} frames; using base")
        src = "base"
    dirs = [d for d in DIRS if d in dirs_of(a.anim, src)]
    n = len(frames_of(a.anim, dirs[0], src))
    ms, warn = anim_ms(a.anim, n)
    if warn:
        print("WARNING:", warn)
    fr = {s: {d: [load_rgba(frame_path(s, a.anim, d, k)) for k in frames_of(a.anim, d, s)] for d in dirs}
          for s in {src, "base"} | ({"clean"} if dirs_of(a.anim, "clean") else set())}
    # union crop (+ pad) over everything, keeps the pivot fixed
    allm = np.zeros((128, 128), bool)
    for s in fr:
        for d in dirs:
            for f in fr[s][d]:
                allm |= f[..., 3] > 0
    ys, xs = np.nonzero(allm)
    x0, x1 = max(xs.min() - 4, 0), min(xs.max() + 5, 128)
    y0, y1 = max(ys.min() - 4, 0), min(max(ys.max(), PIVOT[1] + 3) + 5, 128)
    w, h = x1 - x0, y1 - y0
    bgs = {"grey": np.full((h, w, 3), GREY, np.uint8), "grass": grass_tile(w, h)}
    shm = None if a.no_shadow else shadow_layer(w, h, PIVOT[0] - x0, PIVOT[1] - y0 + 0.5)
    od = os.path.join(PIXEL, "gifs", f"{a.anim}_{src}")
    crop = lambda f: f[y0:y1, x0:x1]
    nfiles = 0
    for d in dirs:
        for bgn, bg in bgs.items():
            frames1 = [frame_on(bg, crop(f), shm) for f in fr[src][d]]
            save_gif(frames1, ms, os.path.join(od, f"{d}_1x_{bgn}.gif"))
            save_gif([up(f, 4) for f in frames1], ms, os.path.join(od, f"{d}_4x_{bgn}.gif"))
            nfiles += 2
    # 8-direction 2x4 grid at 4x, labelled
    order = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
    order = [d for d in order if d in dirs]
    for bgn, bg in bgs.items():
        grid = []
        for k in range(n):
            tiles = [label(up(frame_on(bg, crop(fr[src][d][k]), shm), 4), d) for d in order]
            while len(tiles) < 8:
                tiles.append(up(bg, 4))
            rows = [np.concatenate(tiles[r * 4:(r + 1) * 4], axis=1) for r in range(2)]
            g = np.concatenate(rows, axis=0)
            grid.append(label(g, f"{a.anim} [{src}] f{k:02d}", (4, g.shape[0] - 14)))
        save_gif(grid, ms, os.path.join(od, f"all8_4x_{bgn}.gif"))
        nfiles += 1
    # before / after (base | clean)
    after = "clean" if "clean" in fr else "base"
    sep = np.full((h * 4, 4, 3), (30, 24, 36), np.uint8)
    for d in dirs:
        frames = []
        for k in range(n):
            b = label(up(frame_on(bgs["grey"], crop(fr["base"][d][k]), shm), 4), f"BASE {d}")
            c = label(up(frame_on(bgs["grey"], crop(fr[after][d][k]), shm), 4), f"{after.upper()} {d}")
            frames.append(np.concatenate([b, sep, c], axis=1))
        save_gif(frames, ms, os.path.join(od, f"before_after_{d}_4x.gif"))
        nfiles += 1
    frames = []
    for k in range(n):
        rows = []
        for which in ("base", after):
            tiles = [label(up(frame_on(bgs["grey"], crop(fr[which][d][k]), shm), 2), f"{which[:1].upper()} {d}") for d in order]
            rows.append(np.concatenate(tiles, axis=1))
        frames.append(np.concatenate([rows[0], np.full((4, rows[0].shape[1], 3), (30, 24, 36), np.uint8), rows[1]], axis=0))
    save_gif(frames, ms, os.path.join(od, "before_after_all8_2x.gif"))
    nfiles += 1
    print(f"gif {a.anim} [{src}]: {nfiles} GIFs, {n} frames, {ms[0]} ms/frame, crop {w}x{h} -> {rel(od)}")


if __name__ == "__main__":
    main()
