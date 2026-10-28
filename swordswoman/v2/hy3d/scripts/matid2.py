# matid2.py IN.glb OUT.glb TURN_DIR SKEL.txt [bow_scale=1.3] [bang_push=1]
# Clean material IDs by "visual hull" labelling: each vertex looks up the design FRONT label at (x,y) and the SIDE (left.png) label at (z,y),
# regardless of normal, then height bands measured on turnD/front.png decide body parts. Then geometric fixes: bow x1.3, bangs pushed back
# off the face so the eyes read from the 30deg iso camera.  glb frame: Y up, faces +Z, her left = +X.
import sys, numpy as np, trimesh
from PIL import Image, ImageFilter
src, out, td, skp = sys.argv[1:5]
BS = float(sys.argv[5]) if len(sys.argv) > 5 else 1.3
BANG = int(sys.argv[6]) if len(sys.argv) > 6 else 1
m = trimesh.load(src, force='mesh'); V = m.vertices.copy(); N = m.vertex_normals
sk = np.loadtxt(skp)
ylo, yhi = V[:, 1].min(), V[:, 1].max()
NAMES = ['skin', 'hair', 'dress', 'obi', 'boots', 'eyes', 'bow']
PAL = np.array([[0xf8, 0xda, 0xc2], [0x3c, 0x32, 0x36], [0xc0, 0x3a, 0x3c], [0x44, 0x37, 0x4a], [0x2c, 0x20, 0x2c], [0x55, 0x80, 0xa2], [0xe8, 0x60, 0x4f]])
S, R, B, D, BG = 0, 1, 2, 3, 4  # image classes: skin, red, blue, dark, bg

