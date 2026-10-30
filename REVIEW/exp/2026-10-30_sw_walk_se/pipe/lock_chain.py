"""lock_chain.py WORKDIR/<act>_<VIEW>.json OUTDIR   (pixtools venv)  -- steps 2-4 of the walk-SE lock build: 8x passes -> 1x frames.

Inputs (render_lock.py): per frame guide (material), part, nrm (camera normal), dep (camera depth) at 8x, + eye surface points.
Per frame, in this order (one rule set, no per-frame special cases):
 A. Labels: 8x material + body sub-part (leg.L leg.R arm.L arm.R hand.L hand.R torso neck face hair bow) -> 1x cell vote.
 B. Outline (DESIGN_LOCK 3): the 8x silhouette (eroded SHRINK hi-res px) is traced, Gaussian-smoothed along the curve (SIG px),
    sharp corners pinned (< PIN deg), simplified (Douglas-Peucker EPS px) and redrawn at 1x with uniform slope runs
    (proto_vecline.clean_seg) + pixel-perfect.  TEMPORAL: every polyline vertex snaps to the previous frame's line of the same body
    part (moved by that part's best integer shift) when it passes within SNAP px, so parts keep their line pixels frame to frame
    (vertex hysteresis; the loop is run twice so f00 sees f07).  Inside = the 4-connected regions the line encloses.
 C. Colour (DESIGN_LOCK 2): 14 locked keys; per material a fixed 2-tone ramp (base, shadow) chosen by the band of N.L
    (smoothed camera normal . the renderer's sun direction), the same thresholds in every frame/direction; hair adds the one
    highlight L on the top row of its brightest band; the face skin is always flat s, the neck S.  Band hysteresis: a cell keeps the
    previous frame's band (same material, shifted) while N.L is within HYS of the threshold.
 D. Interior lines (DESIGN_LOCK 3): only where a listed pair of sub-parts meets: leg|leg, arm or hand over body, hand|sleeve,
    bangs|face, bow|hair, chin|neck; drawn 1 px K on the far side (camera depth; bangs|face on the hair side so the face keeps its
    width), only where the 3D depth step is > DSTEP (not for the same-hull pairs bangs|face, bow|hair), pixel-perfect, >= MINLEN px.
 E. Face (DESIGN_LOCK 1): facesys b' eye + brow templates at the tracked surface point (render_lock eyes), hidden by depth (a nearer
    surface at the point = occluded) and clipped to face skin; an eye < 60 % visible is dropped whole; brows on hair are K;
    SE far eye: 2-frame hysteresis.  Expression from the motion keys (facesys/proto EXMAP -> 7 expressions).
 F. Cleanup that can only remove K: redundant L-corners and 2x2 K clumps on interior lines (outline untouched).
Outputs: OUTDIR/fNN.png (128 RGBA) + fNN.txt (key grid), OUTDIR/labels.npz (per-frame material/sub-part/line masks for the gates)."""
import os, sys, json
import numpy as np, cv2
from scipy import ndimage as nd
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart'
sys.path.insert(0, ROOT + '/docs/team_review/2026-10-30/line_art')
sys.path.insert(0, ROOT + '/docs/team_review/2026-10-30/face_palette/scripts')
import proto_vecline as PV  # noqa: E402  (clean_seg, bres, pixel_perfect, smooth_closed)
import facesys as FS  # noqa: E402  (eye templates T, eye(), mirror/narrow)
from lamet import run_defects as LM_run_defects, doubles as LM_doubles  # noqa: E402  (defect counts used by the cleanup)

P, N, OFF = 8, 128, 256
_E = lambda k, d: float(os.environ.get('LOCK_' + k, d))  # tuning overrides (defaults = the locked build)
SHRINK, SIG, EPS, PIN, SNAP, HOLE_MIN = int(_E('SHRINK', 4)), _E('SIG', 0.9), _E('EPS', 0.8), _E('PIN', 100.0), _E('SNAP', 0.75), 6
DSTEP, MINLEN, HYS = 0.02, 4, 0.06
PAL = {k: tuple(int(v['hex'][i:i + 2], 16) for i in (1, 3, 5)) for k, v in json.load(open(ROOT + '/swordswoman/v2/pixelize/palette.json'))['colors'].items()}
LOCK14 = list('KhHgLsSeERQOoW')
PAL = {k: PAL[k] for k in LOCK14}
MATS = {'hair': (61, 50, 53), 'dress': (192, 59, 61), 'skin': (248, 218, 194), 'sleeve': (142, 34, 44), 'socks': (38, 42, 71),
        'boots': (42, 34, 42), 'bow': (232, 96, 79), 'obi': (69, 56, 73)}  # rig guide colours (hx.MATS)
MN = list(MATS); MI = {n: i for i, n in enumerate(MN)}; MCOL = np.array([MATS[k] for k in MN], float)
PARTS = {'leg.L': (255, 0, 0), 'leg.R': (0, 255, 0), 'arm.L': (0, 0, 255), 'arm.R': (255, 255, 0), 'torso': (255, 0, 255), 'head': (0, 255, 255)}
PN = list(PARTS); PCOL = np.array([PARTS[k] for k in PN], float)
SUB = ['leg.L', 'leg.R', 'arm.L', 'arm.R', 'hand.L', 'hand.R', 'torso', 'neck', 'face', 'hair', 'bow']; SI = {n: i for i, n in enumerate(SUB)}
# 2-tone ramps (shadow, base) + the N.L threshold below which a cell is shadow; the same in every frame and direction
RAMP = {'hair': ('h', 'H', 0.15), 'dress': ('R', 'E', 0.05), 'sleeve': ('R', 'E', 0.05), 'bow': ('E', 'e', 0.20), 'obi': ('o', 'O', -0.15),
        'skin': ('S', 's', -0.10), 'socks': ('h', 'H', 0.00), 'boots': ('H', 'g', 0.00)}
