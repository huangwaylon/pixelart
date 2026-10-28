"""S6 round-1 POLISH pass (Claude hand pixel artist).

sprite/<stem>.png  --(polished/ops/<stem>.ops via draw.py ops, each op commented with its reason)-->
                   --(safe hole fill: 1-3 px transparent specks enclosed inside hair/outline)-->
polished/<stem>.png  (+ <stem>_hires.png = x8 nearest view; S6 is hand-drawn at 1x, there is no painted hi-res)

Run: .venv/bin/python tools/hybrid/s6/polish_r1.py
"""
import json
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import draw as D  # noqa: E402
import hylib as H  # noqa: E402
import pixgrid as PG  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
R1 = os.path.join(ROOT, "hybrid", "S6_claude_pixel", "r1")
SRC, OUT, OPS = os.path.join(R1, "sprite"), os.path.join(R1, "polished"), os.path.join(R1, "polished", "ops")

PAL = H.palette()
INV = {}
for ch, name in PG.STD.items():
    try:
        INV[tuple(PAL.rgba(PAL.resolve(name)))] = ch
    except Exception:
        pass
# a hole touching any of these is a legit gap (ribbon / blade / FX), not a speck
KEEP_NEAR = set("pPtTwS")


def fill_holes(a):
    """fill 1-3 px enclosed transparent specks with the dominant neighbour (hair inside hair, K in outline)."""
    t = a[..., 3] == 0
    lab, n = ndimage.label(t)
    border = set(lab[0]) | set(lab[-1]) | set(lab[:, 0]) | set(lab[:, -1])
    fixed = []
    for i in range(1, n + 1):
        if i in border:
            continue
        m = lab == i
        if m.sum() > 3:
            continue
        ring = ndimage.binary_dilation(m) & ~m
        c = Counter(INV.get(tuple(p), "?") for p in a[ring])
        if set(c) & KEEP_NEAR or "?" in c:
            continue
        body = [(k, v) for k, v in c.most_common() if k != "K"]
        ch = body[0][0] if body and body[0][1] >= 3 else "K"
        a[m] = D.col(ch)
        ys, xs = np.where(m)
        fixed.append((ch, list(zip(xs.tolist(), ys.tolist()))))
    return fixed


def main():
    os.makedirs(OUT, exist_ok=True)
    log = {}
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".png"):
            continue
        stem = f[:-4]
        a = np.array(Image.open(os.path.join(SRC, f)).convert("RGBA"))
        before = a.copy()
        cv = D.Canvas(a)
        opf = os.path.join(OPS, stem + ".ops")
        n_ops = 0
        if os.path.exists(opf):
            for line in open(opf):
                op = line.split("#", 1)[0].strip()
                if op:
                    D.run_op(cv, op, OUT)
                    n_ops += 1
        holes = fill_holes(cv.a)
        Image.fromarray(cv.a, "RGBA").save(os.path.join(OUT, f))
        Image.fromarray(cv.a, "RGBA").resize((1024, 1024), Image.NEAREST).save(os.path.join(OUT, stem + "_hires.png"))
        changed = int((cv.a != before).any(-1).sum())
        log[stem] = {"ops": n_ops, "holes_filled": holes, "pixels_changed": changed}
        print(f"{stem:16s} ops={n_ops:2d} holes={len(holes):2d} changed={changed}")
    json.dump(log, open(os.path.join(OUT, "polish_log.json"), "w"), indent=1)
    print("total pixels changed", sum(v["pixels_changed"] for v in log.values()))


if __name__ == "__main__":
    main()