def classify(path):
    im = np.asarray(Image.open(path).convert('RGB')).astype(int); r, g, b = im[..., 0], im[..., 1], im[..., 2]; l = im.mean(2)
    L = np.full(l.shape, S)
    L[(r > g + 60) & (r > b + 50)] = R; L[(b > r + 25) & (b > 90)] = B; L[(l < 110) & (L == S)] = D; L[l > 240] = BG
    L = np.asarray(Image.fromarray(L.astype(np.uint8)).filter(ImageFilter.ModeFilter(7))).astype(int)
    rf = Image.fromarray(((L == R) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.MinFilter(15))
    L[(np.asarray(rf) > 0) & (L == D)] = 5  # 5 = dark line enclosed by red (bow knot/outline)
    nr = np.asarray(Image.fromarray(((L == R) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(13))) > 0
    L[nr & (L == D)] = 6                    # 6 = dark outline hugging red (bow rim)
    ys, xs = np.nonzero(L != BG); return L, ys.min(), ys.max(), xs.min(), xs.max()

def lookup(path, u):  # u: horizontal mesh coord that maps to image x (increasing to the right)
    L, t, b, x0, x1 = classify(path); s = (b - t) / (yhi - ylo)
    px = np.clip(np.round((x0 + x1) / 2 + (u - (u.min() + u.max()) / 2) * s).astype(int), 0, L.shape[1] - 1)
    py = np.clip(np.round(t + (yhi - V[:, 1]) * s).astype(int), 0, L.shape[0] - 1)
    return L[py, px], L, (t, b, x0, x1, s)

Lf, Limf, gf = lookup(f'{td}/front.png', V[:, 0])
Ls, _, _ = lookup(f'{td}/left.png', -V[:, 2])
x, y, z = V[:, 0], V[:, 1], V[:, 2]
# eye ellipses from blue blobs on the design front (bbox of blue, padded to include the dark rim)
t, b, x0, x1, s = gf; ys, xs = np.nonzero(Limf == B); eyes = np.zeros(len(V), bool)
ux = (x0 + x1) / 2 + (x - (x.min() + x.max()) / 2) * s; vy = t + (yhi - y) * s
for side in (xs < (x0 + x1) / 2, xs >= (x0 + x1) / 2):
    ex, ey = xs[side], ys[side]; cx, cy = (ex.min() + ex.max()) / 2, (ey.min() + ey.max()) / 2
    rx, ry = (ex.max() - ex.min()) / 2 + 10, (ey.max() - ey.min()) / 2 + 12
    eyes |= ((ux - cx) / rx) ** 2 + ((vy - cy) / ry) ** 2 < 1
front = (N[:, 2] > 0.2) & (z > 0.05)
lab = np.full(len(V), 2)
head = y > 0.115
lab[head] = 1
lab[head & front & (Lf == S) & (y < 0.385)] = 0
lab[head & front & eyes & (y < 0.385)] = 5
lab[head & (y > 0.70) & np.isin(Lf, [R, 5, 6]) & np.isin(Ls, [R, 5, 6])] = 6
lab[(y > 0.06) & (y <= 0.115) & front & (np.abs(x) < 0.05)] = 0           # neck V
lab[(y < -0.105) & (y > -0.245) & np.isin(Lf, [D, 5, 6])] = 3                           # obi
for wi in (9, 28):                                                           # mitten hands around wrist tails
    c = sk[wi, 3:] + 0.5 * (sk[wi, 3:] - sk[wi, :3]); lab[np.linalg.norm(V - c, axis=1) < 0.06] = 0
sl = V[np.abs(y + 0.7) < 0.01]; hem = -0.505
LC = [np.r_[sl[sl[:, 0] * g > 0][:, [0, 2]].min(0) + sl[sl[:, 0] * g > 0][:, [0, 2]].max(0)] / 2 for g in (-1, 1)]
legd = np.minimum.reduce([np.hypot(x - c[0], z - c[1]) for c in LC])
lab[(y < hem) & (y > -0.82)] = 0                                             # legs below the hem
lab[(y >= hem) & (y < -0.3) & (legd < 0.08)] = 0                             # leg cores inside the skirt (show when the hem lifts)
print('leg centres', np.round(LC, 3).tolist())
lab[(y <= -0.82)] = 4                                                        # boots
nb = m.vertex_neighbors
for it in range(5):
    new = lab.copy()
    for i in range(len(V)):
        c = np.bincount(lab[nb[i]], minlength=7); c[lab[i]] += 1; new[i] = c.argmax()
    lab = new
bowbox = (y > 0.80) & (np.abs(z - z[lab == 6].mean()) < 0.12)
for it in range(4):                                                          # grow bow over hair-labelled folds inside the bow
    g = (lab == 1) & bowbox & np.array([(lab[n] == 6).any() for n in nb]); lab[g] = 6
# geometry fixes
if BS != 1:
    bw = lab == 6; cb = V[bw].mean(0); cb[1] = V[bw][:, 1].min(); w = bw.astype(float)
    A = m.edges_sparse.astype(float); deg = np.asarray(A.sum(1)).ravel() + 1
    for it in range(4): w = (A @ w + w) / deg                    # soft falloff so the scaled bow stays attached and smooth
    w = np.maximum(w, bw * 1.0) * (y > 0.6)
    V += (BS - 1) * w[:, None] * (V - cb)
if BANG:  # pull the bang overhang back toward the forehead plane (front hair, y 0.36..0.62)
    fz = np.percentile(z[(lab == 0) & (y > 0.2) & (y < 0.36) & (np.abs(x) < 0.06)], 90)
    hb = (lab == 1) & (y > 0.32) & (y < 0.62) & (N[:, 2] > -0.2) & (z > 0)
    lim = fz + 0.25 * (y - 0.34); w = np.clip((0.62 - y) / 0.12, 0, 1)
    print('bang verts over limit', int((z[hb] > lim[hb]).sum()))
    V[hb, 2] = np.where(z[hb] > lim[hb], z[hb] - w[hb] * (z[hb] - lim[hb]), z[hb])
    print('bangs: face z', round(fz, 3), 'moved', int((hb & (z > lim)).sum()))
m.vertices = V
print({NAMES[k]: int((lab == k).sum()) for k in range(7)})
lin = PAL[lab] / 255.0; lin = np.where(lin <= 0.04045, lin / 12.92, ((lin + 0.055) / 1.055) ** 2.4)
col = np.concatenate([np.round(lin * 255), np.full((len(V), 1), 255)], 1).astype(np.uint8)
m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col); m.export(out); np.save(out.replace('.glb', '_ids.npy'), lab)