NSIG = {'dress': 3.0, 'sleeve': 3.0, 'skin': 2.0, 'socks': 1.5, 'boots': 1.5, 'hair': 1.5, 'bow': 1.0, 'obi': 1.0}  # N.L smoothing (sprite px) per material: big flat cloth bands
HAIR_L = 0.88   # hair highlight band (top row of the cells above it becomes L)
SUN = np.array([-0.32, 0.67, -0.67]); SUN /= np.linalg.norm(SUN)  # render_motion.py sun (-right*.6 + up*.9 + toward-cam*.9) in camera space
# allowed colours per material (palette gate: no material uses another material's colours); K = line everywhere
ALLOW = {'hair': 'hHLK', 'socks': 'hHK', 'boots': 'HgK', 'skin': 'sSK', 'dress': 'REK', 'sleeve': 'REK', 'bow': 'eEK', 'obi': 'oOK'}
FACE_INK = 'KgWh'
PAIRS = {('leg.L', 'leg.R'): 'leg|leg', ('arm.L', 'torso'): 'arm|body', ('arm.R', 'torso'): 'arm|body', ('hand.L', 'torso'): 'arm|body',
         ('hand.R', 'torso'): 'arm|body', ('hand.L', 'arm.L'): 'hand|sleeve', ('hand.R', 'arm.R'): 'hand|sleeve', ('face', 'hair'): 'bangs|face',
         ('bow', 'hair'): 'bow|hair', ('face', 'neck'): 'chin|neck'}
SAMEHULL = {'bangs|face', 'bow|hair'}  # same surface, colour boundary: no depth step required
EXMAP = {'neutral': 'open', 'smile': 'open', 'joyful': 'happy', 'joy': 'happy', 'determined': 'determined', 'focused': 'determined',
         'effort': 'determined', 'surprised': 'surprised', 'pained': 'hurt', 'wince': 'hurt', 'squint': 'half'}  # face_palette/scripts/proto.py
CROSS = nd.generate_binary_structure(2, 1)


def rd(p):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED); a = a[..., [2, 1, 0, 3]]
    return a.astype(np.float64) / (65535. if a.dtype == np.uint16 else 255.)


def crop(a, dx, dy): return np.roll(np.roll(a[OFF:OFF + N * P, OFF:OFF + N * P], dy * P, 0), dx * P, 1)


def blocks(a): return a.reshape(N, P, N, P, *a.shape[2:]).swapaxes(1, 2).reshape(N, N, P * P, *a.shape[2:])


def expr_of(fr):
    e = EXMAP.get(fr.get('face') or 'neutral', 'open'); b = fr.get('blink', 0) or 0
    try: b = float(b)
    except (TypeError, ValueError): b = 1.0 if str(b) in ('closed', 'blink') else 0.5
    if e == 'hurt': return e
    return 'closed' if b >= 1 else 'half' if b >= .5 else e


# ------------------------------------------------------------------ A. labels
def load(stem, i, al_):
    dx, dy = al_['dx'], al_['dy']; st = f'{stem}_f{i:02d}_'
    g = crop(rd(st + 'guide.png'), dx, dy); alpha = g[..., 3] > 0.5
    mid = ((g[..., None, :3] * 255 - MCOL) ** 2).sum(-1).argmin(-1)
    pa = crop(rd(st + 'part.png'), dx, dy); pid = ((pa[..., None, :3] * 255 - PCOL) ** 2).sum(-1).argmin(-1)
    nrm = crop(rd(st + 'nrm.png'), dx, dy)[..., :3] * 2 - 1; dep = crop(rd(st + 'dep.png'), dx, dy)[..., 0] * 20
    sub = np.full(mid.shape, SI['torso'])
    for s in 'LR':
        sub[pid == PN.index('leg.' + s)] = SI['leg.' + s]
        arm = pid == PN.index('arm.' + s); sub[arm] = SI['arm.' + s]; sub[arm & (mid == MI['skin'])] = SI['hand.' + s]
    head = pid == PN.index('head'); sub[head & (mid == MI['skin'])] = SI['face']
    sub[(pid == PN.index('torso')) & (mid == MI['skin'])] = SI['neck']
    sub[mid == MI['hair']] = SI['hair']; sub[mid == MI['bow']] = SI['bow']
    # skirt cloth weighted to the thighs is torso; the red sock-top bands (dress material on the leg, not touching the skirt) stay leg
    legcloth = np.isin(sub, [SI['leg.L'], SI['leg.R']]) & np.isin(mid, [MI['dress'], MI['sleeve'], MI['obi']]) & alpha
    lc, nlc = nd.label(legcloth); skirt = nd.binary_dilation((sub == SI['torso']) & np.isin(mid, [MI['dress'], MI['obi']]) & alpha, CROSS)
    touch = np.unique(lc[skirt & legcloth]); sub[np.isin(lc, touch[touch > 0])] = SI['torso']
    mid[~alpha] = -1; sub[~alpha] = -1; dep[~alpha] = np.inf
    return dict(alpha=alpha, mid=mid, sub=sub, nrm=nrm, dep=dep)


