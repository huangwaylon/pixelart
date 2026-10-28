# polish.py IN_DIR OUT_DIR : hybrid v3 = obi as a real dark shell (convex hull of the torso band section x1.04, extruded
# y -0.25..-0.105) + wider B sleeves (x/z 1.2 about the shoulder top).
import sys, os, shutil, glob, numpy as np, trimesh
ind, od = sys.argv[1:3]; os.makedirs(od, exist_ok=True)
for f in glob.glob(f'{ind}/*.glb'): shutil.copy(f, od)
lin = lambda c: (np.where(np.array(c) / 255 <= 0.04045, np.array(c) / 255 / 12.92, ((np.array(c) / 255 + 0.055) / 1.055) ** 2.4) * 255).round().astype(np.uint8)
t = trimesh.load(f'{ind}/torso.glb', force='mesh'); v = t.vertices
band = v[(v[:, 1] > -0.25) & (v[:, 1] < -0.105)]
c = band[:, [0, 2]].mean(0); ang = np.arctan2(band[:, 2] - c[1], band[:, 0] - c[0]); rad = np.hypot(band[:, 0] - c[0], band[:, 2] - c[1])
K = 72; bins = ((ang + np.pi) / (2 * np.pi) * K).astype(int) % K
r = np.array([rad[bins == i].max() if (bins == i).any() else np.nan for i in range(K)])
r = np.where(np.isnan(r), np.nanmean(r), r); r = np.convolve(np.r_[r[-2:], r, r[:2]], np.ones(5) / 5, 'valid') * 1.04  # smooth ring, 4% proud
th = -np.pi + (np.arange(K) + 0.5) * 2 * np.pi / K
ring = np.c_[c[0] + r * np.cos(th), c[1] + r * np.sin(th)]
y0, y1 = -0.25, -0.105
VV = np.r_[np.c_[ring[:, 0], np.full(K, y0), ring[:, 1]], np.c_[ring[:, 0], np.full(K, y1), ring[:, 1]], [[c[0], y0, c[1]], [c[0], y1, c[1]]]]
F = []
for i in range(K):
    j = (i + 1) % K; F += [[i, j, K + j], [i, K + j, K + i], [2 * K, j, i], [2 * K + 1, K + i, K + j]]
ob = trimesh.Trimesh(VV, F, process=True); ob.fix_normals()
ob.visual = trimesh.visual.ColorVisuals(ob, vertex_colors=np.tile(np.r_[lin([0x44, 0x37, 0x4a]), 255], (len(ob.vertices), 1)))
print('obi bounds', ob.bounds.round(3).tolist(), 'torso band', band.min(0).round(3).tolist(), band.max(0).round(3).tolist())
tt = trimesh.util.concatenate([t, ob]); tt.export(f'{od}/torso.glb')
for n in ('arm_L', 'arm_R'):
    a = trimesh.load(f'{ind}/{n}.glb', force='mesh'); lo, hi = a.bounds
    p = np.array([(lo[0] + hi[0]) / 2, hi[1], (lo[2] + hi[2]) / 2]); y = a.vertices[:, 1]
    k = 1 + 0.25 * np.clip((hi[1] - y) / (hi[1] - lo[1]), 0, 1)  # widen toward the cuff (bell), shoulder unchanged
    a.vertices[:, [0, 2]] = p[[0, 2]] + (a.vertices[:, [0, 2]] - p[[0, 2]]) * k[:, None]
    a.export(f'{od}/{n}.glb')
