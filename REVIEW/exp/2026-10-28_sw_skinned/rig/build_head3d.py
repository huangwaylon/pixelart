"""build_head3d.py (R, round 5): a real 3D head (no master-pixel projection). From the master-silhouette visual hull (head_hull.py)
it builds two solids in the rig H2 frame (front -Y, her left +X, z up):
  * SKULL = a fitted cranium ellipsoid  U  the hull's face/jaw region (hull voxels whose nearest hull surface is skin/eyes).
    Material: skin in the face zone, hair colour as scalp everywhere else, so gaps between hair clumps never show skin.
  * HAIR shell = hull minus skull (bob volume, crown, back hair, bun; bow lobes/knot/ribbons keep the bow colour)
    + a FULL FRINGE: a 3-4 cm layer in front of the forehead, from the hairline down to about the brow line, cut into even chunky anime
      clumps (tips alternate 1.705/1.725, notches up to 1.75) so the brows can peek through the gaps.
The head is moved FORWARD by HEAD_FWD over the neck (the owner said it was jutted back).
Writes rig/work/head3d.npz: skull (V, F, cls) + hair (V, F, cls) + params; rig/qa/head3d_views.png (silhouettes)."""
import os, sys, json, numpy as np
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from skimage import measure
H = os.path.dirname(os.path.abspath(__file__))
HEAD_FWD = float(os.environ.get('HEAD_FWD', '0.025'))
SIG = float(os.environ.get('SIG', '1.2'))  # surface smoothing (voxels)  # H2 units toward her front (-Y)
d = np.load(os.path.join(H, 'work', 'head_hull.npz'), allow_pickle=True)
keep = d['keep']; lo = d['lo']; VOX = float(d['vox']); HV = d['V']; HM = d['mat'].astype(str)
n = np.array(keep.shape); xs = [lo[i] + VOX * (np.arange(n[i]) + 0.5) for i in range(3)]
G = np.stack(np.meshgrid(*xs, indexing='ij'), -1)
# per-voxel class = class of the nearest hull surface vertex
kv = np.nonzero(keep); P = G[kv]; tr = cKDTree(HV); _, ii = tr.query(P); cls = np.full(keep.shape, '', dtype='<U5'); cls[kv] = HM[ii]
# ---------------- skull: cranium ellipsoid fitted inside the hair, plus the face/jaw region of the hull
C = np.array([0.0, 0.0, 1.665]); R = np.array([0.226, 0.200, 0.228])
ell = (((G - C) / R) ** 2).sum(-1) <= 1.0
# face, cheeks and jaw = the front of the head below the fringe tips, within the face width (the visual hull cannot tell a side-hair curtain
# from the cheeks: S says hair at |x| > .2, E says face at the front -> the face owns the front slab, the side bob starts behind the cheeks)
fz_ = G[..., 2]; fy_ = G[..., 1]; fx_ = G[..., 0]
# forehead profile: the hull front above the eyes is the master's bang overhang, not skin -> clip the face to a natural forehead that slopes
# back into the cranium (y_clip -0.228 up to the eyes, easing to the ellipsoid front at z 1.76)
FTOP = 1.772; ycl = np.where(fz_ < 1.62, -0.228, -0.228 + np.clip((fz_ - 1.62) / 0.14, 0, 1) * 0.055)
face = keep & (fz_ < FTOP) & (fy_ < 0.06) & (np.isin(cls, ['skin', 'eyes']) | (fy_ < -0.02)) & (np.abs(fx_) < 0.205) & (fy_ >= ycl)
curtain = keep & (np.abs(fx_) >= 0.190) & (fy_ < -0.02) & (fz_ < FTOP) & (fz_ > 1.36)  # r8c: side hair starts behind the cheek line (profile face reads)  # removed: hair in front of the cheek line
face = nd.binary_opening(face, iterations=1)
skull = (ell & keep) | face
skull = nd.binary_closing(skull, iterations=2) & (keep | ell)
# ---------------- hair shell
hair = keep & ~skull
# full fringe layer over the forehead: in front of the skull, |x| < 0.205, from the hairline down to the brow line, clumped tips
fx = G[..., 0]; fy = G[..., 1]; fz = G[..., 2]
# skull front surface y(x,z) (min y of skull voxels per x,z column)
sy = np.where(skull, fy, 9.0).min(1)  # (nx, nz)
syF = sy[:, None, :]
CW = 0.047  # clump width (H2 units) ~ 2.5 px
ph = (fx / CW) % 1.0; tri = np.abs(ph - 0.5) * 2  # 0 at clump centre, 1 at the notch
k = np.floor(fx / CW).astype(int); tipz = np.where(k % 2 == 0, 1.772, 1.786) + 0.026 * tri ** 2.2  # r5b (F: S fringe bottom = master row 46.5): tips 1.772/1.786, notches ~1.80 so the brows peek through
thick = 0.040 * np.clip((fz - tipz) / 0.05, 0.6, 1.0)  # thick, even clumps lying on the forehead (no visor), thinner toward the tips
front = (fy <= syF + 0.02) & (np.abs(fx) < 0.215) & (syF < 1.0)
fr = front & (fz >= tipz) & (fz <= 1.94) & (fy >= syF - thick)  # the fringe lies on the forehead (no visor out to the hull front)
visor = front & (fz > 1.60) & (fz < 1.95) & (fy < syF - thick)  # hull volume in front of the fringe layer (master bang overhang) -> removed
hair = keep & ~skull & ~curtain & ~visor & ~(front & (fz < tipz) & (fz > 1.60))
hair = hair | (fr & ~skull)
hair = nd.binary_closing(hair, iterations=1) & ~nd.binary_erosion(skull, iterations=1)
# r8d: profile balance (owner: "head looks jutted back"). Compress the back-of-head hair depth (incl. the bun overhang) toward the head:
# y' = Y0 + (y - Y0) * BACKK for y > Y0, resampled on the voxel grid. Front views keep their silhouette (x/z untouched); the fringe is in front.
Y0 = 0.06; BACKK = float(os.environ.get("BACKK", "0.62"))
yy = G[0, :, 0, 1]; src_y = np.where(yy > Y0, Y0 + (yy - Y0) / BACKK, yy)  # for each destination y, the source y
src_j = np.clip(np.round((src_y - lo[1]) / VOX - 0.5).astype(int), 0, n[1] - 1); inb = src_y <= lo[1] + VOX * n[1]
hair_c = hair[:, src_j, :] & inb[None, :, None]
hair = np.where((yy > Y0)[None, :, None], hair_c, hair) | (hair & (yy <= Y0)[None, :, None])
hair = hair & ~nd.binary_erosion(skull, iterations=1)
# drop tiny crumbs; keep components with > 200 voxels
lab, nl = nd.label(hair); sz = nd.sum(hair, lab, range(1, nl + 1)); hair = np.isin(lab, 1 + np.nonzero(sz > 200)[0])
# bow colour only inside the bow (back-top band + knot) and the ribbon tails (back, near the midline); stray bow-class voxels -> hair
bowzone = ((fy > 0.06) & (fz > 1.80)) | ((fy > 0.14) & (np.abs(fx) < 0.10))
hcls = np.full(cls.shape, 'hair', dtype='<U5')  # round 5: the bow is modelled separately (build_mesh.py lofts), the hull's bow voxels become hair volume
def mesh(vol, labels):
    v = nd.gaussian_filter(np.pad(vol, 3).astype(float), SIG)
    V, F, Nn, _ = measure.marching_cubes(v, 0.5, spacing=(VOX, VOX, VOX)); V = V + lo + VOX * 0.5 - 3 * VOX
    idx = np.clip(np.round((V - lo - VOX * 0.5) / VOX).astype(int), 0, n - 1)
    # label = nearest labelled voxel of the solid
    sel = np.nonzero(vol); Ps = G[sel]; t2 = cKDTree(Ps); _, j = t2.query(V); L = labels[sel][j]
    V[:, 1] -= HEAD_FWD
    return V, F[:, ::-1] if False else F, L
skl = np.where(face, 'skin', 'scalp')  # the whole face region is skin; cranium = scalp (hair colour)
SV, SF, SL = mesh(skull, skl)
HVv, HFf, HL = mesh(hair, hcls)
print('skull', len(SV), {c: int((SL == c).sum()) for c in ('skin', 'scalp')}, 'hair', len(HVv), {c: int((HL == c).sum()) for c in ('hair', 'bow')})
np.savez_compressed(os.path.join(H, 'work', 'head3d.npz'), SV=SV, SF=SF, SL=SL, HV=HVv, HF=HFf, HL=HL, head_fwd=HEAD_FWD, C=C - np.array([0, HEAD_FWD, 0]), R=R)
