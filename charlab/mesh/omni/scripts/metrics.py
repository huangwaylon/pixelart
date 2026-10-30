"""Mesh metrics for Omni experiments.

Usage: venv/bin/python -I metrics.py RENDER_DIR OUT.jsonl REF_FRONT_MASK [--side SIDE_MASK] [--res 384] MESH.glb ...
For each mesh: tris, watertight, components / floater fraction, mirror-symmetry error, silhouette IoU of the front
(and side) clay renders (render.py framing: ortho 2.3 units, height 2, feet at z=0, centred) vs the reference mask
scaled to the same height and centred on its bbox. Appends JSON rows to OUT.jsonl (one per mesh, keyed by name).
"""
import argparse, json, os
import numpy as np, trimesh
from PIL import Image
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument('rdir'); ap.add_argument('out'); ap.add_argument('front')
ap.add_argument('meshes', nargs='+')
ap.add_argument('--side'); ap.add_argument('--res', type=int, default=384)
a = ap.parse_args()
R = a.res
PX_H = 2.0 / 2.3 * R  # mesh height in px
FEET = R / 2 + (1.0 / 2.3) * R  # feet row (camera centred at z=1)


def ref_canvas(path):
    m = np.asarray(Image.open(path).convert('L')) > 127
    ys, xs = np.nonzero(m)
    crop = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape; s = PX_H / h
    im = Image.fromarray(crop.astype(np.uint8) * 255).resize((max(1, round(w * s)), round(PX_H)), Image.BILINEAR)
    c = np.zeros((R, R), bool); arr = np.asarray(im) > 127
    y0 = int(round(FEET - arr.shape[0])); x0 = int(round(R / 2 - arr.shape[1] / 2))
    c[y0:y0 + arr.shape[0], x0:x0 + arr.shape[1]] = arr
    return c


def iou(render, ref):
    m = np.asarray(Image.open(render))[..., 3] > 127
    return float((m & ref).sum() / max(1, (m | ref).sum()))


refF = ref_canvas(a.front)
refS = ref_canvas(a.side) if a.side else None
rows = []
for p in a.meshes:
    name = os.path.splitext(os.path.basename(p))[0]
    m = trimesh.load(p, force='mesh')
    parts = m.split(only_watertight=False)
    nf = len(m.faces); big = max(parts, key=lambda q: len(q.faces))
    sig = [q for q in parts if len(q.faces) > 0.001 * nf]
    V = m.vertices; h = np.ptp(V[:, 1])
    pts = np.asarray(big.sample(20000)); c = (pts.min(0) + pts.max(0)) / 2
    q = pts - c; mir = q * [-1, 1, 1]
    d = cKDTree(q).query(mir)[0]
    row = dict(name=name, tris=nf, watertight=bool(m.is_watertight), main_watertight=bool(big.is_watertight),
               components=len(parts), sig_components=len(sig), floater_frac=round(1 - len(big.faces) / nf, 4),
               sym_err_pct=round(100 * float(d.mean()) / h, 3), sym_p95_pct=round(100 * float(np.percentile(d, 95)) / h, 3),
               self_intersect=None)
    fr = os.path.join(a.rdir, name + '_front.png')
    if os.path.exists(fr):
        row['iou_front'] = round(iou(fr, refF), 4)
    if refS is not None:
        sr = os.path.join(a.rdir, name + '_side.png')
        if os.path.exists(sr):
            row['iou_side'] = round(iou(sr, refS), 4)
    print(json.dumps(row), flush=True)
    rows.append(row)
with open(a.out, 'a') as f:
    for r in rows:
        f.write(json.dumps(r) + '\n')