def vote(lab, alpha, n):
    """plurality label per 1x cell (-1 where the cell has no coverage)"""
    b = blocks(np.where(alpha, lab, n)); cnt = np.stack([(b == k).sum(-1) for k in range(n + 1)], -1); cnt[..., n] = 0
    out = cnt.argmax(-1); out[cnt.max(-1) == 0] = -1; return out


def vote_given(lab, mid, alpha, mat1, n):
    b = blocks(np.where(alpha & (mid == np.repeat(np.repeat(mat1, P, 0), P, 1)), lab, n))
    cnt = np.stack([(b == k).sum(-1) for k in range(n)], -1); out = cnt.argmax(-1); out[cnt.max(-1) == 0] = -1; return out


def fill_nearest(lab, inside):
    known = lab >= 0
    if not known.any(): return lab
    idx = nd.distance_transform_edt(~known, return_distances=False, return_indices=True)
    out = lab[idx[0], idx[1]]; out[~inside] = -1; return out


# ------------------------------------------------------------------ B. outline (vector line + temporal vertex hysteresis)
def trace(alpha8, prev_line=None):
    cs, hier = cv2.findContours(alpha8.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    line = np.zeros((N, N), bool); snapped = total = 0
    by_part, cur_part = prev_line if prev_line is not None else ({}, None)
    for c, h in zip(cs, hier[0]):
        if cv2.contourArea(c) / 64.0 < (HOLE_MIN if h[3] >= 0 else 4): continue
        pts = (c[:, 0, :].astype(float) + 0.5) / P
        sm = PV.smooth_closed(pts, SIG)
        if len(pts) > 40:  # pin sharp corners (bow lobes, hair tips, toes) to the raw shape
            k = 12; a = np.roll(pts, k, 0) - pts; b = np.roll(pts, -k, 0) - pts
            cosang = (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-9)
            w = nd.maximum_filter1d((cosang > np.cos(np.radians(PIN))).astype(float), 2 * k + 1, mode='wrap')
            w = nd.uniform_filter1d(w, k, mode='wrap')[:, None]; sm = w * pts + (1 - w) * sm
        ap = cv2.approxPolyDP(sm.astype(np.float32).reshape(-1, 1, 2), EPS, True)[:, 0, :]
        v = []
        for x, y in ap:
            q = (int(np.floor(y)), int(np.floor(x))); total += 1
            pl = by_part.get(int(cur_part[min(max(q[0], 0), N - 1), min(max(q[1], 0), N - 1)])) if cur_part is not None else None
            if pl is not None and len(pl):  # vertex hysteresis: reuse last frame's line pixel (same part, motion-compensated) within SNAP px
                d = np.abs(pl[:, 0] + 0.5 - y).clip(0) ** 2 + np.abs(pl[:, 1] + 0.5 - x) ** 2; j = d.argmin()
                if d[j] <= SNAP ** 2: q = (int(pl[j, 0]), int(pl[j, 1])); snapped += 1
            v.append(q)
        v = [p for i, p in enumerate(v) if p != v[i - 1]] or v
        path = []; cur = v[0]
        for b in v[1:] + v[:1]:
            sg = PV.clean_seg(cur, b); path += sg[:-1]; cur = sg[-1]
        if cur != v[0]: path += PV.bres(cur, v[0])[:-1]
        path = PV.pixel_perfect(path)
        if h[3] < 0: path = dezig(path)  # outer contour: remove remaining 1-3-1 zigzags (lamet run rule)
        for y, x in path:
            if 0 <= y < N and 0 <= x < N: line[y, x] = True
    cov = blocks(alpha8.astype(float)).mean(-1)
    lab, n = nd.label(~line, CROSS)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    inside = np.zeros((N, N), bool)
    for i in range(1, n + 1):
        if i not in border and cov[lab == i].mean() >= 0.5: inside |= lab == i
    p8 = nd.binary_dilation(inside, np.ones((3, 3)))
    line &= p8  # a stroke pixel that touches no inside cell is not needed
    return line, inside, (snapped, total)


def path_zigs(path):
    """lamet 1-3-1 zigzag sites of the closed outer path (the path filled = the silhouette it draws)"""
    m = np.zeros((N, N), bool)
    for y, x in path:
        if 0 <= y < N and 0 <= x < N: m[y, x] = True
    return [p for k, p in LM_run_defects(nd.binary_fill_holes(m))[4] if k == 'zig']


def dezig(path, it=10):
    """remove the remaining zigzags of the outer path: the span around a zigzag (W path px each side) is re-drawn as one
    Bresenham segment; the change is kept only if the path's zigzag count drops (lamet rule)"""
    z = path_zigs(path)
    for _ in range(it):
        if not z: break
        best = None; idx = {p: i for i, p in enumerate(path)}
        for (y, x) in z:
            i = idx.get((int(y), int(x)))
            if i is None: continue
            rot = path[i - len(path) // 2:] + path[:i - len(path) // 2]; c = len(path) // 2  # zig site in the middle (no seam)
            for w1 in range(1, 8):
              for w2 in range(1, 8):
                a, b = c - w1, c + w2
                new = PV.pixel_perfect(rot[:a] + PV.bres(rot[a], rot[b]) + rot[b + 1:])
                zn = path_zigs(new)
                if len(zn) < len(z) and (best is None or (len(zn), w1 + w2) < (len(best[0]), best[2])): best = (zn, new, w1 + w2)
        if best is None: break
        z, path = best[0], best[1]
    return path


def best_shift(a, b, r=3):
    best = (1 << 30, 0, 0)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            v = int((a ^ np.roll(np.roll(b, dy, 0), dx, 1)).sum())
            if v < best[0]: best = (v, dy, dx)
    return best[1], best[2]


def sh(a, d): return np.roll(np.roll(a, d[0], 0), d[1], 1)


def part_motion(prev_sub, prev_line, prev_band, cur_sub):
    """per sub-part integer motion (best shift of the part's cells, +-4 px) from the previous frame to this one; returns the
    previous line pixels per part moved by their part's shift (for the vertex hysteresis), the previous bands moved the same
    way (band hysteresis), and this frame's part grid (nearest part everywhere, to look up a vertex's part)."""
    near = lambda lab: lab[tuple(nd.distance_transform_edt(lab < 0, return_distances=False, return_indices=True))]
    pp = near(prev_sub); cp = near(cur_sub); by_part = {}; band = np.full((N, N), -1, np.int8)
    for k in range(len(SUB)):
        a, b = cur_sub == k, prev_sub == k
        if not a.any() or not b.any(): continue
        d = best_shift(a, b, r=4)
        by_part[k] = np.argwhere(sh(prev_line & (pp == k), d))
        mb = sh(b, d); band[mb] = sh(prev_band, d)[mb]
    return by_part, cp, band


# ------------------------------------------------------------------ C. colour
def ndl_cells(F, mat1):
    """per cell: mean N.L of the cell's own material pixels (N.L smoothed inside each material, NSIG px)"""
    v = (F['nrm'] * SUN).sum(-1); out = np.zeros((N, N))
    for k in range(len(MN)):
        m = (F['mid'] == k)
        if not m.any(): continue
        sg = NSIG[MN[k]] * P; num = nd.gaussian_filter(np.where(m, v, 0), sg); den = nd.gaussian_filter(m.astype(float), sg)
        vs = np.where(m, num / np.maximum(den, 1e-6), 0); bm = blocks(m); bv = blocks(vs)
        c = bm.sum(-1); s = (bv * bm).sum(-1); sel = mat1 == k
        out[sel] = np.where(c[sel] > 0, s[sel] / np.maximum(c[sel], 1), 0.3)
    return out


def colour(mat1, sub1, ndl, inside, prev_band=None):
    g = np.full((N, N), '.', dtype='<U1'); band = np.zeros((N, N), np.int8)  # 0 shadow 1 base
    for m, (dk, bk, t) in RAMP.items():
        sel = inside & (mat1 == MI[m])
        b = (ndl > t).astype(np.int8)
        if prev_band is not None:  # hysteresis: near the threshold keep last frame's band
            near = np.abs(ndl - t) < HYS; b = np.where(near & (prev_band >= 0), prev_band, b)
        band[sel] = b[sel]; g[sel & (b == 1)] = bk; g[sel & (b == 0)] = dk
    face = inside & (sub1 == SI['face']) & (mat1 == MI['skin']); g[face] = 's'; band[face] = 1
    neck = inside & (sub1 == SI['neck']) & (mat1 == MI['skin']); g[neck] = 'S'; band[neck] = 0
    hair = inside & (mat1 == MI['hair']) & (sub1 == SI['hair'])
    hl = hair & (ndl > HAIR_L); top = hl & ~np.roll(hl, 1, 0)  # one-pixel sheen: the top row of the brightest hair band
    lab, n = nd.label(top, np.ones((3, 3)))
    for k in range(1, n + 1):
        if (lab == k).sum() >= 2: g[lab == k] = 'L'
    band[~inside] = -1
    return g, band


# ------------------------------------------------------------------ D. interior lines at listed overlaps
def interior(F, sub1, inside, outline):
    """far-side 1 px K where a listed sub-part pair meets (cell level, depth from the 8x pass)"""
    bd = blocks(F['dep']); bs = blocks(F['sub'])
    dep1 = np.full((N, N, len(SUB)), np.inf)
    for k in range(len(SUB)):
        m = bs == k; c = m.sum(-1)
        dep1[..., k] = np.where(c > 0, np.where(m, bd, 0).sum(-1) / np.maximum(c, 1), np.inf)
    line = np.zeros((N, N), bool); kind = np.full((N, N), '', dtype=object)
    fillc = inside & ~outline
    for (a, b), nm in PAIRS.items():
        A = fillc & (sub1 == SI[a]); B = fillc & (sub1 == SI[b])
        for X, Y, xn, yn in ((A, B, a, b), (B, A, b, a)):
            nb = nd.binary_dilation(Y, CROSS) & X  # X cells 4-adjacent to Y
            for y, x in zip(*np.nonzero(nb)):
                if nm == 'bangs|face':
                    far = xn == 'hair'  # bangs edge drawn on the hair side (keeps the face width for the eyes)
                else:
                    ys, xs = slice(max(y - 1, 0), y + 2), slice(max(x - 1, 0), x + 2)
                    dx_ = dep1[y, x, SI[xn]]; dy_ = np.nanmin(np.where(Y[ys, xs], dep1[ys, xs, SI[yn]], np.inf))
                    far = np.isfinite(dx_) and np.isfinite(dy_) and dx_ > dy_ + (0.0 if nm in SAMEHULL else DSTEP)
                if far: line[y, x] = True; kind[y, x] = nm
    line = thin_pp(line)
    lab, n = nd.label(line, np.ones((3, 3)))
    for k in range(1, n + 1):
        if (lab == k).sum() < MINLEN: line[lab == k] = False
    kind[~line] = ''
    return line, kind


def thin_pp(m):
    """pixel-perfect: drop orthogonal elbows whose removal keeps the stroke 8-connected"""
    m = m.copy()
    for _ in range(3):
        p = np.pad(m, 1); n_, s_, w_, e_ = p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]
        ne, nw, se, sw = p[:-2, 2:], p[:-2, :-2], p[2:, 2:], p[2:, :-2]
        el = m & (((n_ & e_) & ~ne & ~s_ & ~w_) | ((e_ & s_) & ~se & ~n_ & ~w_) | ((s_ & w_) & ~sw & ~n_ & ~e_) | ((w_ & n_) & ~nw & ~s_ & ~e_))
        if not el.any(): break
        for y, x in zip(*np.nonzero(el)):
            if (y + x) % 2 == 0: m[y, x] = False
    return m


# ------------------------------------------------------------------ E. face
def stamp_eyes(g, sub1, inside, outline, F, fr, cal, prev_far, nxt_raw=None):
    """returns (ink mask, raw visibility per eye, final visibility per eye)"""
    ex = expr_of(fr); ink = np.zeros((N, N), bool); vis = {}
    for e in cal['eyes']:
        E_ = fr['eyes'][e['key']]; x, y = E_['px']; yy, xx = int(np.floor(y * P)), int(np.floor(x * P))
        occl = not (0 <= yy < N * P and 0 <= xx < N * P) or E_['facing'] < 0.05 or F['dep'][yy, xx] < E_['depth_m'] - 0.012
        X0 = int(np.floor(x + e['off_px'][0] + 0.5)); Y0 = int(np.floor(y + e['off_px'][1] + 0.5))
        rows = FS.eye(ex, e['side'], e['kind']); pts = [(Y0 + r, X0 + c, ch) for r, l in enumerate(rows) for c, ch in enumerate(l) if ch not in ' .']
        face = inside & ~outline & (sub1 == SI['face'])
        ok = [(r, c, ch) for r, c, ch in pts if 0 <= r < N and 0 <= c < N and face[r, c]]
        eyeink = [p for p in pts if p[2] != 'h']; eyeok = [p for p in ok if p[2] != 'h']
        show = (not occl) and eyeink and len(eyeok) >= 0.6 * len(eyeink)
        vis[e['key']] = dict(show=bool(show), pts=pts, ok=ok, frac=round(len(eyeok) / max(1, len(eyeink)), 2), occluded=bool(occl), X0=X0, Y0=Y0)
    return ex, vis


def apply_eyes(g, ink, vis, inside, outline):
    for k, v in vis.items():
        if not v['show']: continue
        for r, c, ch in v['ok']:
            g[r, c] = {'@': 'W'}.get(ch, ch); ink[r, c] = True
        for r, c, ch in v['pts']:  # brows show through the bangs: on hair they are K
            if ch == 'h' and 0 <= r < N and 0 <= c < N and inside[r, c] and not outline[r, c] and g[r, c] in 'HhL':
                g[r, c] = 'K'; ink[r, c] = True


# ------------------------------------------------------------------ F. cleanup (only removes K from interior lines)
def cleanup(g, outline, iline, ink, fillcol):
    """removes only K (never adds): 2x2 K clumps (interior-line px first) and redundant L-corners (a K elbow touching no fill
    4-wise; removed only if that does not add a 1-3-1 zigzag to the silhouette, lamet.run_defects). A removed px becomes
    background if it touches background, else the fill colour under it; never when that would put fill (or an interior line)
    next to background. Ink (eyes/brows) is kept. Interior-line pieces that fell under MINLEN px are dropped last."""
    def nbs(y, x): return [(yy, xx) for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))]
    def drop(y, x):
        nb = [(g[q] if (0 <= q[0] < N and 0 <= q[1] < N) else '.', q) for q in nbs(y, x)]
        has_bg = any(c == '.' for c, _ in nb)
        inner = [c for c, q in nb if c not in '.K' or (c == 'K' and 0 <= q[0] < N and 0 <= q[1] < N and ink[q])]
        if has_bg and inner: return False  # would open the outline
        if has_bg: g[y, x] = '.'
        elif fillcol[y, x] not in '.K': g[y, x] = fillcol[y, x]
        elif [c for c in inner if c != 'K']: g[y, x] = [c for c in inner if c != 'K'][0]
        else: return False
        iline[y, x] = False; outline[y, x] = False; return True
    zig = lambda: LM_run_defects(g != '.')[0]
    for _ in range(4):
        changed = False; K = (g == 'K') & ~ink
        c = K[:-1, :-1] & K[1:, :-1] & K[:-1, 1:] & K[1:, 1:]
        for y, x in zip(*np.nonzero(c)):
            q = [(yy, xx) for yy, xx in ((y, x), (y, x + 1), (y + 1, x), (y + 1, x + 1)) if g[yy, xx] == 'K' and not ink[yy, xx]]
            q.sort(key=lambda t: (not iline[t], t))
            for yy, xx in q:
                if drop(yy, xx): changed = True; break
        K = (g == 'K') & ~ink; fill = (g != '.') & (g != 'K')
        p = np.pad(g == 'K', 1); n_, s_, w_, e_ = p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]
        ne, nw, se, sw = p[:-2, 2:], p[:-2, :-2], p[2:, 2:], p[2:, :-2]
        el = K & ((n_ & e_ & ~s_ & ~w_ & ~ne) | (e_ & s_ & ~n_ & ~w_ & ~se) | (s_ & w_ & ~n_ & ~e_ & ~sw) | (w_ & n_ & ~s_ & ~e_ & ~nw))
        pf = np.pad(fill, 1); touch = pf[:-2, 1:-1] | pf[2:, 1:-1] | pf[1:-1, :-2] | pf[1:-1, 2:]
        z0 = zig()
        for y, x in sorted(zip(*np.nonzero(el & ~touch)), key=lambda t: (not iline[t], t)):
            if g[y, x] != 'K': continue
            save = (g[y, x], iline[y, x], outline[y, x])
            if drop(y, x):
                z1 = zig()
                if z1 > z0: g[y, x], iline[y, x], outline[y, x] = save
                else: z0 = z1; changed = True
        if not changed: break
    lab, n = nd.label(iline & (g == 'K'), np.ones((3, 3)))
    bgn = nd.binary_dilation(g == '.', CROSS)
    for k in range(1, n + 1):
        m = lab == k
        if m.sum() < MINLEN:
            for y, x in zip(*np.nonzero(m)):
                iline[y, x] = False
                if bgn[y, x]: outline[y, x] = True  # it became silhouette when an outline elbow was removed: keep as outline
                else: g[y, x] = fillcol[y, x]
    return g


