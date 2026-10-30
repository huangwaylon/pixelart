"""Line-art metrics for char-grid sprites (swordswoman palette keys, '.' = background).

Usage: lamet.py  (prints the comparison table, writes metrics.json + 4x defect boards)
Definitions (all on the 1x grid):
  sil      silhouette px = opaque px 4-adjacent to background
  gap      silhouette px that is not K (outline break / sel-out); gap_runs = 8-connected runs of them
  dbl      redundant L-corner: a K elbow (K at two orthogonal 4-nbrs, the opposite two not K, the diagonal between them not K)
           that touches no fill px 4-wise -> deletable without exposing fill (pixel-perfect violation)
  clump    2x2 all-K blocks (line weight blob)
  wK/wD    line weight: from each silhouette px march inward (away from bg) counting consecutive K (wK) or dark px K|h|D (wD);
           histogram 1 / 2 / 3+
  zig      contour run-length zigzags: 8-chain contour -> segments using 2 adjacent directions -> run lengths of the major
           direction; a run that is a local extremum differing by >=2 from a neighbour (1-3-1, 3-1-3) = zig; any other
           non-monotone extremum (1-2-1 inside a monotone curve) = irr; segments where BOTH directions repeat = kink
  bump     1 px spikes/notches of the row/column extents (snowpeak qa.jaggy_count)
  orphK    K components (8-conn) of size <= 2 not touching the silhouette line (stray interior line px)
  intK     interior K px (not 8-connected to the silhouette K)
  flick    frame-to-frame K change after best integer shift (|K_t xor K_t+1| / |K_t|), silhouette and interior separately
"""
import os, json, sys
import numpy as np
from scipy import ndimage as nd
import cv2
from PIL import Image, ImageDraw

ROOT = '/Users/waylonhuang/Documents/other/pixelart'
OUT = os.path.join(ROOT, 'docs/team_review/2026-10-30/line_art')
REL = ROOT + '/REVIEW/exp/2026-10-28_sw_skinned/release/out/'
BUILDS = {'r10': '20261030_66119a7', 'hyb': '20261029_3831ac8', 'r4': '20261028_854761b'}
PAL = {k: v['hex'] for k, v in json.load(open(ROOT + '/swordswoman/v2/pixelize/palette.json'))['colors'].items()}
RGB = {k: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for k, h in PAL.items()}
BG = (110, 110, 110)
CROSS = nd.generate_binary_structure(2, 1)
DARK = set('KhD')


def load_txt(p):
    return np.array([list(l.rstrip('\n')) for l in open(p) if l.strip('\n')], dtype='<U1')


def master(d):
    return load_txt(f'{ROOT}/swordswoman/v2/m96/masters/EC0_{d}_96.txt')


def frames(build, act, d):
    fd = f'{REL}{BUILDS[build]}/work/{act}/{d}/final'
    fs = sorted(f for f in os.listdir(fd) if f.endswith('.txt'))
    return [load_txt(os.path.join(fd, f)) for f in fs]


def n4(m):
    p = np.pad(m, 1)
    return p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]  # N S W E


def masks(g):
    op = g != '.'
    bg = ~op
    N, S, W, E = n4(bg)
    sil = op & (N | S | W | E)
    K = g == 'K'
    return op, sil, K


def doubles(g):
    op, sil, K = masks(g)
    fill = op & ~K
    N, S, W, E = n4(K)
    p = np.pad(K, 1)
    NE, NW, SE, SW = p[:-2, 2:], p[:-2, :-2], p[2:, 2:], p[2:, :-2]
    el = ((N & E & ~S & ~W & ~NE) | (E & S & ~N & ~W & ~SE) | (S & W & ~N & ~E & ~SW) | (W & N & ~S & ~E & ~NW)) & K
    fN, fS, fW, fE = n4(fill)
    return el & ~(fN | fS | fW | fE)


def clumps(g):
    K = g == 'K'
    c = K[:-1, :-1] & K[1:, :-1] & K[:-1, 1:] & K[1:, 1:]
    m = np.zeros_like(K)
    m[:-1, :-1] |= c; m[1:, :-1] |= c; m[:-1, 1:] |= c; m[1:, 1:] |= c
    return int(c.sum()), m


def weights(g, dark):
    op, sil, K = masks(g)
    D = np.isin(g, list(dark))
    bg = ~op
    H, Wd = g.shape
    hist = [0, 0, 0, 0]  # 0,1,2,3+
    for y, x in zip(*np.nonzero(sil)):
        best = None
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            yy, xx = y - dy, x - dx  # neighbour in direction (dy,dx) is bg -> march opposite
            if 0 <= y + dy < H and 0 <= x + dx < Wd and bg[y + dy, x + dx]:
                n = 0; cy, cx = y, x
                while 0 <= cy < H and 0 <= cx < Wd and D[cy, cx] and n < 3:
                    n += 1; cy -= dy; cx -= dx
                best = n if best is None else max(best, n)
        hist[min(best, 3)] += 1
    return hist


