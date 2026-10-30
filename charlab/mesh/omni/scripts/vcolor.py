"""Vertex colour from reference projection (texture fallback: Hunyuan Paint weights are not installed).

Usage: venv/bin/python -I vcolor.py IN.glb OUT.glb VIEW=IMG.png [VIEW=IMG.png ...]
VIEW in front|back|left|right|q34 (azimuth 0/180/90/-90/45 deg; left = camera on her left, +X).
glb frame: Y up, faces +Z. Each view: orthographic projection, figure height in the image = mesh height,
horizontal centre = silhouette centre. A vertex takes the colour of the view that sees it most frontally (z-buffer
visibility from dense surface samples); unseen vertices get the colour of the nearest seen vertex.
Outlines (dark line pixels) are skipped by eroding 4 px into the matte and by rejecting the darkest pixels in a
5x5 neighbourhood. sRGB -> linear for glTF COLOR_0.
"""
import sys
import numpy as np, trimesh
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

src, out = sys.argv[1:3]
views = [v.split('=', 1) for v in sys.argv[3:]]
AZ = {'front': 0, 'back': 180, 'left': 90, 'right': -90, 'q34': 45}
m = trimesh.load(src, force='mesh')
V = m.vertices; N = m.vertex_normals
ylo, yhi = V[:, 1].min(), V[:, 1].max()
S, fi = trimesh.sample.sample_surface(m, 1500000)
OUTLINE = np.array([43, 34, 53.])
best = np.full(len(V), -1.0); col = np.zeros((len(V), 3))
for name, path in views:
    az = np.radians(AZ[name])
    d = np.array([np.sin(az), 0, np.cos(az)])  # direction from object to camera
    right = np.array([np.cos(az), 0, -np.sin(az)])
    im = Image.open(path)
    arr = np.asarray(im.convert('RGBA')).astype(float)
    if arr[..., 3].min() > 250:  # white background
        fg = (255 - arr[..., :3]).max(2) > 22
    else:
        fg = arr[..., 3] > 127
    rgb = arr[..., :3]
    line = np.linalg.norm(rgb - OUTLINE, axis=2) < 70
    line &= ~ndimage.binary_opening(line, iterations=10)  # big dark areas (black hair) are paint, not line
    clean = ndimage.binary_erosion(fg, iterations=10) & ~ndimage.binary_dilation(line, iterations=2)
    # fill line pixels from neighbours: nearest clean pixel
    idx = ndimage.distance_transform_edt(~clean, return_distances=False, return_indices=True)
    rgbf = rgb[idx[0], idx[1]]
    ys, xs = np.nonzero(fg); t, b = ys.min(), ys.max(); xc = (xs.min() + xs.max()) / 2
    s = (b - t) / (yhi - ylo)
    u = V @ right; uS = S @ right
    uc = (uS.min() + uS.max()) / 2
    def to_px(uu, yy):
        return np.round(xc + (uu - uc) * s).astype(int), np.round(t + (yhi - yy) * s).astype(int)
    # z-buffer from samples (in image pixel grid)
    px, py = to_px(uS, S[:, 1]); depth = S @ d
    H, W = fg.shape
    ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
    zb = np.full((H, W), -np.inf)
    np.maximum.at(zb, (py[ok], px[ok]), depth[ok])
    zb = ndimage.maximum_filter(zb, 3)
    vx, vy = to_px(u, V[:, 1]); vz = V @ d
    inb = (vx >= 0) & (vx < W) & (vy >= 0) & (vy < H)
    vis = np.zeros(len(V), bool)
    vis[inb] = vz[inb] >= zb[vy[inb], vx[inb]] - 0.012 * (yhi - ylo)
    score = N @ d
    take = vis & (score > 0.3) & (score > best)
    take[inb] &= fg[vy[inb], vx[inb]]
    col[take] = rgbf[vy[take], vx[take]]
    best[take] = score[take]
seen = best > -1
print('seen frac %.3f' % seen.mean())
if (~seen).any():
    _, j = cKDTree(V[seen]).query(V[~seen])
    col[~seen] = col[seen][j]
lin = col / 255.0; lin = np.where(lin <= 0.04045, lin / 12.92, ((lin + 0.055) / 1.055) ** 2.4)
c8 = np.concatenate([np.round(lin * 255), np.full((len(V), 1), 255)], 1).astype(np.uint8)
m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=c8)
m.export(out); print('vcolor', out)
