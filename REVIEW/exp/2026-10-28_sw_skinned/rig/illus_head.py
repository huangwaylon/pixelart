"""illus_head.py (R, round 7): illustration-textured 3D head, step 1 (pixtools, -I).
* Fits, per view (S SE E NE N), the 2D map from the hi-res Gemini illustration (v2/hair/turnE_final, pzlib.SRC mapping) to the m96 master
  cell (the masters were E2-pixelized from these): x_m = ax * X + bx, y_m = ay * Y + by, initialised from the figure bboxes and refined by
  maximising the silhouette IoU of the area-downsampled illustration mask vs the master mask. Composed with the rig's master registration
  (rig/align.json reg_dx/reg_dy/yaw), this IS the projection camera of each illustration.
* Builds a hi-res visual hull of the HEAD from the illustration head silhouettes (illustration mask inside the master head-stamp ROI,
  collar excluded), carved at 4x master resolution (voxel 0.004 H2 units), views S SE E NE N + mirrored SE/E/NE; reports per-view IoU at 4x.
* Classifies hull vertices hair / skin / bow from the visible illustration colours.
Writes rig/illus_map.json, rig/work/head_illus.npz, rig/tex_illus/<V>.png (illustration with the background filled by the nearest figure
colour, SW/W/NW = flipped SE/E/NE) and rig/qa/illus_hull_reproj.png."""
import os, sys, json, numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial import cKDTree
from skimage import measure
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx  # noqa: E402
H = os.path.dirname(os.path.abspath(__file__)); SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/'
SRC = {'S': 'iso_S.png', 'SE': 'iso_SE_fixed.png', 'E': 'iso_E.png', 'NE': 'iso_NE.png', 'N': 'iso_N.png'}
AL = json.load(open(os.path.join(H, 'align.json')))
for k_, v_ in json.loads(os.environ.get('YAWS', '{}')).items(): AL[k_]['yaw'] = v_
ANC = json.load(open(SW + 'm96/heads/anchor.json'))['views']
PPU = 52.608; SUP = 4  # carve masks at 4x master resolution
VOX = float(os.environ.get('IVOX', '0.004')); ISOFT = int(os.environ.get('ISOFT', '0'))
AZC = {'SE': (1, 1), 'E': (1, 0), 'S': (0, 1), 'NE': (1, -1), 'N': (0, -1)}


def fg_mask(a):
    return (255 * 3 - a[..., :3].astype(int).sum(-1)) > 40


def fit_map(v):
    a = np.asarray(Image.open(SW + 'hair/turnE_final/' + SRC[v]).convert('RGB')); m = fg_mask(a)
    M = hx.read_grid(SW + f'v2/m96/masters/EC0_{v}_96.txt'.replace('v2/v2/', 'v2/')) if False else hx.read_grid(SW + f'm96/masters/EC0_{v}_96.txt')
    mm = M != '.'; js = json.load(open(SW + f'm96/masters/EC0_{v}_96.json'))
    ys, xs = np.nonzero(m); bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    ax0 = js['w'] / (bx1 - bx0); ay0 = js['h'] / (by1 - by0); bxa = js['ox'] - bx0 * ax0; bya = js['oy'] - by0 * ay0
    def iou(ax, ay, bx, by):
        # forward-map illustration fg pixel centres into the master grid (count coverage per cell)
        cx = np.floor(ax * (xs + 0.5) + bx).astype(int); cy = np.floor(ay * (ys + 0.5) + by).astype(int)
        ok = (cx >= 0) & (cx < 128) & (cy >= 0) & (cy < 128); cnt = np.zeros((128, 128)); np.add.at(cnt, (cy[ok], cx[ok]), 1)
        cov = cnt * ax * ay > 0.5; return (cov & mm).sum() / (cov | mm).sum()
    best = (iou(ax0, ay0, bxa, bya), ax0, ay0, bxa, bya)
    for it in range(3):
        _, ax, ay, bx, by = best
        for dax in (-0.01, 0, 0.01):
            for day in (-0.01, 0, 0.01):
                for dbx in (-0.5, -0.25, 0, 0.25, 0.5):
                    for dby in (-0.5, -0.25, 0, 0.25, 0.5):
                        c = (ax * (1 + dax), ay * (1 + day), bx + dbx, by + dby); s = iou(*c)
                        if s > best[0]: best = (s,) + c
    print(v, 'illus->master map IoU', round(best[0], 3), 'scale', round(best[1], 5), round(best[2], 5)); return a, m, best