DIRS = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]  # (dy,dx) codes 0..7


def chain(op):
    cs, _ = cv2.findContours(op.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cs:
        pts = c[:, 0, ::-1]  # (y,x)
        if len(pts) < 8: continue
        codes = []
        for a, b in zip(pts, np.roll(pts, -1, 0)):
            d = (int(b[0] - a[0]), int(b[1] - a[1]))
            if d in DIRS: codes.append(DIRS.index(d))
        out.append((pts, codes))
    return out


def stretches(op):
    """Contour (8-chain, outer) -> pixel runs -> stretches.  A run = maximal straight axis-aligned piece of the chain (broken by
    diagonal moves and by 90-degree turns).  A stretch = consecutive runs joined by the SAME diagonal move and the same axis
    orientation (1-px runs are orientation-free).  Returns list of (lengths, start points, n_corner) per contour + corner points."""
    out = []; corners = []; npx = 0
    for pts, codes in chain(op):
        npx += len(codes)
        n = len(codes)
        # rotate so we start right after a diagonal (avoid splitting a run at the array seam)
        st = next((i + 1 for i, c in enumerate(codes) if c % 2 == 1), 0)
        idx = [(st + k) % n for k in range(n)]
        runs = []  # [axisdir or None, npts, start_pt, diag_before]
        cur = [None, 1, tuple(pts[idx[0]]), None]
        for k in idx:
            c = codes[k]
            if c % 2 == 0:  # axis move
                if cur[0] is None or cur[0] == c:
                    cur[0] = c; cur[1] += 1
                else:  # 90-degree turn: L corner on the contour
                    corners.append(tuple(pts[k])); runs.append(cur); cur = [c, 2, tuple(pts[k]), 'turn']
            else:
                runs.append(cur); cur = [None, 1, tuple(pts[(k + 1) % n]), c]
        runs.append(cur)
        # stretches
        cs = []; cur_s = []; orient = None; dg = None
        for r in runs:
            o = None if r[0] is None else r[0] % 4  # 0 = horizontal (E/W), 2 = vertical (N/S)
            brk = r[3] == 'turn' or (r[3] is not None and dg is not None and r[3] != dg) or (o is not None and orient is not None and o != orient)
            if brk and cur_s:
                cs.append(cur_s)
                tail = [x for x in cur_s[-1:] if x[0] is None]  # an ambiguous 1-px run belongs to both sides
                cur_s = tail[:]; orient = None; dg = None
            cur_s.append(r)
            if o is not None: orient = o
            if r[3] not in (None, 'turn'): dg = r[3]
        if cur_s: cs.append(cur_s)
        out += cs
    return out, corners, npx


def run_defects(op):
    """zig: interior run that is a local extremum differing by >= 2 from a neighbour within a stretch (1-3-1, 4-1-4);
    irr: extremum differing by exactly 1 that breaks an otherwise monotone stretch (e.g. 1-1-2-1-2-3)."""
    zig = irr = 0; bad = []
    S_, corners, npx = stretches(op)
    for s in S_:
        L = [r[1] for r in s]
        if len(L) < 3: continue
        for k in range(1, len(L) - 1):
            p_, c_, n_ = L[k - 1], L[k], L[k + 1]
            if not ((c_ > p_ and c_ > n_) or (c_ < p_ and c_ < n_)): continue
            if max(abs(c_ - p_), abs(c_ - n_)) >= 2 and min(abs(c_ - p_), abs(c_ - n_)) >= 1:
                if k == 1 or k == len(L) - 2:
                    # end runs of a stretch are often clipped by the split; only flag if clearly a zigzag (both sides differ by >=2)
                    if min(abs(c_ - p_), abs(c_ - n_)) < 2: continue
                zig += 1; bad.append(('zig', s[k][2]))
            elif len(L) >= 5:
                # alternating 1-2-1-2 patterns are legit slopes; flag only if the neighbours on both sides are monotone otherwise
                if k >= 2 and k <= len(L) - 3 and L[k - 2] != c_ and L[k + 2] != c_:
                    irr += 1; bad.append(('irr', s[k][2]))
    return zig, irr, len(corners), npx, bad + [('kink', c) for c in corners]


def bumps(op):
    tot = 0; pts = []
    for axis in (0, 1):
        m = op if axis == 0 else op.T
        rows = [r for r in range(m.shape[0]) if m[r].any()]
        for side in (0, 1):
            ext = {r: (np.nonzero(m[r])[0].min() if side == 0 else np.nonzero(m[r])[0].max()) for r in rows}
            for r in rows:
                if r - 1 in ext and r + 1 in ext and ext[r - 1] == ext[r + 1] and abs(ext[r] - ext[r - 1]) == 1:
                    tot += 1; pts.append((r, ext[r]) if axis == 0 else (ext[r], r))
    return tot, pts


def line_parts(g):
    op, sil, K = masks(g)
    lab, n = nd.label(K, np.ones((3, 3)))
    silK = set(np.unique(lab[sil & K])) - {0}
    outer = np.isin(lab, list(silK))
    inner = K & ~outer
    sz = nd.sum(K, lab, range(1, n + 1)) if n else []
    orph = np.zeros_like(K)
    for i, s in enumerate(sz, 1):
        if i not in silK and s <= 2: orph |= lab == i
    return outer, inner, orph


def metrics(g):
    op, sil, K = masks(g)
    gap = sil & ~K
    gl, gn = nd.label(gap, np.ones((3, 3)))
    dbl = doubles(g)
    ncl, _ = clumps(g)
    zig, irr, kink, npx, _ = run_defects(op)
    b, _ = bumps(op)
    st_ = [[r[1] for r in x] for x in stretches(op)[0] if len(x) >= 3]
    def clean(L):
        d = np.diff(L)
        return bool((d >= 0).all() or (d <= 0).all() or (len(set(L)) == 2 and max(L) - min(L) == 1 and all(L[i] != L[i + 1] for i in range(len(L) - 1))))
    mono = float(np.mean([clean(L) for L in st_])) if st_ else 1.0
    outer, inner, orph = line_parts(g)
    gapcol = {}
    for c in g[gap]: gapcol[c] = gapcol.get(c, 0) + 1
    return dict(sil=int(sil.sum()), gap=int(gap.sum()), gap_runs=int(gn), gap_cols=dict(sorted(gapcol.items(), key=lambda kv: -kv[1])[:4]),
                dbl=int(dbl.sum()), clump=ncl, wK=weights(g, 'K'), wD=weights(g, DARK), zig=zig, irr=irr, kink=kink, contour=npx,
                bump=b, mono=mono, intK=int(inner.sum()), orphK=int(orph.sum()), K=int(K.sum()))


def best_shift(a, b, r=3):
    best = (1e9, 0, 0)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            s = np.roll(np.roll(b, dy, 0), dx, 1)
            v = int((a != s).sum())
            if v < best[0]: best = (v, dy, dx)
    return best[1:]


def flicker(fr):
    """boil: fraction of K px (silhouette line / interior line) with no K of the same kind within 1 px in the neighbouring frame
    (after the best global integer shift) - K that appears/disappears rather than moving with the body.  Mean of both directions."""
    out_s, out_i = [], []
    for a, b in zip(fr, fr[1:] + fr[:1]):
        dy, dx = best_shift(a != '.', b != '.')
        b2 = np.roll(np.roll(b, dy, 0), dx, 1)
        oa, ia, _ = line_parts(a); ob, ib, _ = line_parts(b2)
        for x, y, acc in ((oa, ob, out_s), (ia, ib, out_i)):
            dx_ = nd.binary_dilation(x, np.ones((3, 3))); dy_ = nd.binary_dilation(y, np.ones((3, 3)))
            acc.append(0.5 * ((y & ~dx_).sum() / max(y.sum(), 1) + (x & ~dy_).sum() / max(x.sum(), 1)))
    return float(np.mean(out_s)), float(np.mean(out_i))


def rgb(g, s=4, bg=BG):
    H, W = g.shape
    a = np.zeros((H, W, 3), np.uint8); a[:] = bg
    for k, c in RGB.items(): a[g == k] = c
    return Image.fromarray(a).resize((W * s, H * s), Image.NEAREST)


def crop_box(gs, pad=3):
    ys, xs = [], []
    for g in gs:
        y, x = np.nonzero(g != '.'); ys += [y.min(), y.max()]; xs += [x.min(), x.max()]
    return max(min(ys) - pad, 0), min(max(ys) + pad + 1, 128), max(min(xs) - pad, 0), min(max(xs) + pad + 1, 128)


def annotate(g, s=6):
    im = rgb(g, s).convert('RGB'); dr = ImageDraw.Draw(im)
    op, sil, K = masks(g)

    def circ(y, x, col, r=None):
        r = r or s * 1.1
        cx, cy = x * s + s / 2, y * s + s / 2
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
    for y, x in zip(*np.nonzero(sil & ~K)): dr.rectangle([x * s + 1, y * s + 1, x * s + s - 2, y * s + s - 2], outline=(0, 230, 255), width=1)
    _, cm = clumps(g)
    for y, x in zip(*np.nonzero(cm)): dr.rectangle([x * s + 2, y * s + 2, x * s + s - 3, y * s + s - 3], fill=(255, 140, 0))
    for y, x in zip(*np.nonzero(doubles(g))): circ(y, x, (255, 40, 40))
    for kind, (y, x) in run_defects(op)[4]:
        circ(y, x, {'zig': (255, 235, 0), 'irr': (190, 190, 60), 'kink': (255, 0, 255)}[kind], s * 1.6 if kind == 'zig' else s * 1.2)
    for y, x in bumps(op)[1]: circ(y, x, (120, 255, 120))
    _, _, orph = line_parts(g)
    for y, x in zip(*np.nonzero(orph)): circ(y, x, (255, 0, 200), s * 1.8)
    return im


def board(cols, path, s=6, title=None):
    """cols: list of (label, grid). One row, cropped to a common box, plain 4x + annotated."""
    y0, y1, x0, x1 = crop_box([g for _, g in cols])
    tiles = []
    for lab, g in cols:
        c = g[y0:y1, x0:x1]
        a = rgb(c, s); b = annotate(c, s)
        t = Image.new('RGB', (a.width, a.height * 2 + 36), (40, 40, 40)); t.paste(a, (0, 18)); t.paste(b, (0, a.height + 36))
        d = ImageDraw.Draw(t); d.text((4, 3), lab, fill=(255, 255, 255)); d.text((4, a.height + 21), 'annotated', fill=(200, 200, 200))
        tiles.append(t)
    W = sum(t.width + 6 for t in tiles); H = max(t.height for t in tiles) + 40
    out = Image.new('RGB', (W, H), (25, 25, 25)); x = 0
    for t in tiles: out.paste(t, (x, 0)); x += t.width + 6
    d = ImageDraw.Draw(out)
    d.text((4, H - 34), 'red=redundant L-corner  yellow=1-3-1 zigzag  olive=1-2-1 irregular  magenta=kink/orphan K  green=1px bump', fill=(230, 230, 230))
    d.text((4, H - 18), 'cyan box=silhouette px not K (gap/sel-out)  orange=2x2 K clump' + (('   ' + title) if title else ''), fill=(230, 230, 230))
    out.save(path)


def summarise(ms):
    keys = ['mono', 'gap', 'gap_runs', 'dbl', 'clump', 'zig', 'irr', 'kink', 'bump', 'intK', 'orphK', 'K', 'contour']
    r = {k: float(np.mean([m[k] for m in ms])) for k in keys}
    for w in ('wK', 'wD'):
        h = np.sum([m[w] for m in ms], 0); h = h / max(h.sum(), 1)
        r[w] = [round(float(v), 3) for v in h]
    r['zig_per100'] = 100 * r['zig'] / max(r['contour'], 1)
    r['irr_per100'] = 100 * (r['irr'] + r['kink']) / max(r['contour'], 1)
    return r


if __name__ == '__main__':
    res = {}
    for d in ('S', 'SE', 'E'):
        res[f'master/{d}'] = summarise([metrics(master(d))])
        for b in ('r10', 'hyb', 'r4'):
            for act in ('idle', 'walk'):
                fr = frames(b, act, d)
                s = summarise([metrics(g) for g in fr]); s['flick_sil'], s['flick_int'] = flicker(fr); s['n'] = len(fr)
                res[f'{b}/{act}/{d}'] = s
        board([('master EC0_' + d, master(d)), ('r10 idle f00', frames('r10', 'idle', d)[0]), ('r10 walk f02', frames('r10', 'walk', d)[2]),
               ('hybrid idle f00', frames('hyb', 'idle', d)[0]), ('hybrid walk f02', frames('hyb', 'walk', d)[2])], f'{OUT}/board_audit_{d}.png')
    json.dump(res, open(f'{OUT}/metrics.json', 'w'), indent=1)
    hdr = f"{'set':16s} {'gap':>5s} {'gRun':>5s} {'dbl':>4s} {'clmp':>5s} {'zig':>4s} {'irr':>4s} {'kink':>4s} {'bump':>4s} {'intK':>5s} {'orph':>4s} {'mono':>5s}  wK(0/1/2/3+)          wD(0/1/2/3+)          flk_s flk_i"
    print(hdr)
    for k, r in res.items():
        print(f"{k:16s} {r['gap']:5.1f} {r['gap_runs']:5.1f} {r['dbl']:4.1f} {r['clump']:5.1f} {r['zig']:4.1f} {r['irr']:4.1f} {r['kink']:4.1f} {r['bump']:4.1f} {r['intK']:5.1f} {r['orphK']:4.1f} {r['mono']:5.2f}  "
              f"{str(r['wK']):22s}{str(r['wD']):22s}{r.get('flick_sil', 0):5.2f} {r.get('flick_int', 0):5.2f}")
