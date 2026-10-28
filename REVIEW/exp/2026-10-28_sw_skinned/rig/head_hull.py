"""head_hull.py (R, round 2): visual-hull head from the m96 master head stamps (S, SE, E, NE, N + mirrored SW, W, NW), in the H2 frame
(units: figure 2.0 tall, front -Y, her left +X, z up).  Game camera: 30 deg elevation ortho, 52.608 px per unit at 1x, 192 cell pivot
(96,152) -> master 128 cell = 192 cell - 32 + per-view alignment (rig/align.json, the feet alignment used by the pixel chain).
Writes rig/work/head_hull.npz (verts, faces, per-vertex material class) + rig/qa/head_hull_reproj.png (hull silhouette vs master mask).
usage: pixtools python -I head_hull.py [voxel=0.006] [dil=1]"""
import sys, os, json, numpy as np
from scipy import ndimage as nd
from skimage import measure
from PIL import Image
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx  # noqa: E402
H = os.path.dirname(os.path.abspath(__file__))
VOX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.006; DIL = int(sys.argv[2]) if len(sys.argv) > 2 else 1; SOFT = int(sys.argv[3]) if len(sys.argv) > 3 else 1
AL = json.load(open(os.path.join(H, 'align.json')))
for k_, v_ in json.loads(os.environ.get('YAWS', '{}')).items(): AL[k_]['yaw'] = v_
PPU = 52.608
ANC = json.load(open(hx.SW + 'v2/m96/heads/anchor.json'))['views']
AZC = {'SE': (1, 1), 'E': (1, 0), 'S': (0, 1), 'NE': (1, -1), 'N': (0, -1)}  # contract-frame camera azimuth (render_motion.AZ)


def cam(view, yaw):
    """returns (proj(P)->(col,row) in the master 128 cell, view dir toward camera d, H2 frame) for the rig turned by yaw (deg)"""
    ax, ay = AZC[view]; c = np.array([-ax, -ay, 0.0]); c /= np.linalg.norm(c)  # H2 frame = contract rotated 180 about Z
    el = np.radians(30); loc = np.array([c[0] * np.cos(el), c[1] * np.cos(el), np.sin(el)])
    f = -loc / np.linalg.norm(loc); r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    ps = np.radians(yaw); Rz = np.array([[np.cos(ps), -np.sin(ps), 0], [np.sin(ps), np.cos(ps), 0], [0, 0, 1]])
    a = AL[view]
    def proj(P):
        Q = P @ Rz.T
        return np.stack([96 + PPU * (Q @ r) - 32 + a.get('reg_dx', a['dx']), 152 - PPU * (Q @ u) - 32 + a.get('reg_dy', a['dy'])], -1)
    return proj, Rz.T @ (-f)  # direction toward the camera in the model frame


def views():
    """(name, mask, chars, proj, dir) for real + mirrored views"""
    out = []
    for v in ('S', 'SE', 'E', 'NE', 'N'):
        t, x0, y0 = hx.stamp_of(v); g = np.full((128, 128), '.', dtype='<U1'); g = hx.paste(g, t, x0, y0)
        M = hx.read_grid(hx.SW + f'v2/m96/masters/EC0_{v}_96.txt')
        yaw = AL[v].get('yaw', 0.0); proj, d = cam(v, yaw)
        m = g != '.'
        # round 4: the stamps include the red kimono collar under the chin -> it became hull geometry that moved with the head and drew
        # red over the chin. Drop dress-red pixels in the stamp's lower part (below the mouth / the lowest 5 rows) from the head mask.
        red = np.isin(g, list('ReE')); an = ANC.get(v, {}); ycut = (an['mouth'][1] + 3) if an.get('mouth') else (t.shape[0] + y0 - 5)
        lowrows = np.arange(128)[:, None] >= ycut
        m = m & ~(red & lowrows)
        out.append((v, m, M, proj, d))
        if v in ('SE', 'E', 'NE'):  # mirrored view of her other side: mirror the model (x -> -x) and reuse the same image
            def projm(P, proj=proj): return proj(P * np.array([-1, 1, 1.0]))
            out.append((v + '_m', m, M, projm, d * np.array([-1, 1, 1.0])))
    return out


