"""Preview GIFs for hybrid sprite sets (nearest-neighbour, exact palette colours, pivot fixed).

  .venv/bin/python tools/hybrid/gifs.py all SPRITES_OR_DIRS... --out-dir D [--no-shadow] [--jump-z] [--slow 4]
  .venv/bin/python tools/hybrid/gifs.py turntable SPRITES... --out-dir D [--ms 250]
  .venv/bin/python tools/hybrid/gifs.py anim SPRITES... --out-dir D [--only slash_SE] [--slow 4] [--jump-z]
  .venv/bin/python tools/hybrid/gifs.py grid SPRITES... --out-dir D [--anim turn]
  .venv/bin/python tools/hybrid/gifs.py compare SET_A SET_B [SET_C ...] --labels A,B,C --out-dir D [--zoom 3]

Outputs (D/):
  turntable_{1x,4x}_{grey,grass}.gif     turn_<DIR> in rotation order S SE E NE N NW W SW
  dirs8_4x_{grey,grass}.gif / .png       2x4 grid of the 8 directions (animated when an anim has all 8)
  <anim>_<DIR>_{1x,4x}_{grey,grass}.gif  per-direction animation, real timing (holds included)
  <anim>_<DIR>_slow_4x_grey.gif          slow-motion (x --slow, default 4), frame label + ms stamped
  compare_<seq>_<zoom>x.gif              labelled side-by-side of the same names in several sets
Timing: hylib.timing_for -> hybrid/ANIM_DIRECTION.md ({"timing": {...}} json block or
'timing <anim>[_<DIR>]: a,b,c' lines), then docs/anim_spec.json (if the frame count matches),
then the key-pose TEST_TIMING (walk 140/110/140/110, slash 220/50/160/240 = anticipation hold,
smear, hit-stop, follow-through hold; jump 160/220/200).  --ms overrides.
Ground shadow: #1a1220 @ 35 %, 2:1 ellipse 20x10 under the pivot (64, 104); with --jump-z the
jump keys are lifted by anim_spec engine_z_offset_px (crouch 0, apex 16, land 0) and the shadow
scales by shadow_scale, as the engine will do.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hylib as H  # noqa: E402

sys.path.insert(0, os.path.join(H.ROOT, "tools", "pixel"))
from gif import grass_tile, label, save_gif  # noqa: E402

GREY = (128, 128, 128)
SEP = (30, 24, 36)
TURN_ORDER = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
JUMP_KEY_FRAME = {"crouch": 0, "anticipation": 0, "rise": 1, "takeoff": 1, "apex": 2, "fall": 3, "land": 4, "recover": 5}


def load_set(inputs):
    paths = H.collect(inputs)
    return {os.path.basename(p): H.load_rgba(p) for p in paths}, paths


def union_crop(imgs, pad=4):
    m = np.zeros((H.CELL, H.CELL), bool)
    for a in imgs:
        m |= a[..., 3] > 0
    if not m.any():
        return 0, H.CELL, 0, H.CELL
    ys, xs = np.nonzero(m)
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, H.CELL)
    y0, y1 = max(ys.min() - pad, 0), min(max(ys.max(), H.PIVOT[1] + 6) + pad + 1, H.CELL)
    return y0, y1, x0, x1


def shadow_mask(h, w, cx, cy, scale=1.0, rx=10, ry=5):
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx + 0.5 - cx) / (rx * scale)) ** 2 + ((yy + 0.5 - cy) / (ry * scale)) ** 2 <= 1.0


class Stage:
    """renders cells onto a background with a fixed crop (pivot never moves)."""

    def __init__(self, imgs, shadow=True, pad=4, extra_top=0):
        self.y0, self.y1, self.x0, self.x1 = union_crop(imgs, pad)
        self.y0 = max(self.y0 - extra_top, 0)
        self.h, self.w = self.y1 - self.y0, self.x1 - self.x0
        self.bgs = {"grey": np.full((self.h, self.w, 3), GREY, np.uint8), "grass": grass_tile(self.w, self.h)}
        self.shadow = shadow

    def frame(self, a, bg="grey", z=0, shadow_scale=1.0):
        out = self.bgs[bg].astype(float).copy()
        if self.shadow:
            sm = shadow_mask(self.h, self.w, H.PIVOT[0] - self.x0, H.PIVOT[1] - self.y0 + 0.5, shadow_scale)
            out[sm] = out[sm] * 0.65 + np.array((0x1a, 0x12, 0x20)) * 0.35
        out = out.astype(np.uint8)
        c = np.zeros_like(a)
        if z:
            c[:H.CELL - z] = a[z:]          # lift by z px (engine z offset)
        else:
            c = a
        c = c[self.y0:self.y1, self.x0:self.x1]
        m = c[..., 3] > 0
        out[m] = c[..., :3][m]
        return out


def jump_z(names):
    spec = json.load(open(os.path.join(H.ROOT, "docs", "anim_spec.json")))["anims"]["jump"]
    zs, ss = [], []
    for n in names:
        r = H.parse_name(n)
        k = JUMP_KEY_FRAME.get(r[2], r[3] if r[2][:1] in "kf" else 0) if r else 0
        k = min(k, len(spec["engine_z_offset_px"]) - 1)
        zs.append(spec["engine_z_offset_px"][k])
        ss.append(spec["shadow_scale"][k])
    return zs, ss


def stamp(f, text, xy=(3, 2)):
    return label(f, text, xy)


def turntable(imgs, od, ms=250, shadow=True):
    names = [f"turn_{d}.png" for d in TURN_ORDER if f"turn_{d}.png" in imgs]
    if len(names) < 2:
        return []
    st = Stage([imgs[n] for n in names], shadow)
    out = []
    for bg in ("grey", "grass"):
        fr = [st.frame(imgs[n], bg) for n in names]
        for z in (1, 4):
            p = os.path.join(od, f"turntable_{z}x_{bg}.gif")
            fz = [H.up(f, z) for f in fr]
            if z == 4:
                fz = [stamp(f, n[5:-4]) for f, n in zip(fz, names)]
            save_gif(fz, [ms] * len(fz), p)
            out.append(p)
    return out


def dirs_grid(imgs, od, anim="turn", shadow=True, z=4):
    """2x4 grid of the 8 directions; animated if <anim>_<DIR>_* sequences exist for every dir."""
    seqs = H.group_sequences(list(imgs))
    out = []
    if anim == "turn":
        frames_by_dir = {d: [f"turn_{d}.png"] for d in TURN_ORDER if f"turn_{d}.png" in imgs}
        ms = [400]
    else:
        frames_by_dir = {d: seqs[(anim, d)] for d in TURN_ORDER if (anim, d) in seqs}
        if not frames_by_dir:
            return out
        n0 = len(next(iter(frames_by_dir.values())))
        ms, _ = H.timing_for(anim, "SE", n0)
    if len(frames_by_dir) < 2:
        return out
    allimgs = [imgs[n] for v in frames_by_dir.values() for n in v]
    st = Stage(allimgs, shadow)
    n = max(len(v) for v in frames_by_dir.values())
    for bg in ("grey", "grass"):
        grid = []
        for k in range(n):
            tiles = []
            for d in TURN_ORDER:
                if d in frames_by_dir:
                    lst = frames_by_dir[d]
                    tiles.append(stamp(H.up(st.frame(imgs[lst[min(k, len(lst) - 1)]], bg), z), d))
                else:
                    tiles.append(H.up(st.bgs[bg], z))
            rows = [np.concatenate(tiles[r * 4:(r + 1) * 4], 1) for r in range(2)]
            grid.append(np.concatenate(rows, 0))
        tag = "dirs8" if anim == "turn" else f"{anim}_dirs8"
        p = os.path.join(od, f"{tag}_{z}x_{bg}.gif")
        save_gif(grid, list(ms)[:len(grid)] if len(ms) >= len(grid) else [ms[0]] * len(grid), p)
        from PIL import Image
        Image.fromarray(grid[0]).save(p[:-4] + ".png")
        out += [p, p[:-4] + ".png"]
    return out


def anim_gifs(imgs, od, only=None, slow=4, ms_override=None, jz=False, shadow=True):
    out = []
    seqs = H.group_sequences(list(imgs))
    for (anim, d), names in sorted(seqs.items()):
        if anim == "turn" or len(names) < 2:
            continue
        tag = f"{anim}_{d}"
        if only and tag not in only and anim not in only:
            continue
        keys = [H.parse_name(n)[2] for n in names]
        ms, src = (ms_override, "--ms") if ms_override else H.timing_for(anim, d, len(names), keys)
        if len(ms) != len(names):
            ms = [ms[0]] * len(names)
        zs, ss = jump_z(names) if (jz and anim == "jump") else ([0] * len(names), [1.0] * len(names))
        st = Stage([imgs[n] for n in names], shadow, extra_top=max(zs))
        for bg in ("grey", "grass"):
            fr = [st.frame(imgs[n], bg, z, s) for n, z, s in zip(names, zs, ss)]
            for zz in (1, 4):
                p = os.path.join(od, f"{tag}_{zz}x_{bg}.gif")
                save_gif([H.up(f, zz) for f in fr], ms, p)
                out.append(p)
        if slow:
            fr = [stamp(H.up(st.frame(imgs[n], "grey", z, s), 4), f"{k or n} {m}ms")
                  for n, k, m, z, s in zip(names, keys, ms, zs, ss)]
            p = os.path.join(od, f"{tag}_slow_4x_grey.gif")
            save_gif(fr, [int(m * slow) for m in ms], p)
            out.append(p)
        print(f"  {tag}: {len(names)} frames, ms {ms} ({src})")
    return out


def compare(sets, labels, od, zoom=3, slow=1, shadow=True):
    """same sprite names across several set directories, side by side, labelled."""
    loaded = [load_set([s])[0] for s in sets]
    common = sorted(set.intersection(*[set(l) for l in loaded]))
    if not common:
        print("compare: no common sprite names")
        return []
    allimgs = [l[n] for l in loaded for n in common]
    st = Stage(allimgs, shadow)
    seqs = H.group_sequences(common)
    out = []
    sep = np.full((st.h * zoom, 3, 3), SEP, np.uint8)
    turn = [f"turn_{d}.png" for d in TURN_ORDER if f"turn_{d}.png" in common]
    groups = dict(((a, d), v) for (a, d), v in seqs.items() if a != "turn")
    if turn:
        groups[("turntable", "")] = turn
    for (anim, d), names in sorted(groups.items()):
        if anim == "turntable":
            ms = [300] * len(names)
        else:
            ms, _ = H.timing_for(anim, d, len(names), [H.parse_name(n)[2] for n in names])
        frames = []
        for n in names:
            tiles = []
            for l, lab in zip(loaded, labels):
                tiles.append(stamp(H.up(st.frame(l[n], "grey"), zoom), f"{lab} {n[:-4]}"))
                tiles.append(sep)
            frames.append(np.concatenate(tiles[:-1], 1))
        tag = f"{anim}_{d}" if d else anim
        p = os.path.join(od, f"compare_{tag}_{zoom}x.gif")
        save_gif(frames, [int(m * slow) for m in ms], p)
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["all", "turntable", "anim", "grid", "compare"])
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--ms", help="comma list of per-frame ms (overrides timing lookup)")
    ap.add_argument("--only", help="comma list of <anim>_<DIR> or <anim> to render")
    ap.add_argument("--slow", type=float, default=4.0, help="slow-motion factor (0 = no slow variant)")
    ap.add_argument("--jump-z", action="store_true")
    ap.add_argument("--no-shadow", action="store_true")
    ap.add_argument("--anim", default="turn", help="grid: which anim to lay out in 2x4")
    ap.add_argument("--labels")
    ap.add_argument("--zoom", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    sh = not a.no_shadow
    ms = [int(v) for v in a.ms.split(",")] if a.ms else None
    files = []
    if a.cmd == "compare":
        labels = a.labels.split(",") if a.labels else [os.path.basename(os.path.normpath(s)) for s in a.inputs]
        files = compare(a.inputs, labels, a.out_dir, a.zoom, 1, sh)
    else:
        imgs, _ = load_set(a.inputs)
        if not imgs:
            sys.exit("no sprites")
        if a.cmd in ("all", "turntable"):
            files += turntable(imgs, a.out_dir, ms[0] if ms else 250, sh)
        if a.cmd in ("all", "grid"):
            files += dirs_grid(imgs, a.out_dir, a.anim, sh)
            if a.cmd == "all":
                for an in sorted({k[0] for k in H.group_sequences(list(imgs)) if k[0] != "turn"}):
                    files += dirs_grid(imgs, a.out_dir, an, sh)
        if a.cmd in ("all", "anim"):
            files += anim_gifs(imgs, a.out_dir, a.only.split(",") if a.only else None, a.slow, ms, a.jump_z, sh)
    print(f"gifs {a.cmd}: {len(files)} files -> {os.path.relpath(a.out_dir, H.ROOT) if os.path.isabs(a.out_dir) else a.out_dir}")


if __name__ == "__main__":
    main()
