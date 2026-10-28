"""Metrics + boards + GIFs for the hi-res experiment.

  .venv/bin/python -B REVIEW/exp/2026-10-28_snowpeak_hires/scripts/analyze.py
Reads frames/*.pkl, writes metrics.json, metrics.md, boards/*.png, boards/*.gif.
Metrics (pipeline/qa.py definitions where they exist):
  orphans   qa.orphan_count, face colours + generator-deliberate pixels protected (as run_qa)
  jaggies   render.jaggy_count summed over frames
  colours   distinct palette indices over the clip / max per frame
  hdelta    max over frames of (max - min) body-bbox height across directions; h = standing height per dir
  ABA       temporal boil: pixels with f[t-1] == f[t+1] != f[t] (cyclic), mean per frame
  dpx       mean pixels changed between consecutive frames
  coatisl   islands (<= 3 px, 4-conn) of non-coat colours fully enclosed by coat-ramp pixels (the "teal in coat" bug)
  diffN     % of opaque pixels that differ from the native shipped pass
"""
import glob
import json
import os
import pickle
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hrlib as H  # noqa: E402
from pipeline import qa  # noqa: E402
from pipeline.palette import Palette  # noqa: E402

BG = (128, 128, 128)
LABEL = {"N": "native (shipped ss3)", "V": "vote mean-lam", "VM": "vote mode-band", "KC": "k-centroid bands",
         "KS": "k-centroid smooth", "AA": "area avg+lock", "PF": "RD pixel-fixer", "VME": "VM + edge pass",
         "KCE": "KC + edge pass"}


def palette_for(variant):
    spec = H.B.load_variant(variant)
    pal = Palette(H.B.variant_inputs(spec)[1])
    for m, names in spec.get("ramp_overrides", {}).items():
        pal.ramps[m] = names
    return pal


def rgb(pal, idx, bg=BG):
    a = pal.to_rgba(idx)
    o = np.zeros(idx.shape + (3,), np.uint8); o[:] = bg
    m = a[..., 3] > 0
    o[m] = a[m, :3]
    return o


