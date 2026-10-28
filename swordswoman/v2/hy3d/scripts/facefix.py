# facefix.py IN.glb IN_ids.npy OUT.glb [raise=0.07]
# Lead round 2: bangs covered the eyes at 30 deg. Raise the bang line (front hair band -> forehead skin, pushed back onto the face plane),
# flatten the remaining bang overhang onto the forehead, and repaint larger eyes just below the new bang line.  glb: Y up, faces +Z.
import sys, numpy as np, trimesh
src, idp, out = sys.argv[1:4]; RAISE = float(sys.argv[4]) if len(sys.argv) > 4 else 0.07
m = trimesh.load(src, force='mesh'); V = np.asarray(m.vertices).copy(); N = m.vertex_normals; lab = np.load(idp)
PAL = np.array([[0xf8, 0xda, 0xc2], [0x3c, 0x32, 0x36], [0xc0, 0x3a, 0x3c], [0x44, 0x37, 0x4a], [0x2c, 0x20, 0x2c], [0x55, 0x80, 0xa2], [0xe8, 0x60, 0x4f]])
x, y, z = V.T
face = (lab == 0) & (y > 0.2) & (y < 0.37) & (np.abs(x) < 0.12)
fz = np.percentile(z[face], 80); bang0 = y[(lab == 1) & (z > 0.2) & (np.abs(x) < 0.06) & (y > 0.3)].min()
print('face plane z', round(fz, 3), 'bang line y', round(bang0, 3))
newb = bang0 + RAISE
fw = lambda yy: 0.215 - 0.25 * np.clip(yy - 0.40, 0, None)          # forehead half-width (shrinks up the head)
front = (N[:, 2] > 0.15) & (z > 0.12)
# 1) forehead: hair band between old and new bang line inside face width -> skin, pushed back onto a gently receding plane
zt = fz - 0.35 * (y - 0.34) - 0.5 * x ** 2
fh = (lab == 1) & (z > zt - 0.08) & (z > 0.12) & (y >= bang0 - 0.04) & (y < newb) & (np.abs(x) < fw(y))
lab[fh] = 0; V[fh, 2] = np.minimum(z[fh], zt[fh])
# 2) remaining bangs: cap the overhang so the hair front sits at most ~0.015 proud of the forehead, fading out by y=0.66
hb = (lab == 1) & (z > 0.12) & (y >= newb) & (y < 0.66) & (np.abs(x) < 0.30)
lim = zt + 0.015 + 0.25 * np.clip(y - newb, 0, None); w = np.clip((0.66 - y) / 0.14, 0, 1)
V[hb, 2] = np.where(z[hb] > lim[hb], z[hb] - w[hb] * (z[hb] - lim[hb]), z[hb])
# side locks beside the face stay (bob frame), but pull them back a touch so they do not hide the cheeks from SE/E
SL = float(sys.argv[5]) if len(sys.argv) > 5 else 0.10
sl = (lab == 1) & (z > 0.05) & (y > 0.05) & (y < newb + 0.05) & (np.abs(x) >= fw(y) - 0.02) & (np.abs(x) < 0.40)
ws = np.clip((newb + 0.05 - y) / 0.08, 0, 1) * np.clip((np.abs(x) - fw(y) + 0.02) / 0.05, 0, 1); zl = fz - SL
V[sl, 2] = np.where(z[sl] > zl, z[sl] - ws[sl] * (z[sl] - zl), z[sl])
# 3) eyes: two big ellipses just under the new bang line
lab[(lab == 5)] = 0
ey = newb - 0.085; skin = (lab == 0) & front & (y > 0.15) & (y < newb)
for sx in (-1, 1):
    e = skin & (((x - sx * 0.105) / 0.062) ** 2 + ((y - ey) / 0.078) ** 2 < 1); lab[e] = 5
print('eyes', int((lab == 5).sum()), 'eye centre y', round(ey, 3), 'forehead verts', int(fh.sum()), 'bang verts', int(hb.sum()))
# light Laplacian smoothing on moved hair/forehead to avoid creases
moved = fh | hb | sl; A = m.edges_sparse.astype(float); deg = np.asarray(A.sum(1)).ravel()
for it in range(3):
    S = (A @ V) / np.maximum(deg, 1)[:, None]; V[moved] = 0.5 * V[moved] + 0.5 * S[moved]
m.vertices = V
lin = PAL[lab] / 255.0; lin = np.where(lin <= 0.04045, lin / 12.92, ((lin + 0.055) / 1.055) ** 2.4)
col = np.concatenate([np.round(lin * 255), np.full((len(V), 1), 255)], 1).astype(np.uint8)
m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=col); m.export(out); np.save(out.replace('.glb', '_ids.npy'), lab)
print('wrote', out)
