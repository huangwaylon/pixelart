# matid.py IN.glb OUT.glb TURN_DIR : project design turnaround, classify to material IDs, write flat palette vertex colours (+ ids .npy)
# glb frame (Omni skeleton frame): Y up, faces +Z. Height bands from the Omni rest skeleton.
import sys, numpy as np, trimesh
from PIL import Image
src, out, td = sys.argv[1:4]
m = trimesh.load(src, force='mesh'); V = m.vertices; N = m.vertex_normals
views = {'front': (np.array([0, 0, 1.]), lambda p: p[:, 0]), 'back': (np.array([0, 0, -1.]), lambda p: -p[:, 0]),
         'left': (np.array([1., 0, 0]), lambda p: -p[:, 2]), 'right': (np.array([-1., 0, 0]), lambda p: p[:, 2])}
ylo, yhi = V[:, 1].min(), V[:, 1].max(); H = yhi - ylo
pick = np.stack([N @ d for d, _ in views.values()], 1).argmax(1)
from PIL import ImageFilter
NAMES = ['skin', 'hair', 'dress', 'obi', 'boots', 'eyes', 'bow']
PAL = np.array([[0xf8, 0xda, 0xc2], [0x3c, 0x32, 0x36], [0xc0, 0x3a, 0x3c], [0x44, 0x37, 0x4a], [0x2c, 0x20, 0x2c], [0x55, 0x80, 0xa2], [0xe8, 0x60, 0x4f]])
def label_image(path):
    im = np.asarray(Image.open(path).convert('RGB')).astype(int); r, g, b = im[..., 0], im[..., 1], im[..., 2]; lum = im.mean(2)
    ys, xs = np.nonzero(np.abs(im - 255).sum(2) > 40); t, bt = ys.min(), ys.max()
    yy = (bt - np.arange(im.shape[0]))[:, None] / (bt - t) * np.ones((1, im.shape[1]))
    L = np.full(lum.shape, 7)  # 7 = bg
    red = (r > g + 60) & (r > b + 50); blue = (b > r + 25) & (b > 90); dark = (lum < 110) & ~red & ~blue
    L[(lum < 240) & ~red & ~blue & ~dark] = 0
    L[red] = np.where(yy[red] > 0.62, 6, 2); L[blue & (yy > 0.5)] = 5
    L[dark & (yy > 0.5)] = 1; L[dark & (yy < 0.12)] = 4; L[dark & (yy >= 0.12) & (yy <= 0.5)] = 3
    L[lum >= 240] = 7
    Li = Image.fromarray(L.astype(np.uint8)).filter(ImageFilter.ModeFilter(9)).filter(ImageFilter.ModeFilter(5))
    return np.asarray(Li).astype(int), t, bt, xs.min(), xs.max()
lab = np.full(len(V), -1)
for k, (name, (d, ufn)) in enumerate(views.items()):
    L, t, b, x0, x1 = label_image(f'{td}/{name}.png'); s = (b - t) / H
    u = ufn(V); px = np.clip(np.round((x0 + x1) / 2 + (u - (u.min() + u.max()) / 2) * s).astype(int), 0, L.shape[1] - 1)
    py = np.clip(np.round(t + (yhi - V[:, 1]) * s).astype(int), 0, L.shape[0] - 1)
    sel = pick == k; lab[sel] = L[py[sel], px[sel]]
lab[lab == 7] = -1
# geometric overrides (bands measured on design front.png, normalised height from feet)
y = (V[:, 1] - ylo) / H; proj = lab.copy()
skel = np.loadtxt(sys.argv[4]) if len(sys.argv) > 4 else None
lab[:] = 2
lab[y < 0.10] = 4
LX, CZ = (abs(skel[45, 0]), skel[0, 2]) if skel is not None else (0.08, 0.09)
legd = np.minimum(np.hypot(V[:, 0] - LX, V[:, 2] - CZ), np.hypot(V[:, 0] + LX, V[:, 2] - CZ))
lab[(y >= 0.10) & (y < 0.26) & (legd < 0.095)] = 0
torso = np.hypot(V[:, 0], (V[:, 2] - CZ) * 1.2) < 0.23
lab[(y >= 0.385) & (y < 0.45) & torso] = 3
if skel is not None:
    for wi in (9, 28):  # Wrist.R, Wrist.L rows
        w = skel[wi]; c = (w[:3] + w[3:]) / 2
        lab[np.linalg.norm(V - c, axis=1) < 0.075] = 0
head = y >= 0.56
hp = proj[head]; front = (pick[head] == 0)
hl = np.full(hp.shape, 1)
hl[np.isin(hp, [2, 6]) & (y[head] > 0.72)] = 6
hl[(hp == 0) & front & (y[head] < 0.72)] = 0
hl[(hp == 5) & front] = 5
lab[head] = hl
# fill unknowns + majority smoothing over vertex neighbours
nb = m.vertex_neighbors
for it in range(30):
    unk = np.nonzero(lab < 0)[0]
    if len(unk) == 0: break
    new = lab.copy()
    for i in unk:
        v = [lab[j] for j in nb[i] if lab[j] >= 0]
        if v: new[i] = np.bincount(v).argmax()
    lab = new
lab[lab < 0] = 2
for it in range(2):
    new = lab.copy()
    for i in range(len(V)):
        c = np.bincount(lab[nb[i]], minlength=7); c[lab[i]] += 1; new[i] = c.argmax()
    lab = new
BS = float(__import__('os').environ.get('BOW_SCALE', '1'))
if BS != 1:
    bw = lab == 6; cb = V[bw].mean(0); cb[1] = V[bw][:, 1].min(); V = m.vertices.copy(); V[bw] = cb + (V[bw] - cb) * BS; m.vertices = V
print({NAMES[k]: int((lab == k).sum()) for k in range(7)})
lin = PAL[lab] / 255.0; lin = np.where(lin <= 0.04045, lin / 12.92, ((lin + 0.055) / 1.055) ** 2.4)
col = np.concatenate([np.round(lin * 255), np.full((len(V), 1), 255)], 1).astype(np.uint8)
m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col); m.export(out); np.save(out.replace('.glb', '_ids.npy'), lab)