def protect_limbs(iline, kind, sub1, inside, line):
    """an overlap line may not thin a limb below 2 px (P's rule): where the far-side line leaves a limb pixel outside every 2x2
    block, the line moves to the near side if that is plain body (torso/neck), else it is dropped there."""
    fill = inside & ~line
    for nm in LIMB_SUBS:
        k = SI[nm]
        for _ in range(3):
            L = fill & (sub1 == k) & ~iline
            if not L.any(): break
            core = nd.binary_opening(np.pad(L, 1), np.ones((2, 2)))[1:-1, 1:-1]; thin = L & ~nd.binary_dilation(core, CROSS)
            bad = iline & (sub1 == k) & nd.binary_dilation(thin, np.ones((3, 3)))
            if not bad.any(): break
            for y, x in zip(*np.nonzero(bad)):
                iline[y, x] = False; nm_ = kind[y, x]; kind[y, x] = ''
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= yy < N and 0 <= xx < N and fill[yy, xx] and sub1[yy, xx] in (SI['torso'], SI['neck']) and not iline[yy, xx]:
                        iline[yy, xx] = True; kind[yy, xx] = nm_
    iline = thin_pp(iline); lab, n = nd.label(iline, np.ones((3, 3)))
    for i in range(1, n + 1):
        if (lab == i).sum() < MINLEN: iline[lab == i] = False
    kind[~iline] = ''
    return iline, kind


