# vcol_proj.py RAW.glb IN_DIR OUT.glb
# Colour a generated part from its own input views: each vertex picks the view its normal faces most (front/back/left),
# looks up the pixel by bbox mapping (image bbox <-> mesh bbox), snaps to the Level-D flat palette, outline pixels are
# filled by neighbour majority. Output vertex colours are linear (as in rest_mat.glb).
import sys, numpy as np, trimesh
from PIL import Image
src, idir, out = sys.argv[1:4]; part = sys.argv[4] if len(sys.argv) > 4 else ''
m = trimesh.load(src, force='mesh'); m = max(m.split(only_watertight=False), key=lambda c: len(c.faces))
V = m.vertices; N = m.vertex_normals; lo, hi = V.min(0), V.max(0)
PAL = np.array([[0xf8, 0xda, 0xc2], [0x3c, 0x32, 0x36], [0xc0, 0x3a, 0x3c], [0x84, 0x26, 0x3e], [0x44, 0x37, 0x4a], [0x55, 0x80, 0xa2], [0xee, 0xf0, 0xf5], [0x2a, 0x39, 0x5a], [0x1a, 0x12, 0x20], [0x28, 0x1c, 0x26]], float)
MAP = np.array([0, 1, 2, 2, 3, 5, 5, 5, -1, 1])  # -> 0 skin 1 hair 2 red 3 dark(obi/boot) 5 eyes, -1 outline
OUTC = np.array([[0xf8, 0xda, 0xc2], [0x3c, 0x32, 0x36], [0xc0, 0x3a, 0x3c], [0x44, 0x37, 0x4a], [0x2c, 0x20, 0x2c], [0x55, 0x80, 0xa2]], float)
if part == 'head': OUTC[2] = [0xe8, 0x60, 0x4f]  # red on the head = bow
if part == 'leg': OUTC[3] = [0x2c, 0x20, 0x2c]   # dark on the leg = boot
def look(view, u):
    im = np.asarray(Image.open(f'{idir}/{view}.png').convert('RGBA')).astype(float)
    ys, xs = np.nonzero(im[..., 3] > 30); t, b, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    px = np.clip(np.round(x0 + (u - u.min()) / (u.max() - u.min()) * (x1 - x0)).astype(int), 0, im.shape[1] - 1)
    py = np.clip(np.round(t + (hi[1] - V[:, 1]) / (hi[1] - lo[1]) * (b - t)).astype(int), 0, im.shape[0] - 1)
    c = im[py, px, :3]; d = ((c[:, None, :] - PAL[None]) ** 2).sum(2); l = MAP[d.argmin(1)]
    l[im[py, px, 3] < 30] = -1; return l
Lf, Lb, Ll = look('front', V[:, 0]), look('back', -V[:, 0]), look('left', -V[:, 2])
w = np.stack([N[:, 2] - 0.25, -N[:, 2], np.abs(N[:, 0]) * 1.2], 1); pick = w.argmax(1)
lab = np.choose(pick, [Lf, Lb, Ll])
REMAP = {'head': {3: 1}, 'torso': {1: 3, 5: 3}, 'skirt': {0: 2, 1: 2, 3: 2, 5: 2}, 'leg': {1: 3, 2: 3, 5: 3}, 'arm': {1: 2, 3: 2, 5: 2}}.get(part, {})
for a_, b_ in REMAP.items(): lab[lab == a_] = b_
nb = m.vertex_neighbors
for it in range(12):
    bad = np.nonzero(lab < 0)[0]
    if not len(bad): break
    new = lab.copy()
    for i in bad:
        k = lab[nb[i]]; k = k[k >= 0]
        if len(k): new[i] = np.bincount(k).argmax()
    lab = new
lab[lab < 0] = 1
for it in range(8 if part == 'head' else 2):  # majority smoothing (head: removes thin skin streaks on hair locks)
    new = lab.copy()
    for i in range(len(V)):
        c = np.bincount(lab[nb[i]], minlength=6); c[lab[i]] += 1; new[i] = c.argmax()
    lab = new
lin = lambda c: np.where(c / 255 <= 0.04045, c / 255 / 12.92, ((c / 255 + 0.055) / 1.055) ** 2.4) * 255
col = lin(OUTC[lab]).round().astype(np.uint8)
m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.c_[col, np.full(len(col), 255, np.uint8)])
m.export(out); print(out, np.bincount(lab, minlength=6))
