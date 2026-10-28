# vcolor.py IN.glb OUT.glb TURN_DIR  : project design turnaround (front/back/left/right.png, white bg) onto a REST mesh as vertex colours.
# glb frame: Y up, character faces +Z, her left = +X. Orthographic, uniform scale from height; view picked by normal.
import sys, numpy as np, trimesh
from PIL import Image
src, out, td = sys.argv[1:4]
m = trimesh.load(src, force='mesh'); V = m.vertices; N = m.vertex_normals
views = {'front': (np.array([0, 0, 1.]), lambda p: p[:, 0]), 'back': (np.array([0, 0, -1.]), lambda p: -p[:, 0]),
         'left': (np.array([1., 0, 0]), lambda p: -p[:, 2]), 'right': (np.array([-1., 0, 0]), lambda p: p[:, 2])}
ylo, yhi = V[:, 1].min(), V[:, 1].max()
score = np.stack([N @ d for d, _ in views.values()], 1); pick = score.argmax(1)
col = np.zeros((len(V), 4), np.uint8); col[:, 3] = 255
for k, (name, (d, ufn)) in enumerate(views.items()):
    im = np.asarray(Image.open(f'{td}/{name}.png').convert('RGB')).astype(int)
    fg = (np.abs(im - 255).sum(2) > 40); ys, xs = np.nonzero(fg)
    t, b = ys.min(), ys.max(); s = (b - t) / (yhi - ylo)
    u = ufn(V); uc = (u.min() + u.max()) / 2; xc = (xs.min() + xs.max()) / 2
    px = np.clip(np.round(xc + (u - uc) * s).astype(int), 0, im.shape[1] - 1)
    py = np.clip(np.round(t + (yhi - V[:, 1]) * s).astype(int), 0, im.shape[0] - 1)
    sel = pick == k; c = im[py[sel], px[sel]]
    white = (c.sum(1) > 720)  # fell on background: mark grey
    c[white] = 140; col[sel, :3] = c
lin = col[:, :3] / 255.0; lin = np.where(lin <= 0.04045, lin / 12.92, ((lin + 0.055) / 1.055) ** 2.4); col[:, :3] = np.round(lin * 255)
m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col); m.export(out); print('vcolor', out)