LIMB_SUBS = ['leg.L', 'leg.R', 'arm.L', 'arm.R', 'hand.L', 'hand.R']


def limb_thin(g, sub1):
    fill = (g != '.') & (g != 'K'); t = 0
    for nm in LIMB_SUBS:
        L = fill & (sub1 == SI[nm])
        if L.any(): t += int((L & ~nd.binary_dilation(nd.binary_opening(np.pad(L, 1), np.ones((2, 2)))[1:-1, 1:-1], CROSS)).sum())
    return t


def defects(g, ink, sub1=None):
    """line-art defect score on the grid (eye ink masked): 1-3-1 zigzags, redundant L-corners, outline gaps, 2x2 K clumps"""
    gl = g.copy(); gl[ink] = 's'; op = gl != '.'; K = gl == 'K'
    zs = [p for k, p in LM_run_defects(op)[4] if k == 'zig']
    dbl = LM_doubles(gl); bg = ~op; p_ = np.pad(bg, 1); sil = op & (p_[:-2, 1:-1] | p_[2:, 1:-1] | p_[1:-1, :-2] | p_[1:-1, 2:])
    gap = int((sil & ~K).sum()); cl = int((K[:-1, :-1] & K[1:, :-1] & K[:-1, 1:] & K[1:, 1:]).sum())
    sites = [tuple(map(int, p)) for p in zs] + [tuple(map(int, p)) for p in zip(*np.nonzero(dbl))]
    lt = limb_thin(g, sub1) if sub1 is not None else 0
    return 3 * len(zs) + 2 * int(dbl.sum()) + 20 * gap + 20 * cl + 20 * lt, sites