def main():
    V = views()
    lo = np.array([-0.40, -0.40, 1.30 + 0.044]); hi = np.array([0.40, 0.45, 2.15])
    n = np.ceil((hi - lo) / VOX).astype(int); print('grid', n, n.prod())
    xs = [lo[i] + VOX * (np.arange(n[i]) + 0.5) for i in range(3)]
    keep = np.ones(n, bool)
    # soft carve: inside the DIL-dilated mask in all but SOFT views, and inside the (DIL+2)-dilated mask in every view (masters disagree by 1-3 px)
    MD = [(nd.binary_dilation(m, iterations=DIL) if DIL else m, nd.binary_dilation(m, iterations=DIL + 2)) for _, m, _, _, _ in V]
    X, Y = np.meshgrid(xs[0], xs[1], indexing='ij')
    for k, z in enumerate(xs[2]):
        P = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z)], 1); kk = np.ones(len(P), bool); cnt = np.zeros(len(P), int)
        for (name, m, _, proj, _), (md, mw) in zip(V, MD):
            cr = proj(P); c = np.floor(cr[:, 0]).astype(int); r = np.floor(cr[:, 1]).astype(int)
            ok = (c >= 0) & (c < 128) & (r >= 0) & (r < 128); rc, cc_ = np.clip(r, 0, 127), np.clip(c, 0, 127)
            kk &= ok & mw[rc, cc_]; cnt += ok & md[rc, cc_]
        strict = kk & (cnt >= len(V) - SOFT)
        # bow / bun / ribbon zone (back of the head): the masters disagree most there -> allow 2 dissenting views
        zone = (P[:, 1] > 0.06) & (P[:, 2] > 1.86 + 0.044)
        keep[:, :, k] = (strict | (zone & kk & (cnt >= len(V) - SOFT - 2))).reshape(X.shape)
    # round 4: E-profile nose bump. Triangulate the nose tip from the S nose pixels and the E profile bump (anchor.json nose), add a small
    # ellipsoid of voxels there (the strict carve shaved it: the other views don't resolve a 1-2 px bump)
    def aff(v):
        proj, _ = cam(v, AL[v].get('yaw', 0.0)); c0 = proj(np.zeros((1, 3)))[0]; return np.stack([proj(np.eye(3)[i][None])[0] - c0 for i in range(3)], 1), c0
    (Ms, cs), (Me, ce) = aff('S'), aff('E')
    ns = np.array([[x + 0.5, y + 0.5] for x, y, _ in ANC['S']['nose']]).mean(0); ne = np.array([79.0, 55.0])  # E bump: K outline col 79, rows 54-55
    A_ = np.vstack([Ms, Me]); b_ = np.concatenate([ns - cs, ne - ce]); NT = np.linalg.lstsq(A_, b_, rcond=None)[0]
    G_ = np.stack(np.meshgrid(*xs, indexing='ij'), -1)
    col = keep & (np.abs(G_[..., 0]) < 0.02) & (np.abs(G_[..., 2] - NT[2]) < 0.012)
    yf = float(G_[..., 1][col].min()) if col.any() else NT[1]; NT = np.array([0.0, min(NT[1], yf - 0.006), NT[2]])  # midline, just proud of the face
    dd = (G_ - NT) / np.array([0.014, 0.016, 0.016])
    nose = (dd ** 2).sum(-1) < 1.0; print('nose tip', NT.round(4), 'voxels', int(nose.sum()))
    keep = keep | nose
    lab, nl = nd.label(keep); sz = nd.sum(keep, lab, range(1, nl + 1)); keep = lab == 1 + int(np.argmax(sz))
    print('voxels', int(keep.sum()), 'components', nl)
    KV = np.stack(np.nonzero(keep), 1) * VOX + lo + VOX * 0.5
    vol = nd.gaussian_filter(np.pad(keep, 2).astype(float), 1.0)  # pad: closed surface at the grid bounds
    verts, faces, normals, _ = measure.marching_cubes(vol, 0.5, spacing=(VOX, VOX, VOX))
    verts = verts + lo + VOX * 0.5 - 2 * VOX
    # orient normals outward (marching cubes on a smoothed occupancy gives gradient-toward-inside normals)
    cen = verts.mean(0); out_ = ((verts - cen) * normals).sum(1).mean()
    if out_ < 0: normals = -normals; faces = faces[:, ::-1]
    # reprojection IoU + per-vertex classification by visible master chars
    CL = {**{c: 'hair' for c in 'hHgL'}, **{c: 'skin' for c in 'sSmk'}, **{c: 'bow' for c in 'ReE'}, 'W': 'eyes', 'K': 'K', '.': '.'}
    votes = {c: np.zeros(len(verts)) for c in ('hair', 'skin', 'bow', 'eyes')}
    tiles = []; rep = {}
    for name, m, M, proj, d in V:
        cr = proj(verts); c = np.floor(cr[:, 0]).astype(int); r = np.floor(cr[:, 1]).astype(int)
        sil = np.zeros((128, 128), bool); cv = proj(KV); sil[np.clip(np.floor(cv[:, 1]).astype(int), 0, 127), np.clip(np.floor(cv[:, 0]).astype(int), 0, 127)] = True
        iou = (sil & m).sum() / (sil | m).sum(); rep[name] = [round(float(iou), 3), int((sil & ~m).sum()), int((m & ~sil).sum())]  # IoU, extra px, missing px
        # visibility: depth buffer of verts at 4x
        dep = verts @ d  # larger = closer to camera
        S4 = 4; cc = np.floor(cr * S4).astype(int); key = np.clip(cc[:, 1], 0, 511) * 512 + np.clip(cc[:, 0], 0, 511)
        zb = np.full(512 * 512, -9.0); np.maximum.at(zb, key, dep)
        zb2 = nd.grey_dilation(zb.reshape(512, 512), size=(3, 3)).ravel()
        vis = (dep >= zb2[key] - 0.02) & ((normals @ d) > 0.15)
        ch = M[np.clip(r, 0, 127), np.clip(c, 0, 127)]
        w = (normals @ d).clip(0, 1) * vis * (1.0 if not name.endswith('_m') else 0.7)
        for k_, cl in CL.items():
            if cl in votes: votes[cl] += w * (ch == k_)
        im = np.zeros((128, 128, 3), np.uint8); im[m] = (90, 90, 90); im[sil & m] = (230, 230, 230); im[sil & ~m] = (230, 60, 60); im[m & ~sil] = (60, 120, 230)
        tiles.append(Image.fromarray(im[10:70, 30:100]).resize((280, 240), Image.NEAREST))
    print('reproj IoU', rep)
    Vt = np.stack([votes[c] for c in ('hair', 'skin', 'bow', 'eyes')], 1); vote = np.array(['hair', 'skin', 'bow', 'eyes'])[Vt.argmax(1)]
    vote[Vt.sum(1) < 1e-6] = 'hair'
    # unseen / K-only vertices: nearest-neighbour fill from voted ones
    from scipy.spatial import cKDTree
    seen = Vt.sum(1) > 0.05; t_ = cKDTree(verts[seen]); _, ii = t_.query(verts[~seen]); vote[~seen] = vote[seen][ii]
    np.savez_compressed(os.path.join(H, 'work', 'head_hull.npz'), V=verts, F=faces, N=normals, mat=vote, reproj=json.dumps(rep), vox=VOX, dil=DIL)
    W = Image.new('RGB', (280 * len(tiles), 240))
    for i, t in enumerate(tiles): W.paste(t, (280 * i, 0))
    W.save(os.path.join(H, 'qa', 'head_hull_reproj.png')); print('mats', {c: int((vote == c).sum()) for c in ('hair', 'skin', 'bow', 'eyes')}, len(verts), len(faces))


if __name__ == '__main__':
    main()
