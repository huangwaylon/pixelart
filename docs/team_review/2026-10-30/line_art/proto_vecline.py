"""Prototype: vector silhouette line for the skinned-rig pixel chain (no rebuild; post-process of a built frame).

For one built frame (round-10 chain output + R's 8x passes in release/out/<build>/work/<act>/<DIR>/):
 1. silhouette contour(s) from the 8x alpha (guide pass), traced at 8x with cv2 (outer + holes >= HOLE_MIN 1x px^2)
 2. contour -> 1x float coords, Gaussian-smoothed along the curve (SIG px), simplified (Douglas-Peucker, EPS px)
 3. vertices snapped to pixel centres, segments rasterised with Bresenham (one straight digital segment per edge =
    regular runs), then the ordered path is made pixel-perfect (an orthogonal elbow between two diagonal neighbours is dropped)
 4. the path is the outer line (K, or sel-out on lit top/left edges with --selout); inside = 4-connected regions of ~line with
    8x coverage >= .5 that are not connected to the frame border
 5. fill colours: the chain's own colours (nearest chain fill colour where the new silhouette adds a pixel)
 6. interior lines: the chain's interior K outside the textured head is skeletonised to 1 px, made pixel-perfect, components
    < MINLEN px dropped; the textured head (eyes, lashes, face) keeps the chain's pixels unchanged.
Usage: proto_vecline.py  -> writes proto_<act>_<DIR>_fNN.txt/png + board_proto_*.png + proto_metrics.json
"""
import os, sys, json
import numpy as np, cv2
from scipy import ndimage as nd
from skimage.morphology import skeletonize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lamet as L

P, N, OFF = 8, 128, 256
SIG = float(os.environ.get('SIG', '0.9'))      # smoothing along the contour, 1x px
EPS = float(os.environ.get('EPS', '0.8'))     # Douglas-Peucker tolerance, 1x px
HOLE_MIN = 6                                   # holes (arm|body gaps) smaller than this many 1x px are ignored
MINLEN = 4
PIN = float(os.environ.get('PIN', '100'))  # interior angle (deg) below which a contour corner is pinned (0 = off)
MODE = os.environ.get('MODE', 'clean')
SHRINK = int(os.environ.get('SHRINK', '4'))  # hi-res px the alpha is eroded before tracing (matches the chain's silhouette volume)
BUILD = L.BUILDS['r10']


def rd(p):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    a = a[..., [2, 1, 0, 3]]
    return a.astype(np.float64) / (65535. if a.dtype == np.uint16 else 255.)


def bres(p0, p1):
    (y0, x0), (y1, x1) = p0, p1
    dy, dx = abs(y1 - y0), abs(x1 - x0); sy = 1 if y1 > y0 else -1; sx = 1 if x1 > x0 else -1
    err = dx - dy; pts = []
    while True:
        pts.append((y0, x0))
        if (y0, x0) == (y1, x1): break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x0 += sx
        if e2 < dx: err += dx; y0 += sy
    return pts


def clean_seg(p0, p1, tol=0.25):
    """segment p0->p1 drawn with UNIFORM runs when the slope is close to a clean ratio 1:k / k:1 (k = 1,2,3,4,...);
    otherwise Bresenham (which alternates k,k+1).  Returns pixels incl. both ends (the end may drift from p1 by < 1 run)."""
    (y0, x0), (y1, x1) = p0, p1
    dy, dx = y1 - y0, x1 - x0
    ady, adx = abs(dy), abs(dx)
    if ady == 0 or adx == 0: return bres(p0, p1)
    sy, sx = (1 if dy > 0 else -1), (1 if dx > 0 else -1)
    long_, short = max(ady, adx), min(ady, adx)
    r = long_ / short; k = max(1, int(round(r)))
    if abs(r - k) / r > tol: return bres(p0, p1)
    pts = [(y0, x0)]; y, x = y0, x0
    for i in range(short):
        for j in range(k):
            if adx >= ady:
                x += sx
                if j == 0: y += sy
            else:
                y += sy
                if j == 0: x += sx
            pts.append((y, x))
    return pts