def polish(g, line, iline, ink, mat1, sub1, it=30):
    """last line pass: local 1-px edits of the OUTLINE around each remaining zigzag / L-corner, kept only if the defect score
    drops (never creates a gap or clump): drop a K px, push the outline out by 1 px, or pull it in by 1 px."""
    score, sites = defects(g, ink, sub1)
    for _ in range(it):
        if not sites: break
        best = None
        for (sy, sx) in sites:
            for y in range(max(sy - 2, 1), min(sy + 3, N - 1)):
                for x in range(max(sx - 2, 1), min(sx + 3, N - 1)):
                    nb4 = ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)); cands = []
                    if g[y, x] == 'K' and line[y, x] and not ink[y, x]:
                        cands.append([((y, x), '.', -1)])  # drop
                        for q in nb4:  # pull in: K -> bg, the fill behind it -> K
                            if g[q] not in '.K' and not ink[q]: cands.append([((y, x), '.', -1), (q, 'K', -1)])
                    if g[y, x] == '.':
                        for q in nb4:  # push out: bg -> K, the K behind it -> the fill behind that
                            if g[q] == 'K' and line[q] and not ink[q]:
                                r = (2 * q[0] - y, 2 * q[1] - x)
                                if 0 <= r[0] < N and 0 <= r[1] < N and g[r] not in '.K': cands.append([((y, x), 'K', -1), (q, g[r], mat1[r], sub1[r])])
                    for c in cands:
                        old = [(e[0], g[e[0]], mat1[e[0]], sub1[e[0]]) for e in c]
                        for e in c:
                            g[e[0]] = e[1]
                            if e[2] >= 0: mat1[e[0]] = e[2]
                            if len(e) > 3: sub1[e[0]] = e[3]
                        sc, st = defects(g, ink, sub1)
                        for pq, v, m, sb in old: g[pq] = v; mat1[pq] = m; sub1[pq] = sb
                        if sc < score and (best is None or sc < best[0]): best = (sc, c, st)
        if best is None: break
        score, c, sites = best
        for e in c:
            pq, v = e[0], e[1]; g[pq] = v
            if e[2] >= 0: mat1[pq] = e[2]
            if len(e) > 3: sub1[pq] = e[3]
            line[pq] = v == 'K'; iline[pq] = False
    return g