def cam(view, yaw):
    ax, ay = AZC[view]; c = np.array([-ax, -ay, 0.0]); c /= np.linalg.norm(c); el = np.radians(30)
    loc = np.array([c[0] * np.cos(el), c[1] * np.cos(el), np.sin(el)]); f = -loc / np.linalg.norm(loc)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    ps = np.radians(yaw); Rz = np.array([[np.cos(ps), -np.sin(ps), 0], [np.sin(ps), np.cos(ps), 0], [0, 0, 1]]); a = AL[view]
    def proj(P):  # -> master cell coords (registration)
        Q = P @ Rz.T; return np.stack([96 + PPU * (Q @ r) - 32 + a.get('reg_dx', a['dx']), 152 - PPU * (Q @ u) - 32 + a.get('reg_dy', a['dy'])], -1)
    return proj, Rz.T @ (-f)


def main():
    MAP = {}; V = []
    os.makedirs(os.path.join(H, 'tex_illus'), exist_ok=True)
    for v in ('S', 'SE', 'E', 'NE', 'N'):
        a, m, (s, ax, ay, bx, by) = fit_map(v); MAP[v] = {'ax': ax, 'ay': ay, 'bx': bx, 'by': by, 'iou_1x': round(float(s), 4), 'size': [a.shape[1], a.shape[0]], 'src': SRC[v]}
        # head ROI from the master head stamp (collar removed), dilated 1 master px, at 4x
        t, x0, y0 = hx.stamp_of(v); g = np.full((128, 128), '.', dtype='<U1'); g = hx.paste(g, t, x0, y0)
        an = ANC.get(v, {}); ycut = (an['mouth'][1] + 3) if an.get('mouth') else (t.shape[0] + y0 - 5)
        roi = (g != '.') & ~(np.isin(g, list('ReE')) & (np.arange(128)[:, None] >= ycut))
        roi4 = nd.binary_dilation(np.kron(roi, np.ones((SUP, SUP), bool)), iterations=SUP)
        # illustration mask resampled into the 4x master grid (nearest by inverse map)
        yy, xx = np.mgrid[0:128 * SUP, 0:128 * SUP]; Xi = ((xx + 0.5) / SUP - bx) / ax; Yi = ((yy + 0.5) / SUP - by) / ay
        inb = (Xi >= 0) & (Xi < a.shape[1]) & (Yi >= 0) & (Yi < a.shape[0])
        mi = np.zeros_like(inb); mi[inb] = m[Yi[inb].astype(int), Xi[inb].astype(int)]
        hm = mi & roi4
        img4 = np.zeros((128 * SUP, 128 * SUP, 3), np.uint8); img4[inb] = a[Yi[inb].astype(int), Xi[inb].astype(int)]
        proj, d = cam(v, AL[v].get('yaw', 0.0))
        V.append((v, hm, img4, proj, d))
        if v in ('SE', 'E', 'NE'):
            def pm(P, proj=proj): return proj(P * np.array([-1, 1, 1.0]))
            V.append((v + '_m', hm, img4, pm, d * np.array([-1, 1, 1.0])))
        # texture: illustration with the background filled by the nearest figure colour
        solid = nd.binary_erosion(m, iterations=3)  # drop the anti-aliased white halo: fill only from solid interior colours
        _, (iy, ix) = nd.distance_transform_edt(~solid, return_indices=True); tex = a[iy, ix]
        Image.fromarray(tex).save(os.path.join(H, 'tex_illus', f'{v}.png'))
        if v in ('SE', 'E', 'NE'): Image.fromarray(tex[:, ::-1]).save(os.path.join(H, 'tex_illus', {'SE': 'SW', 'E': 'W', 'NE': 'NW'}[v] + '.png'))
    json.dump({'_doc': 'R round 7: illustration -> master-cell map per view: x_m = ax*X + bx, y_m = ay*Y + by (X, Y illustration px). Mirrored views SW/W/NW use the flipped SE/E/NE illustration: X_flip = size_x - 1 - X.', **MAP},
              open(os.path.join(H, 'illus_map.json'), 'w'), indent=1)
    # ---------------- hi-res carve
    lo = np.array([-0.40, -0.42, 1.30 + 0.044]); hi = np.array([0.40, 0.45, 2.16]); n = np.ceil((hi - lo) / VOX).astype(int)
    xs = [lo[i] + VOX * (np.arange(n[i]) + 0.5) for i in range(3)]; keep = np.zeros(n, bool)
    X, Y = np.meshgrid(xs[0], xs[1], indexing='ij')
    MD = [(m_, nd.binary_dilation(m_, iterations=2 * SUP)) for _, m_, _, _, _ in V]
    for k, z in enumerate(xs[2]):
        P = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z)], 1); kk = np.ones(len(P), bool); cnt = np.zeros(len(P), int)
        for (name, m_, _, proj, _), (md, mw) in zip(V, MD):
            cr = proj(P) * SUP; c = np.floor(cr[:, 0]).astype(int); r = np.floor(cr[:, 1]).astype(int)
            ok = (c >= 0) & (c < 128 * SUP) & (r >= 0) & (r < 128 * SUP); rc, cc_ = np.clip(r, 0, 128 * SUP - 1), np.clip(c, 0, 128 * SUP - 1)
            kk &= ok & mw[rc, cc_]; cnt += ok & md[rc, cc_]
        zone = (P[:, 1] > 0.06) & (P[:, 2] > 1.86 + 0.044)
        keep[:, :, k] = (kk & ((cnt >= len(V) - ISOFT) | (zone & (cnt >= len(V) - 2)))).reshape(X.shape)
    lab, nl = nd.label(keep); sz = nd.sum(keep, lab, range(1, nl + 1)); keep = lab == 1 + int(np.argmax(sz))
    vol = nd.gaussian_filter(np.pad(keep, 3).astype(float), 1.3)
    verts, faces, normals, _ = measure.marching_cubes(vol, 0.5, spacing=(VOX, VOX, VOX)); verts = verts + lo + VOX * 0.5 - 3 * VOX
    cen = verts.mean(0)
    if ((verts - cen) * normals).sum(1).mean() < 0: normals = -normals
    KV = np.stack(np.nonzero(keep), 1) * VOX + lo + VOX * 0.5
    rep, votes, tiles = {}, {c: np.zeros(len(verts)) for c in ('hair', 'skin', 'bow')}, []
    for name, m_, img4, proj, d in V:
        cv = proj(KV) * SUP; sil = np.zeros_like(m_); sil[np.clip(np.floor(cv[:, 1]).astype(int), 0, 128 * SUP - 1), np.clip(np.floor(cv[:, 0]).astype(int), 0, 128 * SUP - 1)] = True
        sil = nd.binary_closing(sil, iterations=1); rep[name] = round(float((sil & m_).sum() / (sil | m_).sum()), 3)
        cr = proj(verts) * SUP; dep = verts @ d; cc = np.floor(cr).astype(int); key = np.clip(cc[:, 1], 0, 511) * 512 + np.clip(cc[:, 0], 0, 511)
        zb = np.full(512 * 512, -9.0); np.maximum.at(zb, key, dep); zb2 = nd.grey_dilation(zb.reshape(512, 512), size=(5, 5)).ravel()
        vis = (dep >= zb2[key] - 0.015) & ((normals @ d) > 0.15)
        col = img4[np.clip(cc[:, 1], 0, 511), np.clip(cc[:, 0], 0, 511)].astype(int); r_, g_, b_ = col[:, 0], col[:, 1], col[:, 2]
        bow = (r_ > 110) & (g_ < 0.5 * r_) & (b_ < 0.55 * r_); skin = ~bow & (r_ > 150) & (g_ > 0.52 * r_) & (r_ > b_ + 25)
        w = (normals @ d).clip(0, 1) * vis * (0.7 if name.endswith('_m') else 1.0)
        votes['bow'] += w * bow; votes['skin'] += w * skin; votes['hair'] += w * (~bow & ~skin)
        im = np.zeros(m_.shape + (3,), np.uint8); im[m_] = (90, 90, 90); im[sil & m_] = (230, 230, 230); im[sil & ~m_] = (230, 60, 60); im[m_ & ~sil] = (60, 120, 230)
        tiles.append(Image.fromarray(im[40 * SUP:72 * SUP, 36 * SUP:92 * SUP]))
    Vt = np.stack([votes[c] for c in ('hair', 'skin', 'bow')], 1); mat = np.array(['hair', 'skin', 'bow'])[Vt.argmax(1)]
    seen = Vt.sum(1) > 0.05; t_ = cKDTree(verts[seen]); _, ii = t_.query(verts[~seen]); mat[~seen] = mat[seen][ii]
    print('reproj IoU (4x)', rep, {c: int((mat == c).sum()) for c in ('hair', 'skin', 'bow')}, len(verts))
    np.savez_compressed(os.path.join(H, 'work', 'head_illus.npz'), V=verts, F=faces, N=normals, mat=mat, reproj=json.dumps(rep))
    W = Image.new('RGB', (sum(t.width for t in tiles), tiles[0].height)); x = 0
    for t in tiles: W.paste(t, (x, 0)); x += t.width
    W.save(os.path.join(H, 'qa', 'illus_hull_reproj.png'))


if __name__ == '__main__':
    main()
