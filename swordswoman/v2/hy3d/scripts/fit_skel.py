# fit_skel.py MESH.glb SKEL.txt OUT.txt OVERLAY_PREFIX(render prefix with _front/_side) legx armsx armsy dz
# Adjust Omni rest skeleton to another rest mesh; draws overlay on front + side renders for checking.
import sys, numpy as np, trimesh
from PIL import Image, ImageDraw
mesh, sk, out, pre = sys.argv[1:5]; legx, ax, ay, dz = map(float, sys.argv[5:9])
P = np.loadtxt(sk); V = trimesh.load(mesh).to_geometry().vertices
Q = P.copy(); Q[:, 2] += dz; Q[:, 5] += dz
legs = list(range(45, 51)); arms = list(range(7, 25)) + list(range(26, 44))
for i in legs:
    for s in (0, 3): Q[i, s] = np.sign(Q[i, s]) * (abs(Q[i, s]) - 0.08 + legx) if abs(Q[i, s]) > 0.01 else Q[i, s]
for i in arms:  # scale arm chain about shoulder end (Arm head)
    side = 7 if i < 26 else 26; piv = Q[side, :3].copy()
    for s in (0, 3):
        d = Q[i, s:s+3] - piv; Q[i, s:s+3] = piv + d * np.array([ax, ay, 1.0])
np.savetxt(out, Q)
lo, hi = V.min(0), V.max(0); H = hi[1] - lo[1]; c = (lo + hi) / 2; k = 2.0 / H * 512 / 2.5
def to_px(p, view):
    if view == 'front': u = (p[0] - c[0]) * k + 256
    else: u = -(p[2] - c[2]) * k + 256  # side cam at +X: screen right = -Z_glb (back)
    v = 512 - ((p[1] - lo[1]) * k + (512 - 2.0 * 512 / 2.5) / 2 + 0.0)
    return u, v
for view in ('front', 'side'):
    im = Image.open(f'{pre}_{view}.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); d = ImageDraw.Draw(bg)
    for i in range(len(Q)):
        a, b = to_px(Q[i, :3], view), to_px(Q[i, 3:], view); d.line([a, b], fill=(255, 0, 0) if Q[i, 0] < -0.01 else (0, 0, 255), width=3)
    bg.save(f'/tmp/hy_fit_{view}.png')
print('ok')