SPECK = 6


def limb_specks(sub1, mat1, inside, line):
    """P's speck rule: limb pieces other than the limb's largest that are smaller than SPECK cells (vote noise where two legs
    overlap, a 1-cell arm crumb) take the label + material of their most common 4-neighbour."""
    fill = inside & ~line
    for nm in LIMB_SUBS:
        k = SI[nm]; lab, n = nd.label(fill & (sub1 == k), np.ones((3, 3)))
        if n < 2: continue
        sz = nd.sum(np.ones_like(lab), lab, range(1, n + 1)); big = int(np.argmax(sz)) + 1
        for c in range(1, n + 1):
            if c == big or sz[c - 1] >= SPECK: continue
            m = lab == c; ring = nd.binary_dilation(m, CROSS) & fill & ~m & (sub1 != k)
            if not ring.any(): continue
            vals, cnts = np.unique(sub1[ring], return_counts=True); t = int(vals[cnts.argmax()])
            mv, mc = np.unique(mat1[ring & (sub1 == t)], return_counts=True)
            sub1[m] = t; mat1[m] = int(mv[mc.argmax()])
    return sub1, mat1


def limb_tips(g, sub1, mat1, inside, line, iline, ink):
    """last limb rule (P: 'a final width repair turns limb slivers into outline, only while the limb keeps a core'): a limb fill
    px that is still outside every 2x2 block of its limb and touches the outline becomes outline K."""
    for nm in LIMB_SUBS:
        k = SI[nm]
        L = inside & (sub1 == k) & (g != 'K')
        core = nd.binary_opening(np.pad(L, 1), np.ones((2, 2)))[1:-1, 1:-1]
        if not core.any(): continue
        thin = L & ~nd.binary_dilation(core, CROSS) & ~ink; edge = thin & nd.binary_dilation(line, CROSS)
        g[edge] = 'K'; line |= edge
        for y, x in zip(*np.nonzero(thin & ~edge)):  # inner crumb: take the colour + label of the most common non-limb neighbour
            nb = [(yy, xx) for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if inside[yy, xx] and g[yy, xx] != 'K' and sub1[yy, xx] != k]
            if nb:
                c = max(set(g[q] for q in nb), key=[g[q] for q in nb].count); q = next(q for q in nb if g[q] == c); g[y, x] = c; sub1[y, x] = sub1[q]; mat1[y, x] = mat1[q]
    return g


def limb_repair(sub1, mat1, inside, line):
    """P's 2 px limb guarantee on the label grid: a limb pixel outside every 2x2 block of its limb grows the 2x2 block that needs
    the fewest relabels (only plain body cells: torso/neck, never another limb, face, hair or bow); the grown cells take the
    limb's material. Runs before colour and interior lines, so both follow the repaired labels."""
    fill = inside & ~line; grow_ok = np.isin(sub1, [SI['torso'], SI['neck']])
    for nm in LIMB_SUBS:
        k = SI[nm]
        for _ in range(4):
            L = fill & (sub1 == k)
            if not L.any(): break
            core = nd.binary_opening(np.pad(L, 1), np.ones((2, 2)))[1:-1, 1:-1]; thin = L & ~nd.binary_dilation(core, CROSS)
            if not thin.any(): break
            vals, cnts = np.unique(mat1[L], return_counts=True); m = int(vals[cnts.argmax()])
            done = False
            for y, x in zip(*np.nonzero(thin)):
                best = None
                for oy in (-1, 0):
                    for ox in (-1, 0):
                        cells = [(y + oy + a, x + ox + b) for a in (0, 1) for b in (0, 1)]
                        if not all(0 <= c[0] < N and 0 <= c[1] < N and fill[c] for c in cells): continue
                        need = [c for c in cells if sub1[c] != k]
                        if all(grow_ok[c] for c in need) and (best is None or len(need) < len(best)): best = need
                if best:
                    for c in best: sub1[c] = k; mat1[c] = m; grow_ok[c] = False
                    done = True
            if not done: break
    return sub1, mat1


