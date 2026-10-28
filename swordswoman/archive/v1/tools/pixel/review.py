"""Pixel review sheets: 12x zoom, coordinate grid + rulers every 4 px, palette-name legend.

  .venv/bin/python tools/pixel/review.py --anim idle --dir S [--frames 0,3] [--zoom 12] [--src clean|base]

Per frame -> pixel/review/<anim>/<DIR>/fNN.png with 5 panels on one row:
  CLEAN (base + overrides) | BASE | DIFF (changed px boxed magenta, base faded) |
  SOURCE (512 px toon render, same framing, scaled to the same zoom) | FLAGS (lint overlay)
plus a legend (palette names + pixel counts of the clean frame, override list, flag counts).
Strip -> pixel/review/<anim>/<DIR>/strip.png: every frame (clean row + base row + source row) at 5x.
Coordinates are cell pixels (x = column, y = row in the 128x128 cell), the same numbers px.py takes.
Without clean frames (px.py apply not run yet) CLEAN shows the base.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxlib import PIVOT, PIXEL, Palette, anim_loops, dirs_of, frame_path, frames_of, load_overrides, load_rgba, rel  # noqa: E402
import lint as L  # noqa: E402

INK = (30, 24, 36)
TXT = (240, 232, 214)
SUB = (160, 172, 196)
GRID1 = (0, 0, 0, 34)
GRID4 = (0, 0, 0, 110)
BG_A, BG_B = (202, 204, 208), (188, 190, 196)
FLAG_COL = {
    "off_palette": (255, 0, 0), "semi_alpha": (255, 120, 0), "orphan": (255, 230, 0), "outline_gap": (0, 230, 255),
    "notch": (0, 140, 255), "spur": (170, 90, 255), "double": (255, 80, 200), "jaggy": (255, 150, 150),
    "banding": (120, 255, 120), "inner_break": (0, 255, 190), "flicker": (255, 255, 255),
}


def font(sz=12):
    try:
        return ImageFont.load_default(sz)
    except TypeError:
        return ImageFont.load_default()


F = font(12)
FS = font(10)


def checker(w, h, z):
    a = np.zeros((h, w, 3), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((yy // z) + (xx // z)) % 2 == 0
    a[m] = BG_A
    a[~m] = BG_B
    return Image.fromarray(a, "RGB").convert("RGBA")


def zoom(a, box, z):
    x0, y0, x1, y1 = box
    return Image.fromarray(a[y0:y1, x0:x1].astype(np.uint8), "RGBA").resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)


def grid(img, box, z, major_only=False):
    x0, y0, x1, y1 = box
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x in range(x0, x1 + 1):
        if x % 4 == 0 or not major_only:
            d.line([((x - x0) * z, 0), ((x - x0) * z, img.size[1])], fill=GRID4 if x % 4 == 0 else GRID1)
    for y in range(y0, y1 + 1):
        if y % 4 == 0 or not major_only:
            d.line([(0, (y - y0) * z), (img.size[0], (y - y0) * z)], fill=GRID4 if y % 4 == 0 else GRID1)
    # pivot cross
    px, py = PIVOT
    if x0 <= px < x1 and y0 <= py < y1:
        d.rectangle([(px - x0) * z, (py - y0) * z, (px - x0 + 1) * z - 1, (py - y0 + 1) * z - 1], outline=(255, 60, 60, 200))
    return Image.alpha_composite(img, ov)


def panel(a, box, z, bg=True):
    w, h = (box[2] - box[0]) * z, (box[3] - box[1]) * z
    base = checker(w, h, z) if bg else Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return grid(Image.alpha_composite(base, zoom(a, box, z)), box, z)


def source_panel(src_path, box, z):
    w, h = (box[2] - box[0]) * z, (box[3] - box[1]) * z
    bg = checker(w, h, z)
    if not os.path.exists(src_path):
        d = ImageDraw.Draw(bg)
        d.text((8, 8), "no source render", fill=(60, 0, 0), font=F)
        return bg
    s = Image.open(src_path).convert("RGBA")
    f = s.size[0] / 128.0
    crop = s.crop((int(box[0] * f), int(box[1] * f), int(box[2] * f), int(box[3] * f))).resize((w, h), Image.LANCZOS)
    return grid(Image.alpha_composite(bg, crop), box, z, major_only=True)


def diff_panel(clean, base, box, z):
    fade = base.copy().astype(float)
    fade[..., :3] = fade[..., :3] * 0.35 + 255 * 0.65
    img = panel(fade.astype(np.uint8), box, z)
    d = ImageDraw.Draw(img)
    ch = np.any(clean != base, axis=-1)
    x0, y0 = box[:2]
    n = 0
    for y, x in zip(*np.nonzero(ch)):
        if not (box[0] <= x < box[2] and box[1] <= y < box[3]):
            continue
        n += 1
        X, Y = (x - x0) * z, (y - y0) * z
        if clean[y, x, 3]:
            d.rectangle([X + 2, Y + 2, X + z - 3, Y + z - 3], fill=tuple(int(v) for v in clean[y, x, :3]))
        else:
            d.line([X + 2, Y + 2, X + z - 3, Y + z - 3], fill=(255, 0, 200), width=2)
        d.rectangle([X, Y, X + z - 1, Y + z - 1], outline=(255, 0, 200), width=2)
    return img, n


def flags_panel(clean, flags, box, z):
    dim = clean.copy().astype(float)
    dim[..., :3] = dim[..., :3] * 0.45 + 128 * 0.55
    img = panel(dim.astype(np.uint8), box, z)
    d = ImageDraw.Draw(img)
    x0, y0 = box[:2]
    for f in flags:
        x, y = f["x"], f["y"]
        if not (box[0] <= x < box[2] and box[1] <= y < box[3]):
            continue
        c = FLAG_COL.get(f["type"], (255, 255, 255))
        X, Y = (x - x0) * z, (y - y0) * z
        if f["sev"] == "info":
            d.rectangle([X + 3, Y + 3, X + z - 4, Y + z - 4], outline=c + (150,), width=1)
        else:
            d.rectangle([X + 1, Y + 1, X + z - 2, Y + z - 2], outline=c, width=2)
    return img


def rulers(canvas, ox, oy, box, z):
    d = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = box
    for x in range(x0, x1):
        if x % 4 == 0:
            d.text((ox + (x - x0) * z + 1, oy - 13), str(x), fill=TXT, font=FS)
    for y in range(y0, y1):
        if y % 4 == 0:
            d.text((ox - 24, oy + (y - y0) * z + 1), str(y), fill=TXT, font=FS)


def union_box(anim, d, ks, srcs, pad=2):
    xs0, ys0, xs1, ys1 = 128, 128, 0, 0
    for k in ks:
        for s in srcs:
            p = frame_path(s, anim, d, k)
            if not os.path.exists(p):
                continue
            a = load_rgba(p)
            ys, xs = np.nonzero(a[..., 3] > 0)
            if len(xs):
                xs0, ys0 = min(xs0, xs.min()), min(ys0, ys.min())
                xs1, ys1 = max(xs1, xs.max()), max(ys1, ys.max())
    x0, y0 = max(int(xs0) - pad, 0), max(int(ys0) - pad, 0)
    x1, y1 = min(int(xs1) + pad + 1, 128), min(max(int(ys1), PIVOT[1]) + pad + 1, 128)
    # snap to multiples of 4 so the major grid lines line up with the rulers
    return (x0 // 4 * 4, y0 // 4 * 4, min((x1 + 3) // 4 * 4, 128), min((y1 + 3) // 4 * 4, 128))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anim", default="idle")
    ap.add_argument("--dir", help="default: all directions")
    ap.add_argument("--frames", help="comma list (0-based); default all")
    ap.add_argument("--zoom", type=int, default=12)
    ap.add_argument("--src", default="clean", choices=["clean", "base"], help="what the CLEAN panel shows")
    a = ap.parse_args()
    pal = Palette()
    z = a.zoom
    dirs = [a.dir] if a.dir else dirs_of(a.anim)
    for d in dirs:
        ks = frames_of(a.anim, d)
        sel = [int(v) for v in a.frames.split(",")] if a.frames else ks
        box = union_box(a.anim, d, ks, ["base", "clean"])
        cleans, bases, idxs, lints = {}, {}, [], {}
        for k in ks:
            b = load_rgba(frame_path("base", a.anim, d, k))
            cp = frame_path("clean", a.anim, d, k)
            c = load_rgba(cp) if (a.src == "clean" and os.path.exists(cp)) else b
            bases[k], cleans[k] = b, c
            ids, gn = L.load_groups(a.anim, d, k)
            flags, info, idx = L.lint_frame(c, pal, ids, gn)
            lints[k] = (flags, info)
            idxs.append(idx)
        for kk, lst in L.flicker(idxs, anim_loops(a.anim)).items():
            for x, y, A, B in lst:
                lints[ks[kk]][0].append({"type": "flicker", "x": x, "y": y, "sev": "warn"})
        odir = os.path.join(PIXEL, "review", a.anim, d)
        os.makedirs(odir, exist_ok=True)
        pw, ph = (box[2] - box[0]) * z, (box[3] - box[1]) * z
        gap, top, left, leg_w = 30, 64, 30, 300
        for k in sel:
            c, b = cleans[k], bases[k]
            flags, info = lints[k]
            dp, nchg = diff_panel(c, b, box, z)
            panels = [("CLEAN (base+overrides)", panel(c, box, z)), ("BASE (round snapshot)", panel(b, box, z)),
                      (f"DIFF ({nchg} px changed)", dp),
                      ("SOURCE 512px render", source_panel(frame_path("source", a.anim, d, k), box, z)),
                      (f"FLAGS ({sum(f['sev'] != 'info' for f in flags)} warn)", flags_panel(c, flags, box, z))]
            W = left + len(panels) * (pw + gap) + leg_w
            H = top + ph + 30
            can = Image.new("RGBA", (W, max(H, 760)), INK + (255,))
            dr = ImageDraw.Draw(can)
            edits = load_overrides(a.anim, d, k)
            dr.text((10, 8), f"{a.anim} {d} f{k:02d}   cell 128x128, pivot {PIVOT}   crop x{box[0]}-{box[2] - 1} y{box[1]}-{box[3] - 1}"
                             f"   zoom {z}x   {info['n_colours']} colours   {len(edits)} override px", fill=TXT, font=F)
            for i, (title, im) in enumerate(panels):
                ox = left + i * (pw + gap)
                dr.text((ox, top - 30), title, fill=SUB, font=F)
                can.alpha_composite(im, (ox, top))
                rulers(can, ox, top, box, z)
            lx = left + len(panels) * (pw + gap)
            y = top
            dr.text((lx, y - 30), "palette (clean frame)", fill=SUB, font=F)
            cnt = {}
            op = c[..., 3] > 0
            for v in map(tuple, c[op][:, :3]):
                cnt[v] = cnt.get(v, 0) + 1
            for rgb, n in sorted(cnt.items(), key=lambda t: pal.index.get(pal.by_rgb.get(t[0], ""), 99)):
                nm = pal.by_rgb.get(rgb, "OFF-PALETTE")
                dr.rectangle([lx, y, lx + 14, y + 14], fill=rgb, outline=(0, 0, 0))
                dr.text((lx + 20, y + 1), f"{nm:<11} {'#%02x%02x%02x' % rgb}  {n}", fill=TXT, font=FS)
                y += 18
            y += 10
            dr.text((lx, y), "lint flags (FLAGS panel)", fill=SUB, font=F)
            y += 18
            fc = {}
            for f in flags:
                key = f["type"] + (" (info)" if f["sev"] == "info" else "")
                fc[key] = fc.get(key, 0) + 1
            for t, col in FLAG_COL.items():
                n = fc.get(t, 0)
                ni = fc.get(t + " (info)", 0)
                dr.rectangle([lx, y + 2, lx + 10, y + 12], outline=col, width=2)
                dr.text((lx + 18, y + 1), f"{t:<12} {n}" + (f"  (+{ni} info)" if ni else ""), fill=TXT if n else SUB, font=FS)
                y += 15
            if info.get("pivot"):
                p = info["pivot"]
                y += 6
                dr.text((lx, y), f"feet baseline y={p['baseline_y']}  feet x {p['feet_x0']}-{p['feet_x1']}", fill=TXT, font=FS)
                y += 15
            if edits:
                y += 6
                dr.text((lx, y), "overrides", fill=SUB, font=F)
                y += 16
                for e in edits[:24]:
                    dr.text((lx, y), f"({e['x']},{e['y']}) {e['color']}: {e['reason'][:30]}", fill=TXT, font=FS)
                    y += 13
                if len(edits) > 24:
                    dr.text((lx, y), f"... {len(edits) - 24} more (px.py show)", fill=SUB, font=FS)
            can.convert("RGB").save(os.path.join(odir, f"f{k:02d}.png"))
        # strip: every frame, rows clean / base / source at 5x
        zs = 5
        sw, sh = (box[2] - box[0]) * zs, (box[3] - box[1]) * zs
        st = Image.new("RGBA", (40 + len(ks) * (sw + 8), 30 + 3 * (sh + 22)), INK + (255,))
        ds = ImageDraw.Draw(st)
        for row, (lab, getter) in enumerate((("clean", lambda k: panel(cleans[k], box, zs)),
                                             ("base", lambda k: panel(bases[k], box, zs)),
                                             ("source", lambda k: source_panel(frame_path("source", a.anim, d, k), box, zs)))):
            yy = 30 + row * (sh + 22)
            ds.text((4, yy + sh // 2), lab, fill=SUB, font=FS)
            for i, k in enumerate(ks):
                xx = 40 + i * (sw + 8)
                st.alpha_composite(getter(k), (xx, yy))
                if row == 0:
                    nfl = sum(f["sev"] != "info" for f in lints[k][0])
                    ds.text((xx, 10), f"f{k:02d}  {len(load_overrides(a.anim, d, k))} ovr  {nfl} flags", fill=TXT, font=FS)
        st.convert("RGB").save(os.path.join(odir, "strip.png"))
        print(f"review {a.anim} {d}: {len(sel)} sheets + strip -> {rel(odir)}")


if __name__ == "__main__":
    main()
