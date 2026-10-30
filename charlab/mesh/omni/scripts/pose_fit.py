"""Fit an Omni 51-bone skeleton (normalised frame) to the proportions of a front reference silhouette.

Usage: venv/bin/python -I pose_fit.py POSE_IN.txt FRONT_MASK.png POSE_OUT.txt
1. vertical piecewise-linear remap: feet -> feet, hip joints -> crotch (+3% H), neck -> silhouette neck
   (narrowest row 22-50% from the top), head top -> top.
2. each arm chain (Arm, Elbow, Wrist, fingers) gets a 2D similarity (rotation about Z + scale, pivot = Arm joint)
   so the wrist lands on the reference wrist (hand blob centroid, moved 40% of the hand height toward the shoulder).
Depth (z) is kept. Joint names follow the demo order (bones 7-24 right arm, 26-43 left arm).
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

P = np.loadtxt(sys.argv[1]); m = np.asarray(Image.open(sys.argv[2]).convert('L')) > 127; out = sys.argv[3]
ys, xs = np.nonzero(m); top, bot = ys.min(), ys.max(); H = bot - top
cx = (xs.min() + xs.max()) / 2
Y = lambda r: 0.98 - 1.96 * (r - top) / H     # row -> normalised y
X = lambda c: 1.96 * (c - cx) / H              # col -> normalised x
w = m.sum(1)
lo, hi = int(top + 0.22 * H), int(top + 0.5 * H)
neck_r = lo + int(np.argmin(w[lo:hi]))
# crotch: first row below 45% where the centre column is background (between the legs)
c0 = int(round(cx)); crotch_r = None
for r in range(int(top + 0.45 * H), bot):
    if not m[r, c0 - 2:c0 + 3].any():
        crotch_r = r; break
if crotch_r is None:
    crotch_r = int(top + 0.7 * H)
# hands: components of the silhouette left/right of the body column band below the neck
rr = m[max(neck_r + 1, crotch_r - int(0.06 * H))]
l_ = c0
while l_ > 0 and rr[l_ - 1]: l_ -= 1
r_ = c0
while r_ < len(rr) - 1 and rr[r_ + 1]: r_ += 1
body_half = 0.5 * (r_ - l_)
targets = {}
for side, sgn in (('R', -1), ('L', 1)):   # her right = image left (front view) = -x
    sel = np.zeros_like(m)
    if sgn < 0:
        sel[neck_r:, :int(cx - body_half * 0.95)] = True
    else:
        sel[neck_r:, int(cx + body_half * 0.95):] = True
    arm = m & sel
    lab, n = ndimage.label(arm)
    if n == 0:
        continue
    k = 1 + int(np.argmax(ndimage.sum(arm, lab, range(1, n + 1))))
    ay, ax = np.nonzero(lab == k)
    low = ay > ay.max() - 0.07 * H
    hy, hx = ay[low].mean(), ax[low].mean()
    targets[side] = (X(hx), Y(hy - 0.03 * H))

# current skeleton landmarks (demo indices)
J = {}
def joint(i): return P[i, :3]
head_top = P[:, 4].max()
feet = P[:, 4].min()
hip_y = 0.5 * (P[45, 1] + P[48, 1]); neck_y = P[2, 1]
src = np.array([min(feet, -0.98), hip_y, neck_y, max(head_top, 0.98)])
dst = np.array([src[0], Y(crotch_r) + 0.03 * 1.96, Y(neck_r), src[3]])
def ymap(y): return np.interp(y, src, dst)
Q = P.copy()
Q[:, 1] = ymap(P[:, 1]); Q[:, 4] = ymap(P[:, 4])
arms = {'R': list(range(7, 25)), 'L': list(range(26, 44))}
for side, rows in arms.items():
    if side not in targets:
        continue
    piv = Q[rows[0], :2].copy()               # Arm joint (start of bone 7 / 26)
    wrist = Q[rows[2], :2].copy()             # Wrist joint = start of bone 9 / 28
    tgt = np.array(targets[side])
    a = wrist - piv; b = tgt - piv
    s = np.linalg.norm(b) / np.linalg.norm(a)
    ang = np.arctan2(b[1], b[0]) - np.arctan2(a[1], a[0])
    Rm = s * np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    for r in rows:
        for k in (0, 3):
            if r == rows[0] and k == 0:
                continue
            Q[r, k:k + 2] = piv + Rm @ (Q[r, k:k + 2] - piv)
np.savetxt(out, Q)
print('fit neck y %.3f->%.3f hip y %.3f->%.3f wrists %s' % (neck_y, dst[2], hip_y, dst[1],
      {k: tuple(round(float(x), 3) for x in v) for k, v in targets.items()}))