# ------------------------------------------------------------------ driver
def frame(F, fr, cal, st):
    line, inside, snap = trace(nd.binary_erosion(F['alpha'], iterations=SHRINK), st.get('prev_line_al'))
    mat1 = fill_nearest(vote(F['mid'], F['alpha'], len(MN)), inside)
    sub1 = vote_given(F['sub'], F['mid'], F['alpha'], mat1, len(SUB))  # sub-part among the pixels of the cell's own material
    sub1 = np.where((sub1 >= 0) & inside, sub1, -1); sub1 = fill_nearest(sub1, inside)
    sub1, mat1 = limb_specks(sub1, mat1, inside, line)
    sub1, mat1 = limb_repair(sub1, mat1, inside, line)
    ndl = ndl_cells(F, mat1)
    g, band = colour(mat1, sub1, ndl, inside, st.get('prev_band_al'))
    fillcol = g.copy()
    iline, kind = interior(F, sub1, inside, line)
    iline, kind = protect_limbs(iline, kind, sub1, inside, line)
    g[iline] = 'K'
    g[line] = 'K'
    ink = np.zeros((N, N), bool)
    ex, vis = stamp_eyes(g, sub1, inside, line, F, fr, cal, None)
    return dict(g=g, line=line, inside=inside, mat1=mat1, sub1=sub1, band=band, fillcol=fillcol, iline=iline, kind=kind, ink=ink, ex=ex, vis=vis, snap=snap)


def run(jp, outd):
    info = json.load(open(jp)); stem = jp[:-5]; al_ = info['align']; frs = info['frames']; n = len(frs)
    cal = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'face_calib.json')))
    Fs = [load(stem, f['i'], al_) for f in frs]
    R = [None] * n; st = {}
    for it in range(2):  # loop twice: frame 0 sees frame n-1 (temporal line + band hysteresis)
        for i in range(n):
            if R[i - 1] is not None:
                pr = R[i - 1]; cur_sub = vote(Fs[i]['sub'], Fs[i]['alpha'], len(SUB))
                by_part, cp, band = part_motion(pr['sub1'], pr['line'], pr['band'], cur_sub)
                st = {'prev_line_al': (by_part, cp), 'prev_band_al': band}
            R[i] = frame(Fs[i], frs[i], cal, st)
    # E. far-eye 2-frame hysteresis (cyclic): a visibility change must persist 2 frames, else the previous state is kept
    far = [e['key'] for e in cal['eyes'] if e['kind'] == 'far']
    for k in far:
        raw = [R[i]['vis'][k]['show'] for i in range(n)]; out = raw[:]
        for _ in range(2):
            for i in range(n):
                if raw[i] != out[i - 1] and raw[(i + 1) % n] != raw[i]: out[i] = out[i - 1]
        for i in range(n):
            R[i]['vis'][k]['raw'] = raw[i]; R[i]['vis'][k]['show'] = out[i]
            if out[i] and not R[i]['vis'][k]['ok']: R[i]['vis'][k]['show'] = False
    os.makedirs(outd, exist_ok=True); rec = []
    for i, r in enumerate(R):
        apply_eyes(r['g'], r['ink'], r['vis'], r['inside'], r['line'])
        r['g'] = limb_tips(r['g'], r['sub1'], r['mat1'], r['inside'], r['line'], r['iline'], r['ink'])
        r['g'] = cleanup(r['g'], r['line'], r['iline'], r['ink'], r['fillcol'])
        r['g'] = polish(r['g'], r['line'], r['iline'], r['ink'], r['mat1'], r['sub1'])
        g = r['g']; open(os.path.join(outd, f'f{i:02d}.txt'), 'w').write('\n'.join(''.join(row) for row in g) + '\n')
        a = np.zeros((N, N, 4), np.uint8)
        for k, c in PAL.items(): a[g == k, :3] = c
        a[g != '.', 3] = 255; Image.fromarray(a).save(os.path.join(outd, f'f{i:02d}.png'))
        rec.append({'f': i, 'expr': r['ex'], 'snapped_vertices': r['snap'][0], 'vertices': r['snap'][1],
                    'eyes': {k: {kk: v[kk] for kk in ('show', 'frac', 'occluded', 'X0', 'Y0') if kk in v} | ({'raw': v['raw']} if 'raw' in v else {}) for k, v in r['vis'].items()},
                    'interior_px': {nm: int((r['kind'] == nm).sum()) for nm in sorted(set(PAIRS.values()))}})
    np.savez_compressed(os.path.join(outd, 'labels.npz'), **{f'{k}{i:02d}': R[i][k] for i in range(n) for k in ('mat1', 'sub1', 'line', 'iline', 'ink')},
                        **{f'kind{i:02d}': R[i]['kind'].astype(str) for i in range(n)})
    json.dump({'frames': rec, 'ms': [f['ms'] for f in frs], 'keys': [f['key'] for f in frs]}, open(os.path.join(outd, 'chain.json'), 'w'), indent=1)
    return R, Fs, info


if __name__ == '__main__':
    R, _, _ = run(sys.argv[1], sys.argv[2])
    print('LOCK_CHAIN', len(R), 'frames ->', sys.argv[2])