def coat_islands(f, pal):
    coat = {pal.index[c] for m in ("coat",) for c in pal.ramps.get(m, [])}
    Hh, W = f.shape
    inc = np.isin(f, list(coat))
    cand = (f >= 0) & ~inc
    seen = np.zeros_like(cand)
    n = 0
    for y in range(Hh):
        for x in range(W):
            if not cand[y, x] or seen[y, x]:
                continue
            comp, st = [], [(y, x)]; seen[y, x] = True
            while st:
                cy, cx = st.pop(); comp.append((cy, cx))
                for yy, xx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= yy < Hh and 0 <= xx < W and cand[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True; st.append((yy, xx))
                if len(comp) > 3:
                    break
            if len(comp) > 3:
                continue
            cs = set(comp)
            ok = True
            for cy, cx in comp:
                for yy, xx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if (yy, xx) in cs:
                        continue
                    if not (0 <= yy < Hh and 0 <= xx < W and inc[yy, xx]):
                        ok = False
            n += ok
    return n


def metrics(o, m, pal):
    fin = o["final"][m]
    dirs, frames = o["dirs"], o["frames"]
    face = [pal.special[k] for k in ("eye", "mouth", "blush", "catchlight") if k in pal.special]
    delib = o["deliberate"][m]
    orph = jag = isl = 0
    used = set(); cpf = 0
    for d in dirs:
        for j, i in enumerate(frames):
            f = fin[d][j]
            prot = np.isin(f, face)
            for y, x in delib.get(f"{d}|{i}", []):
                prot[y, x] = True
            orph += qa.orphan_count(f, prot)
            jag += H.R.jaggy_count(f)
            isl += coat_islands(f, pal)
            u = set(np.unique(f[f >= 0]).tolist()); used |= u; cpf = max(cpf, len(u))
    bb = o["body_bbox"][m]
    hd = 0
    for i in frames:
        hs = [bb[f"{d}|{i}"][3] - bb[f"{d}|{i}"][1] + 1 for d in dirs if f"{d}|{i}" in bb]
        if hs:
            hd = max(hd, max(hs) - min(hs))
    hstand = {d: bb[f"{d}|{frames[-1]}"][3] - bb[f"{d}|{frames[-1]}"][1] + 1 for d in dirs if f"{d}|{frames[-1]}" in bb}
    aba = dpx = 0.0; nfl = 0
    if len(frames) >= 3:
        for d in dirs:
            seq = fin[d]
            T = len(seq)
            for t in range(T):
                a, b, c = seq[t - 1], seq[t], seq[(t + 1) % T]
                aba += int(((a == c) & (b != a)).sum())
                dpx += int((b != a).sum())
                nfl += 1
    nf = len(dirs) * len(frames)
    out = dict(orphans=orph, jaggies=jag, jag_per_frame=round(jag / nf, 2), colours=len(used), max_cpf=cpf,
               hdelta=hd, h_stand=hstand, coat_islands=isl, isl_per_frame=round(isl / nf, 2))
    if nfl:
        out["ABA_per_frame"] = round(aba / nfl, 2)
        out["dpx_per_frame"] = round(dpx / nfl, 2)
    if m != "N":
        diff = tot = 0
        for d in dirs:
            for j in range(len(frames)):
                a, b = fin[d][j], o["final"]["N"][d][j]
                op = (a >= 0) | (b >= 0)
                diff += int(((a != b) & op).sum()); tot += int(op.sum())
        out["diffN_pct"] = round(100 * diff / max(tot, 1), 1)
    return out


def label_img(arr, text, scale):
    im = Image.fromarray(arr).resize((arr.shape[1] * scale, arr.shape[0] * scale), Image.NEAREST)
    can = Image.new("RGB", (im.width, im.height + 14), (40, 40, 44))
    can.paste(im, (0, 14))
    ImageDraw.Draw(can).text((2, 1), text, fill=(240, 240, 220))
    return can


def grid(cells, ncol, pad=4, bg=(40, 40, 44)):
    w = max(c.width for c in cells); h = max(c.height for c in cells)
    nrow = (len(cells) + ncol - 1) // ncol
    can = Image.new("RGB", (ncol * (w + pad) + pad, nrow * (h + pad) + pad), bg)
    for n, c in enumerate(cells):
        can.paste(c, (pad + (n % ncol) * (w + pad), pad + (n // ncol) * (h + pad)))
    return can


def title(im, text):
    can = Image.new("RGB", (im.width, im.height + 22), (25, 25, 28))
    can.paste(im, (0, 22))
    ImageDraw.Draw(can).text((6, 5), text, fill=(255, 255, 210))
    return can


def crop_box(o, dirs, frames, pad=2):
    ys, xs = [], []
    for m in o["final"]:
        for d in dirs:
            for j in range(len(frames)):
                yy, xx = np.nonzero(o["final"][m][d][j] >= 0)
                ys += [yy.min(), yy.max()]; xs += [xx.min(), xx.max()]
    return max(min(ys) - pad, 0), min(max(ys) + pad + 1, 64), max(min(xs) - pad, 0), min(max(xs) + pad + 1, 48)


def board(o, pal, methods, dirs, frame, scale, text, raw=False, crop=True):
    cells = []
    y0, y1, x0, x1 = crop_box(o, dirs, o["frames"]) if crop else (0, 64, 0, 48)
    for d in dirs:
        for m in methods:
            src = o["raw" if raw and m != "N" else "final"][m]
            j = o["frames"].index(frame)
            cells.append(label_img(rgb(pal, src[d][j])[y0:y1, x0:x1], f"{d} {m}" if scale < 3 else f"{d} {m}", scale))
    return title(grid(cells, len(methods)), text)


def main():
    os.makedirs(os.path.join(H.EXP, "boards"), exist_ok=True)
    runs = {}
    for p in sorted(glob.glob(os.path.join(H.EXP, "frames", "*.pkl"))):
        with open(p, "rb") as f:
            o = pickle.load(f)
        runs[(o["variant"], o["clip"], o["k"])] = o
    pals = {v: palette_for(v) for v in {k[0] for k in runs}}
    allm = {}
    for key, o in sorted(runs.items()):
        pal = pals[key[0]]
        allm["{}|{}|k{}".format(*key)] = {m: metrics(o, m, pal) for m in o["final"]}
        allm["{}|{}|k{}".format(*key)]["_meta"] = {"dirs": o["dirs"], "frames": len(o["frames"]),
                                                    "temporal_hold": o["temporal_hold"],
                                                    "edge_cells_mean": o["edge_cells_mean"]}
    # shipped sanity: method N == shipped out/variants sheet
    for key, o in runs.items():
        v, c, k = key
        sp = os.path.join(H.ROOT, "out", "variants", f"{v}__{c}", f"{c}_sheet.png")
        if os.path.exists(sp) and o["frames"] == list(range(len(o["frames"]))):
            sh = np.array(Image.open(sp).convert("RGBA"))
            pal = pals[v]
            dirs_all = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
            bad = 0
            for d in o["dirs"]:
                r = dirs_all.index(d)
                for j in o["frames"]:
                    cell = sh[r * 64:(r + 1) * 64, j * 48:(j + 1) * 48]
                    bad += int((cell != pal.to_rgba(o["final"]["N"][d][j])).any(-1).sum())
            allm["{}|{}|k{}".format(*key)]["_meta"]["N_vs_shipped_px"] = bad
    with open(os.path.join(H.EXP, "metrics.json"), "w") as f:
        json.dump(allm, f, indent=1)
    cols = ["orphans", "jag_per_frame", "colours", "max_cpf", "hdelta", "isl_per_frame", "ABA_per_frame",
            "dpx_per_frame", "diffN_pct"]
    lines = []
    for key, mm in allm.items():
        meta = mm["_meta"]
        lines.append(f"\n### {key}  ({len(meta['dirs'])} dirs x {meta['frames']} frames; temporal_hold={meta['temporal_hold']}"
                     f"; N vs shipped px={meta.get('N_vs_shipped_px', 'n/a')})\n")
        lines.append("| method | " + " | ".join(cols) + " | h_stand |")
        lines.append("|---" * (len(cols) + 2) + "|")
        for m, r in mm.items():
            if m == "_meta":
                continue
            hs = r["h_stand"]
            lines.append(f"| {m} | " + " | ".join(str(r.get(c, "")) for c in cols) +
                         f" | {min(hs.values())}-{max(hs.values())} |")
    with open(os.path.join(H.EXP, "metrics.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    B = os.path.join(H.EXP, "boards")
    ms = ["N", "V", "VM", "KC", "KS", "AA", "PF", "VME", "KCE"]
    for key, o in runs.items():
        v, c, k = key
        pal = pals[v]
        ds = [d for d in ("S", "SE", "E") if d in o["dirs"]]
        f0 = o["frames"][0] if c == "idle" else o["frames"][min(2, len(o["frames"]) - 1)]
        mm = [m for m in ms if m in o["final"]]
        board(o, pal, mm, ds, f0, 4, f"{v} {c} f{f0 + 1}  hi-res k={k} -> 48x64, then shipped FIX chain. 4x nearest").save(
            f"{B}/{v}__{c}__k{k}__methods_4x.png")
        board(o, pal, mm, ds, f0, 1, f"{v} {c} 1x").save(f"{B}/{v}__{c}__k{k}__methods_1x.png")
        if c == "idle":
            board(o, pal, mm, ds, f0, 4, f"{v} {c} k={k} RAW (resolve only + plain outline, no FIX chain) 4x",
                  raw=True).save(f"{B}/{v}__{c}__k{k}__raw_4x.png")
    print("boards written")


if __name__ == "__main__":
    main()
