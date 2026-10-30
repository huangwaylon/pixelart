"""Visual hull from R2's orthographic turnaround (front/left/back/right, shared scale, same feet baseline).

Usage: venv/bin/python -I vhull.py REF_DIR OUT.glb [--res 256] [--views front,left,back,right]
glb frame: Y up, faces +Z, her left = +X. R2 convention: yaw 0 front, +90 = camera at her left (she faces
screen-left), 180 back, -90 camera at her right. Per view screen column:
  front: cx + X   back: cx - X   left: cx - Z   right: cx + Z     row: same for all views.
A voxel is inside if every view's alpha mask covers its projection; the carved volume is meshed with marching cubes.
This is the multi-view prior Omni cannot take directly (one image + one control): fed as point / voxel control.
"""
import argparse, json, os
import numpy as np, trimesh
from PIL import Image
from scipy import ndimage
from skimage import measure

ap = argparse.ArgumentParser()
ap.add_argument('ref'); ap.add_argument('out')
ap.add_argument('--res', type=int, default=256); ap.add_argument('--views', default='front,left,back,right')
a = ap.parse_args()
M = {}
for v in a.views.split(','):
    al = np.asarray(Image.open(f'{a.ref}/{v}.png').convert('RGBA'))[..., 3] > 127
    M[v] = al
H, W = next(iter(M.values())).shape
rows = np.nonzero(np.any(np.stack([m.any(1) for m in M.values()]), 0))[0]
top, bot = rows.min(), rows.max()
cxs = {}
for v, m in M.items():
    cols = np.nonzero(m[int(bot - 0.06 * (bot - top)):bot + 1].any(0))[0]  # feet band centre
    cxs[v] = (cols.min() + cols.max()) / 2
half = 0.5 * max(np.ptp(np.nonzero(m.any(0))[0]) for m in M.values()) + 4
n = a.res
ys = np.linspace(top - 2, bot + 2, n)
step = ys[1] - ys[0]
xs = np.arange(-half, half + step, step)
X, Z = np.meshgrid(xs, xs, indexing='ij')
vol = np.zeros((len(xs), n, len(xs)), bool)   # (x, row, z)
for j, r in enumerate(ys):
    ri = int(round(r))
    if ri < 0 or ri >= H:
        continue
    inside = np.ones_like(X, bool)
    for v, m in M.items():
        if v == 'front': col = cxs[v] + X
        elif v == 'back': col = cxs[v] - X
        elif v == 'left': col = cxs[v] - Z
        else: col = cxs[v] + Z
        ci = np.round(col).astype(int)
        ok = (ci >= 0) & (ci < W)
        cov = np.zeros_like(inside); cov[ok] = m[ri, ci[ok]]
        inside &= cov
    vol[:, j, :] = inside
vol = ndimage.binary_opening(vol, iterations=1)
lab, k = ndimage.label(vol)
if k > 1:
    sz = ndimage.sum(vol, lab, range(1, k + 1)); vol = lab == (1 + int(np.argmax(sz)))
volf = ndimage.gaussian_filter(vol.astype(np.float32), 1.0)
verts, faces, _, _ = measure.marching_cubes(np.pad(volf, 1), 0.5)
verts -= 1
# to glb: x = xs, y = -(row) (up), z = xs
vx = xs[0] + verts[:, 0] * step; vy = -(ys[0] + verts[:, 1] * step); vz = xs[0] + verts[:, 2] * step
mesh = trimesh.Trimesh(np.stack([vx, vy, vz], 1) / (bot - top), faces[:, ::-1], process=True)
if mesh.volume < 0:
    mesh.invert()
mesh.export(a.out)
print('vhull', a.out, 'faces', len(mesh.faces), 'extent', np.round(mesh.extents / mesh.extents[1], 3), 'watertight', mesh.is_watertight)
