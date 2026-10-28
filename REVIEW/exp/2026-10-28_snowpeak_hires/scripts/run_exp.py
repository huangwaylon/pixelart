"""Render one variant/clip at k x sprite PPU and resolve it to 48x64 with every method, then run the shipped FIX chain.

  .venv/bin/python -B REVIEW/exp/2026-10-28_snowpeak_hires/scripts/run_exp.py S4_hd2 idle 8 [--dirs S,SE,E] [--frames 0,1]
      [--big S:0,SE:0,E:0]

Writes frames/<variant>__<clip>__k<k>.pkl  {method: {dir: [idx]}}, raw (unfixed) frames, deliberate/body_bbox for QA,
and hi-res intermediates for the --big (dir:frame) list to big/<variant>__<clip>__k<k>__<dir>_f<n>_<buffer>.png.
Methods:  N  native shipped (render_pixels ss=3)       V   vote: majority material + mean lambert -> band (ss=k)
          VM vote: majority material + majority band     KC  k-centroid of flat-band RGB -> lock to material ramp
          KS k-centroid of smooth RGB -> lock           AA  area average of smooth RGB -> lock
          PF Retro Diffusion pixel-art-fixer (forced k grid) of smooth RGB -> lock
          VME / KCE: VM / KC + hi-res normal/depth edge pass (crease + depth-break interior lines, skin excluded)
"""
import argparse
import os
import pickle
import subprocess
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrlib as H  # noqa: E402

METHODS = ["N", "V", "VM", "KC", "KS", "AA", "PF", "VME", "KCE"]
FIXER = os.path.join(H.ROOT, ".models/pixel-art-fixer/venv/bin/python")


def save_png(a, path):
    Image.fromarray(a).save(path)