def pixel_perfect(path):
    """drop orthogonal elbows on a closed ordered 8-path; dedupe."""
    out = []
    for p in path:
        if not out or out[-1] != p: out.append(p)
    changed = True
    while changed and len(out) > 4:
        changed = False; res = []
        n = len(out)
        i = 0
        keep = [True] * n
        for i in range(n):
            a, b, c = out[i - 1], out[i], out[(i + 1) % n]
            if not keep[i - 1]: continue
            if abs(a[0] - c[0]) == 1 and abs(a[1] - c[1]) == 1 and (a[0] == b[0] or a[1] == b[1]) and (c[0] == b[0] or c[1] == b[1]):
                keep[i] = False; changed = True
        out = [p for p, k in zip(out, keep) if k]
    return out


def smooth_closed(c, sig):
    if sig <= 0 or len(c) < 8: return c
    r = int(3 * sig * 8) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / (sig * 8)) ** 2); k /= k.sum()
    cp = np.concatenate([c[-r:], c, c[:r]], 0)
    return np.stack([np.convolve(cp[:, j], k, 'valid') for j in range(2)], 1)


def vec_line(alpha8):
    """alpha8: (1024,1024) bool at 8x -> (line mask, inside mask) at 1x."""
    cs, hier = cv2.findContours(alpha8.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    line = np.zeros((N, N), bool)
    for c, h in zip(cs, hier[0]):
        area = cv2.contourArea(c) / 64.0
        if area < (HOLE_MIN if h[3] >= 0 else 4): continue
        pts = c[:, 0, :].astype(float)  # (x,y) 8x
        pts = (pts + 0.5) / P            # 1x continuous coords (pixel i spans [i, i+1))
        sm = smooth_closed(pts, SIG)
        if PIN > 0 and len(pts) > 40:
            # corner pinning: where the raw 8x contour turns sharply (bow lobes, hair tips, toes, fingers) keep the raw shape
            k = 12  # 1.5 px at 8x
            a = np.roll(pts, k, 0) - pts; b = np.roll(pts, -k, 0) - pts
            cosang = (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-9)
            sharp = cosang > np.cos(np.radians(PIN))  # interior angle < PIN degrees
            w = nd.maximum_filter1d(sharp.astype(float), 2 * k + 1, mode='wrap')
            w = nd.uniform_filter1d(w, k, mode='wrap')[:, None]
            sm = w * pts + (1 - w) * sm
        pts = sm
        if MODE == 'poly':
            ap = cv2.approxPolyDP(pts.astype(np.float32).reshape(-1, 1, 2), EPS, True)[:, 0, :]
            v = [(int(np.floor(y)), int(np.floor(x))) for x, y in ap]  # pixel containing the vertex
            path = []
            for a, b in zip(v, v[1:] + v[:1]): path += bres(a, b)[:-1]
        elif MODE == 'clean':  # clean slopes: uniform runs per segment; the drift is re-aimed by the next segment
            ap = cv2.approxPolyDP(pts.astype(np.float32).reshape(-1, 1, 2), EPS, True)[:, 0, :]
            v = [(int(np.floor(y)), int(np.floor(x))) for x, y in ap]
            v = [p for i, p in enumerate(v) if p != v[i - 1]] or v
            path = []; cur = v[0]
            for b in v[1:] + v[:1]:
                sg = clean_seg(cur, b); path += sg[:-1]; cur = sg[-1]
            if cur != v[0]: path += bres(cur, v[0])[:-1]
        else:  # dense: digitise the smooth curve itself (a convex smooth curve digitises to monotone run lengths)
            seg = np.concatenate([pts, pts[:1]], 0)
            dense = []
            for a, b in zip(seg[:-1], seg[1:]):
                k = max(2, int(np.ceil(np.abs(b - a).max() * 8)))
                dense += [a + (b - a) * t for t in np.arange(k) / k]
            path = [(int(np.floor(y)), int(np.floor(x))) for x, y in dense]
            # 4-steps between consecutive samples can't skip px (dense), keep 8-connected chain
        path = pixel_perfect(path)
        for y, x in path:
            if 0 <= y < N and 0 <= x < N: line[y, x] = True
    cov = alpha8.reshape(N, P, N, P).mean((1, 3))
    lab, n = nd.label(~line, nd.generate_binary_structure(2, 1))
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    inside = np.zeros((N, N), bool)
    for i in range(1, n + 1):
        if i in border: continue
        m = lab == i
        if cov[m].mean() >= 0.5: inside |= m
    # a line pixel is kept only if it touches inside or is needed to close it (all of it here)
    return line, inside


def thin_interior(K, protect):
    sk = skeletonize(K & ~protect)
    # pixel-perfect on a skeleton raster: remove elbow px whose removal keeps 8-connectivity (two orthogonal neighbours, the diagonal free)
    for _ in range(2):
        p = np.pad(sk, 1)
        Nn, Ss, Ww, Ee = p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]
        NE, NW, SE, SW = p[:-2, 2:], p[:-2, :-2], p[2:, 2:], p[2:, :-2]
        el = sk & (((Nn & Ee) & ~NE & ~Ss & ~Ww) | ((Ee & Ss) & ~SE & ~Nn & ~Ww) | ((Ss & Ww) & ~SW & ~Nn & ~Ee) | ((Ww & Nn) & ~NW & ~Ss & ~Ee))
        # remove one elbow per conflict: only those whose index parity is even (avoids removing both pixels of a 2-px corner)
        yy, xx = np.nonzero(el)
        for y, x in zip(yy, xx):
            if (y + x) % 2 == 0: sk[y, x] = False
    lab, n = nd.label(sk, np.ones((3, 3)))
    if n:
        sz = nd.sum(sk, lab, range(1, n + 1))
        sk &= np.isin(lab, [i + 1 for i, s in enumerate(sz) if s >= MINLEN])
    return sk | (K & protect)