def vis_buffers(buf, smooth, flat, dep, cre, matl, palette, prefix):
    Hk, Wk = buf["mat"].shape
    bg = np.array([128, 128, 128], np.uint8)
    op = buf["mat"] >= 0

    def comp(rgba):
        o = np.tile(bg, (Hk, Wk, 1))
        o[rgba[..., 3] > 0] = rgba[rgba[..., 3] > 0, :3]
        return o
    save_png(comp(smooth), prefix + "_a_smooth.png")
    save_png(comp(flat), prefix + "_b_bands.png")
    # material id false colour
    rng = np.random.RandomState(7)
    lut = rng.randint(40, 255, (len(buf["mats"]) + 1, 3)).astype(np.uint8)
    mid = np.tile(bg, (Hk, Wk, 1)); mid[op] = lut[buf["mat"][op]]
    save_png(mid, prefix + "_b_matid.png")
    t = buf["t"]; tv = t[op]
    dimg = np.tile(bg, (Hk, Wk, 1))
    if tv.size:
        dn = (t - tv.min()) / max(np.ptp(tv), 1e-6)
        dimg[op] = (255 * (1 - dn[op]))[:, None].astype(np.uint8).repeat(3, 1)
    save_png(dimg, prefix + "_b_depth.png")
    nimg = np.tile(bg, (Hk, Wk, 1)); nimg[op] = ((buf["nrm"][op] * 0.5 + 0.5) * 255).astype(np.uint8)
    save_png(nimg, prefix + "_b_normal.png")
    e = comp(flat)
    e[dep] = (20, 10, 30); e[cre & ~dep] = (200, 30, 60); e[matl & ~dep & ~cre] = (40, 120, 220)
    save_png(e, prefix + "_c_edges.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant"); ap.add_argument("clip"); ap.add_argument("k", type=int)
    ap.add_argument("--dirs"); ap.add_argument("--frames")
    ap.add_argument("--big", default="")
    ap.add_argument("--crease", type=float, default=50.0)
    a = ap.parse_args()
    t0 = time.time()
    sc, pal = H.setup(a.variant, a.clip)
    k = a.k
    dirs = a.dirs.split(",") if a.dirs else sc.dirs
    n = len(sc.anim.keys)
    frames = [int(v) for v in a.frames.split(",")] if a.frames else list(range(n))
    big = {tuple([s.split(":")[0], int(s.split(":")[1])]) for s in a.big.split(",") if s}
    W, Hh = sc.size
    tag = f"{a.variant}__{a.clip}__k{k}"
    os.makedirs(os.path.join(H.EXP, "big"), exist_ok=True)
    os.makedirs(os.path.join(H.EXP, "frames"), exist_ok=True)
    pfs = {}
    sheet = np.zeros((len(dirs) * Hh * k, len(frames) * W * k, 4), np.uint8)
    bufmeta = {}
    edge_stats = []
    for r, d in enumerate(dirs):
        for c, i in enumerate(frames):
            prims, worlds = sc.primitives(i, d)
            hs = H.hs_for(sc, i, d, prims, worlds)
            buf = H.trace_prims(prims, pal, sc.size, sc.pivot, sc.cam, k, hs, sc.tracer)
            smooth, flat, bidx = H.colorize(buf, pal)
            dep, cre, matl = H.edges(buf, crease_deg=a.crease, mat_lines=True)
            skin = np.array([m == "skin" for m in buf["mats"]] + [False])[buf["mat"]]
            ecell = H.edge_cells(buf, (dep | cre) & ~skin)
            edge_stats.append(int(ecell.sum()))
            valid = buf["mat"] >= 0
            pfs[("V", d, i)] = H.resolve_vote_mean(buf, pal)
            pfs[("VM", d, i)] = H.resolve_vote_mode(buf, pal)
            pfs[("VME", d, i)] = H.resolve_vote_mode(buf, pal, edge=ecell)
            kc = H.kcentroid(flat, k, valid=valid)
            pfs[("KC", d, i)] = H.resolve_rgb(buf, pal, kc)
            pfs[("KCE", d, i)] = H.resolve_rgb(buf, pal, kc, edge=ecell)
            pfs[("KS", d, i)] = H.resolve_rgb(buf, pal, H.kcentroid(smooth, k, valid=valid))
            pfs[("AA", d, i)] = H.resolve_rgb(buf, pal, H.area_avg(smooth, k))
            bufmeta[(d, i)] = {kk: buf[kk] for kk in ("k", "mat", "t", "grp", "mats", "grp_names")}   # for PF material vote
            sheet[r * Hh * k:(r + 1) * Hh * k, c * W * k:(c + 1) * W * k] = smooth
            if (d, i) in big:
                vis_buffers(buf, smooth, flat, dep, cre, matl, pal,
                            os.path.join(H.EXP, "big", f"{tag}__{d}_f{i + 1}"))
        print(f"  traced {d} ({time.time() - t0:.0f}s)", flush=True)
    # Retro Diffusion pixel-art-fixer on the whole smooth sheet with a forced k grid (cells align with the grid)
    tmp_in = os.path.join(H.EXP, "big", f"_pf_in_{tag}.png")
    tmp_out = os.path.join(H.EXP, "big", f"_pf_out_{tag}.png")
    save_png(sheet, tmp_in)
    res = subprocess.run([FIXER, "-I", os.path.join(H.ROOT, "pipeline/tools/pixelfix.py"), tmp_in, tmp_out,
                          "--step", str(k), str(k)], capture_output=True, text=True)
    if res.returncode:
        print("pixfix failed", res.stderr[-800:])
        pf_low = None
    else:
        pf_low = np.array(Image.open(tmp_out).convert("RGBA")).astype(float)
        print("  pixfix", res.stdout.strip()[:200], pf_low.shape)
    for r, d in enumerate(dirs):
        for c, i in enumerate(frames):
            if pf_low is not None and pf_low.shape[0] == len(dirs) * Hh:
                low = pf_low[r * Hh:(r + 1) * Hh, c * W:(c + 1) * W]
                pfs[("PF", d, i)] = H.resolve_rgb(bufmeta[(d, i)], pal, low)
    del bufmeta
    os.remove(tmp_in)
    # pass 2: the shipped FIX chain on every method's PixelFrame
    out = {"variant": a.variant, "clip": a.clip, "k": k, "dirs": dirs, "frames": frames, "final": {}, "raw": {},
           "deliberate": {}, "body_bbox": {}, "edge_cells_mean": float(np.mean(edge_stats))}
    th = sc.char.get("render", {}).get("temporal_hold")
    do_hold = bool(th and sc.anim_data.get("loop") and a.clip in th.get("clips", []) and frames == list(range(n)))
    cur = {}
    for m in METHODS:
        if m != "N" and ("PF" == m and ("PF", dirs[0], frames[0]) not in pfs):
            continue
        sc.deliberate, sc.body_bbox = {}, {}
        fin = {}
        raw = {}
        for d in dirs:
            fin[d], raw[d] = [], []
            for i in frames:
                if m == "N":
                    fin[d].append(sc.render_base(i, d))
                    continue
                cur["pf"] = pfs[(m, d, i)]
                raw[d].append(R_outline(pfs[(m, d, i)].idx.copy(), pal))
                with H.patched(lambda *args: _copy_pf(cur["pf"])):
                    fin[d].append(sc.render_base(i, d))
        if do_hold:
            fin = {d: sc.temporal_hold(fin[d], d, th) for d in dirs}
        out["final"][m] = fin
        out["raw"][m] = raw
        out["deliberate"][m] = {f"{d}|{i}": sorted(v) for (d, i), v in sc.deliberate.items()}
        out["body_bbox"][m] = {f"{d}|{i}": v for (d, i), v in sc.body_bbox.items()}
        print(f"  fixed {m} ({time.time() - t0:.0f}s)", flush=True)
    out["temporal_hold"] = do_hold
    with open(os.path.join(H.EXP, "frames", f"{tag}.pkl"), "wb") as f:
        pickle.dump(out, f)
    print(f"done {tag} in {time.time() - t0:.0f}s")


def R_outline(idx, pal):
    return H.R.add_outline(idx, pal.special["outline"])


def _copy_pf(pf):
    c = H.R.PixelFrame(pf.idx.copy(), pf.depth.copy(), pf.group.copy(), pf.material.copy())
    c.group_names = pf.group_names
    return c


if __name__ == "__main__":
    main()