SELOUT = {'E': 'R', 'e': 'E', 's': 'S', 'S': 'm', 'k': 'm', 'O': 'o', 'Q': 'O'}  # lit edge: one ramp step darker than the fill


def process(act, d, i, selout=False):
    wd = f'{L.REL}{BUILD}/work/{act}/{d}'
    st = f'{wd}/{act}_{d}_f{i:02d}_'
    g0 = L.load_txt(f'{wd}/final/f{i:02d}.txt')
    al = rd(st + 'guide.png')[..., 3] > 0.5
    tex = rd(st + 'tex.png')[..., 3] > 0.5 if os.path.exists(st + 'tex.png') else np.zeros_like(al)
    al8 = al[OFF:OFF + N * P, OFF:OFF + N * P]; tx8 = tex[OFF:OFF + N * P, OFF:OFF + N * P]
    cov = al8.reshape(N, P, N, P).mean((1, 3)) >= 0.5
    dy, dx = L.best_shift(g0 != '.', cov, r=12)
    al8 = np.roll(np.roll(al8, dy * P, 0), dx * P, 1); tx8 = np.roll(np.roll(tx8, dy * P, 0), dx * P, 1)
    line, inside = vec_line(nd.binary_erosion(al8, iterations=SHRINK) if SHRINK else al8)
    head = tx8.reshape(N, P, N, P).mean((1, 3)) >= 0.5
    head = nd.binary_erosion(head, iterations=1)  # the head's own silhouette is handled by the vector line
    # fill colours from the chain
    fillc = np.isin(g0, list('.K'), invert=True)
    idx = nd.distance_transform_edt(~fillc, return_distances=False, return_indices=True)
    near = g0[idx[0], idx[1]]
    g = np.full((N, N), '.', dtype='<U1')
    g[inside] = near[inside]
    # chain interior K: K not 8-adjacent to background in the chain frame
    K0 = g0 == 'K'; bg0 = g0 == '.'
    outer0 = K0 & nd.binary_dilation(bg0, np.ones((3, 3)))
    intK = K0 & ~outer0
    ik = thin_interior(intK, head) & inside
    g[ik] = 'K'
    g[line] = 'K'
    # line pixels with no inside neighbour (stroke bulging into the background) are dropped
    p = np.pad(inside, 1); n4 = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    p8 = n4 | np.pad(inside, 1)[:-2, :-2] | np.pad(inside, 1)[:-2, 2:] | np.pad(inside, 1)[2:, :-2] | np.pad(inside, 1)[2:, 2:]
    g[line & ~p8] = '.'
    if selout:
        # lit from screen top-left: a silhouette px whose background lies up/left and whose inner neighbour (down/right) is a lit fill
        bg = g == '.'
        pb = np.pad(bg, 1)
        up_l = pb[:-2, 1:-1] | pb[1:-1, :-2]
        for y, x in zip(*np.nonzero(line & up_l & (g == 'K'))):
            for yy, xx in ((y + 1, x), (y, x + 1), (y + 1, x + 1)):
                if 0 <= yy < N and 0 <= xx < N and g[yy, xx] in SELOUT and not head[y, x]:
                    g[y, x] = SELOUT[g[yy, xx]]; break
    return g0, g


if __name__ == '__main__':
    OUTD = L.OUT
    sets = [('walk', 'SE', k) for k in range(4)] + [('idle', 'SE', 0), ('idle', 'S', 0), ('idle', 'E', 0)]
    res = {}; per = {}
    for act, d, i in sets:
        g0, g = process(act, d, i)
        _, gs = process(act, d, i, selout=True)
        per[(act, d, i)] = (g0, g, gs)
        open(f'{OUTD}/proto_{act}_{d}_f{i:02d}.txt', 'w').write('\n'.join(''.join(r) for r in g) + '\n')
        for nm, gg in (('chain', g0), ('proto', g), ('selout', gs)):
            res[f'{nm}/{act}/{d}/f{i:02d}'] = L.metrics(gg)
    # boil on walk SE f0-3 (open sequence, 3 transitions)
    def boil(fr):
        fs, fi = [], []
        for a, b in zip(fr, fr[1:]):
            s_, i_ = L.flicker([a, b]); fs.append(s_); fi.append(i_)
        return float(np.mean(fs)), float(np.mean(fi))
    res['boil/chain/walk/SE'] = boil([per[('walk', 'SE', k)][0] for k in range(4)])
    res['boil/proto/walk/SE'] = boil([per[('walk', 'SE', k)][1] for k in range(4)])
    json.dump(res, open(f'{OUTD}/proto_metrics.json', 'w'), indent=1, default=str)
    for d in ('SE', 'S', 'E'):
        g0, g, gs = per[('idle', d, 0)]
        L.board([('master EC0_' + d, L.master(d)), ('r10 chain idle f00', g0), ('PROTO vector line', g), ('PROTO + sel-out', gs)], f'{OUTD}/board_proto_idle_{d}.png')
    L.board([(f'chain walk f{k}', per[('walk', 'SE', k)][0]) for k in range(4)] + [(f'proto walk f{k}', per[('walk', 'SE', k)][1]) for k in range(4)],
            f"{OUTD}/board_proto_walk_SE.png", s=5)
    keys = ['gap', 'dbl', 'clump', 'zig', 'irr', 'kink', 'mono', 'intK', 'orphK', 'K']
    print(f"{'frame':28s} " + ' '.join(f'{k:>6s}' for k in keys) + '  wK')
    for k, m in res.items():
        if k.startswith('boil'): print(k, m); continue
        print(f'{k:28s} ' + ' '.join(f'{m[x]:6.2f}' if isinstance(m[x], float) else f'{m[x]:6d}' for x in keys) + '  ' + str(m['wK']))
