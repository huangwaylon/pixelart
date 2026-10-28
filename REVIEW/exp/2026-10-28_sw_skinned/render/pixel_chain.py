"""pixel_chain.py STEM.json [--stamp] [--no-temporal] [--no-protect] [--no-sep]   (pixtools venv)   -- P's round-2 pixel step.
Called by R's render_motion.py (post stage) or directly.  Inputs per frame (192 cell at 8x): <stem>_fNN_{guide,lum,dep}.png from R, plus the
part-ID pass <dir>/parts/<stem>_fNN_part.png (render/p_parts.py; rendered automatically through Blender if missing).

Material/ID-driven downscale (replaces E2 k-centroid -> palette lock -> fix):
 1. segments = (material from matid) x (part from the part pass: torso head skirt leg.L leg.R arm.L arm.R sleeve.L sleeve.R).
 2. fill = cells whose coverage of the silhouette eroded by ERODE hi-res px is >= .5 (the 1 px outline is later drawn OUTSIDE the fill,
    so thin parts are not eaten by their own outline); label = coverage vote x limb weight x nearest-depth bonus.
 3. limb protection: legs and hands -> hi-res skeleton cells are forced to the limb, then every limb pixel must sit in a 2x2 block of the
    same limb (grown toward the block with the most hi-res limb coverage) => min 2 px fill, legs never vanish.
 4. silhouette clean (1 px spikes/notches, not on limbs) -> outline = 4-dilation of the fill, pixel-perfect (L corners removed).
 5. interior lines: leg.L|leg.R and arm/sleeve|body overlaps get a 1 px K on the FAR side (depth); if that would thin a limb below 2 px,
    the far limb is shaded one step darker instead.  hair|face and hand|sleeve keep lines; hem|skin band gets the skin shadow S.
 6. shading: per-segment smoothed lum -> 3 bands on the locked palette ramps; socks D with a lit d stripe (near leg only), red sock-top band,
    skin band (S under the hem); the far leg is one shade darker.
 7. temporal: per-part integer motion (best shift of the previous part mask) -> warped previous frame; hysteresis on fill coverage
    (.3/.7), on the label (keep previous unless beaten by 25 %) and on shade bands (margin HYS); cells whose hi-res block did not change
    copy the previous output; isolated 1-frame shade flips (a==c!=b within one material class) are removed.  Loops are run twice so f0
    sees the end of the cycle.
Outputs (as before): <stem>_px/fNN.{txt,png,json}, <stem>_4x.gif (mid-grey), <stem>_sheet.png, <stem>_px.json; --stamp also *_hs."""
import sys, os, json, subprocess, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from skimage.morphology import skeletonize
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hx  # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
P, N, OFF = 8, 128, 256
BG = (110, 110, 110)
ERODE = int(os.environ.get('ERODE', '6'))        # hi-res px the fill is eroded by before the outline goes outside (8 = exactly 1 px)
ERODE_LEG = int(os.environ.get('ERODE_LEG', '9'))  # legs are eroded more (the outline outside restores the silhouette)
DTHR = float(os.environ.get('DTHR', '0.03'))     # depth step for overlap lines (dep units, as hx)
HYS = float(os.environ.get('HYS', '0.08'))
RPTOL = float(os.environ.get('RPTOL', '0.02'))  # rest-space match tolerance (mesh units ~ m)
LOCK = float(os.environ.get('LOCK', '0.12'))  # surface-lock lum tolerance (0 = off)
HOLDT = float(os.environ.get('HOLDT', '0.3'))  # head hold threshold (fraction of head cells that differ)
TEX = os.environ.get('TEX', '1') == '1'  # use R's projected master head pass when present
FAMB = float(os.environ.get('FAMB', '0.2'))    # fill hysteresis half-band around .5 coverage
LKEEP = float(os.environ.get('LKEEP', '0.75'))  # keep the previous label if its score >= LKEEP x best
OBILINE = os.environ.get('OBILINE', '0') == '1'  # K line on the far side of obi|dress edges (master has them)
PROTECT_ARMS = os.environ.get('PROTECT_ARMS', '1') == '1'  # round 3: arms (sleeve tube + bag) get the 2 px guarantee too
SPECK = int(os.environ.get('SPECK', '6'))  # limb crumbs smaller than this, detached from the limb's main piece, are relabelled
RIM = os.environ.get('RIM', 'g')  # near-leg rim tone along the leg|leg separation (d = sock sheen; g = boot light, stronger)
SMOOTH = os.environ.get('SMOOTH', '1') == '1'
HOLE = int(os.environ.get('HOLE', '4'))  # enclosed background holes up to this many px are filled
MINRUN = int(os.environ.get('MINRUN', '3'))
HOLD = float(os.environ.get('HOLD', '0.15'))  # part-hold mismatch threshold (0 = off)
LSIG = float(os.environ.get('LSIG', '10'))  # hi-res lum smoothing inside a segment (8 = 1 sprite px)       # shade-band hysteresis margin (lum units)
SHEEN = float(os.environ.get('SHEEN', '0.42'))   # sock lit-stripe lum threshold
MAST = hx.SW + 'v2/m96/masters/EC0_{}_96.txt'
MN = hx.MN; NM = len(MN); MI = {n: i for i, n in enumerate(MN)}
PARTS = ["torso", "head", "skirt", "leg.L", "leg.R", "arm.L", "arm.R", "sleeve.L", "sleeve.R"]; NP = len(PARTS); PI = {p: i for i, p in enumerate(PARTS)}
PCOL = np.array([((i + 1) * 25, 255 - (i + 1) * 25, (i * 67) % 256) for i in range(NP)], float) / 255
PCOL = np.where(PCOL <= 0.0031308, PCOL * 12.92, 1.055 * PCOL ** (1 / 2.4) - 0.055) * 255  # the byte attribute is read as linear -> sRGB out
NS = NM * NP
BODY = {'torso': 0, 'skirt': 0, 'head': 1, 'leg.L': 2, 'leg.R': 3, 'arm.L': 4, 'sleeve.L': 4, 'arm.R': 5, 'sleeve.R': 5}
SEG_M = np.arange(NS) // NP; SEG_P = np.arange(NS) % NP
LEG = (PI['leg.L'], PI['leg.R'])
CROSS = nd.generate_binary_structure(2, 1)
HOLD_GROUPS = [[PI[g] for g in grp.split('+')] for grp in os.environ.get('HOLDG', 'head').split(',') if grp]


def seg(m, p): return m * NP + p


# ------------------------------------------------------------------ io
def gif(ims, durs, path):
    from gifio import write_gif  # shared experiment GIF writer: loop=0, >= 20 ms, 10 ms-quantised with error diffusion, disposal 2, global palette
    write_gif(path, ims, durs)


def sheet(ims, path, labels=None, cols=None):
    cols = cols or len(ims); w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
    S = Image.new('RGB', (w * cols, (h + 14) * rows), (40, 40, 44)); d = ImageDraw.Draw(S)
    for i, im in enumerate(ims):
        x, y = (i % cols) * w, (i // cols) * (h + 14); S.paste(im.convert('RGB'), (x, y + 14))
        if labels: d.text((x + 3, y + 1), labels[i], fill=(230, 230, 120))
    S.save(path)


def crop(a, dx, dy): return hx.shift(a[OFF:OFF + N * P, OFF:OFF + N * P], dx, dy)


def nearest(rgb, pal):
    d = ((rgb[..., None, :] - pal[None, None]) ** 2).sum(-1); return d.argmin(-1)


def load(stem, i, dx, dy, pdir):
    st = f'{stem}_f{i:02d}_'
    g = crop(hx.rd16(st + 'guide.png'), dx, dy); al = g[..., 3] > 0.5
    F = {'alpha': al, 'lum': crop(hx.rd16(st + 'lum.png'), dx, dy)[..., 0], 'dep': crop(hx.rd16(st + 'dep.png'), dx, dy)[..., 0]}
    mid = nearest(g[..., :3] * 255, hx.MC); mid[~al] = -1; F['mid'] = mid
    pp = os.path.join(pdir, os.path.basename(stem) + f'_f{i:02d}_part.png')
    bj = os.path.join(pdir, 'bones.json')
    if os.path.exists(pp) and os.path.exists(bj):
        B = json.load(open(bj)); nb = len(B['bones'])
        bc = np.array([(4 * k + 2, 253 - 4 * k, (37 * k) % 256) for k in range(nb)], float) / 255
        bc = np.where(bc <= 0.0031308, bc * 12.92, 1.055 * bc ** (1 / 2.4) - 0.055) * 255
        pa = crop(hx.rd16(pp), dx, dy); bone = nearest(pa[..., :3] * 255, bc)
        part = np.array([PI[B['parts'][n]] for n in B['bones']])[bone]; F['bone'] = np.where(al, bone, -1); F['nb'] = nb
        F['part_ok'] = float((((pa[..., 3] > 0.5) ^ al).sum()) / max(1, al.sum())) < 0.01
    else:
        part = np.zeros_like(mid); F['part_ok'] = False
    if 'bone' not in F: F['bone'] = np.where(al, part, -1); F['nb'] = NP
    if not F['part_ok']: part[:] = PI['torso']; part[np.isin(mid, [MI['socks'], MI['boots']])] = LEG[0]  # fallback: one leg part
    rp_ = os.path.join(pdir, os.path.basename(stem) + f'_f{i:02d}_rpos.png'); rj = os.path.join(pdir, 'rpos.json')
    if os.path.exists(rp_) and os.path.exists(rj):
        R_ = json.load(open(rj)); lo, hi = np.array(R_['lo']), np.array(R_['hi'])
        rp = crop(hx.rd16(rp_), dx, dy)[..., :3] * (hi - lo) + lo
        w = hx.cells(al.astype(float)).sum((2, 3))
        F['rpos'] = np.stack([hx.cells(rp[..., k] * al).sum((2, 3)) for k in range(3)], -1) / np.maximum(w, 1)[..., None]
        F['rpos_ok'] = w > 0
    tp = f'{stem}_f{i:02d}_tex.png'
    if os.path.exists(tp) and TEX:
        F['tex'] = crop(hx.rd16(tp), dx, dy)
    # skirt cloth weighted to the thighs (hem ring) is skirt, not leg: leg = skin band, sock band, socks, boots only
    part[np.isin(part, LEG) & np.isin(mid, [MI['dress'], MI['sleeve'], MI['obi']])] = PI['skirt']
    part[~al] = -1; F['part'] = part
    F['sid'] = np.where(al, mid * NP + part, -1)
    return F


def ensure_parts(stem, info, pdir):
    fs = [os.path.join(pdir, os.path.basename(stem) + f"_f{f['i']:02d}_part.png") for f in info['frames']]
    if all(os.path.exists(f) for f in fs): return
    act = info['action']
    mot = next((m for m in (f'{EXP}/motion/{act}.json', f'{HERE}/{act}.json') if os.path.exists(m)), None)
    if mot is None: print('WARN no motion file for part pass', act); return
    os.makedirs(pdir, exist_ok=True)
    yaw = info.get('yaw'); ex = [f'--yaw={yaw}'] if yaw is not None else []
    i0, i1 = info['frames'][0]['i'], info['frames'][-1]['i'] + 1
    cmd = ['/Applications/Blender.app/Contents/MacOS/Blender', '-b', f'{EXP}/rig/rig.blend', '-P', f'{HERE}/p_parts.py', '--', mot, info['view'], pdir,
           f'--frames={i0}:{i1}'] + ex
    r = subprocess.run(cmd, capture_output=True, text=True); print('parts:', [l for l in r.stdout.splitlines() if 'PARTS_DONE' in l or 'rror' in l][:3])


def feet(a):
    ys = np.where(a.any(1))[0]; yb = ys.max(); xs = np.where(a[yb - 4:yb + 1].any(0))[0]; return yb, (xs.min() + xs.max()) / 2


def align(stem, view):
    aj = f'{EXP}/rig/align.json'  # R's fixed per-view alignment (same rule, also used for the head texture projection)
    if os.path.exists(aj) and view in json.load(open(aj)): v = json.load(open(aj))[view]; return {'dx': int(v['dx']), 'dy': int(v['dy'])}
    g = hx.rd16(f'{stem}_rest_guide.png')[OFF:OFF + N * P, OFF:OFF + N * P]; a = hx.cells((g[..., 3] > 0.5).astype(float)).mean((2, 3)) > 0.5
    m = hx.read_grid(MAST.format(view)) != '.'
    yb, xc = feet(a); mb, mc = feet(m); return {'dx': int(round(mc - xc)), 'dy': int(mb - yb)}


# ------------------------------------------------------------------ per-cell statistics
def cellidx():
    y, x = np.mgrid[0:N * P, 0:N * P]; return (y // P) * N + (x // P)


CI = cellidx()


def stats(F):
    sid = F['sid']; m = sid >= 0; ci = CI[m]; s = sid[m]; key = ci * NS + s
    cnt = np.bincount(key, minlength=N * N * NS).reshape(N, N, NS) / (P * P)
    dsum = np.bincount(key, weights=F['dep'][m], minlength=N * N * NS).reshape(N, N, NS)
    # per-segment smoothed lum (normalised convolution inside each segment: no bleed across materials/parts)
    Ls = np.zeros(sid.shape)
    for k in np.unique(s):
        mk = (sid == k).astype(float); num = nd.gaussian_filter(F['lum'] * mk, LSIG); den = nd.gaussian_filter(mk, LSIG)
        Ls[sid == k] = (num / np.maximum(den, 1e-6))[sid == k]
    lsum = np.bincount(key, weights=Ls[m], minlength=N * N * NS).reshape(N, N, NS)
    with np.errstate(all='ignore'):
        dep = np.where(cnt > 0, dsum / (cnt * P * P), np.inf); lum = np.where(cnt > 0, lsum / (cnt * P * P), 0)
    er = nd.binary_erosion(F['alpha'], iterations=ERODE) if ERODE > 0 else F['alpha']
    if ERODE_LEG > ERODE:  # slimmer legs (chibi master proportions); the 2 px limb guarantee still applies
        legm = np.isin(F['part'], LEG); er &= ~(legm & ~nd.binary_erosion(F['alpha'], iterations=ERODE_LEG))
    ecov = hx.cells(er.astype(float)).mean((2, 3))
    # per-part coverage
    pc = np.zeros((N, N, NP))
    for p in range(NP): pc[..., p] = cnt[..., SEG_P == p].sum(-1)
    b = F['bone'][m]; nb = F['nb']
    bcov = np.bincount(ci * nb + b, minlength=N * N * nb).reshape(N, N, nb) / (P * P)
    return {'cnt': cnt, 'dep': dep, 'lum': lum, 'ecov': ecov, 'pcov': pc, 'bcov': bcov}


def limb_masks(F):
    """hi-res masks of the protected limbs: legs (whole part) and hands (skin of the arm parts)"""
    out = {}
    for q in LEG: out[q] = F['part'] == q
    for s, q in (('L', PI['arm.L']), ('R', PI['arm.R'])): out[100 + q] = (F['part'] == q) & (F['mid'] == MI['skin'])
    if PROTECT_ARMS:
        for s in 'LR':  # arm = upper arm / forearm cloth + sleeve bag (not the hand)
            q = PI['arm.' + s]; out[200 + q] = np.isin(F['part'], [q, PI['sleeve.' + s]]) & (F['mid'] != MI['skin']) & (F['mid'] >= 0)
    return out


ARMQ = {PI['arm.L']: PI['sleeve.L'], PI['arm.R']: PI['sleeve.R']}


def limb_of_seg(k):
    p = SEG_P[k]; m = SEG_M[k]
    if p in LEG: return p
    if p in (PI['arm.L'], PI['arm.R']) and m == MI['skin']: return 100 + p
    if PROTECT_ARMS:
        for a_, sl_ in ARMQ.items():
            if p in (a_, sl_): return 200 + a_
    return None


def limb_cells(lab, q):
    if q < 100: return (lab >= 0) & np.isin(SEG_P[np.maximum(lab, 0)], [q])
    if q >= 200: return (lab >= 0) & np.isin(SEG_P[np.maximum(lab, 0)], [q - 200, ARMQ[q - 200]]) & (SEG_M[np.maximum(lab, 0)] != MI['skin'])
    return (lab >= 0) & (SEG_P[np.maximum(lab, 0)] == q - 100) & (SEG_M[np.maximum(lab, 0)] == MI['skin'])


def limb_segs(q):
    return [k for k in range(NS) if limb_of_seg(k) == q]


def LIMBQ():
    return [*LEG, 100 + PI['arm.L'], 100 + PI['arm.R']] + ([200 + PI['arm.L'], 200 + PI['arm.R']] if PROTECT_ARMS else [])


KEYS = hx.KEYS; PALRGB = np.array(hx.RGB, float)


def tex_cells(tex):
    """R's projected master head: find the texel phase (master pixels are ~8x8 hi-res blocks), roll it onto the sprite grid, then the
    per-cell mode of the exact palette colours (coverage >= .5).  Returns (mask, char grid)."""
    al = tex[..., 3] > 0.5; rgb = tex[..., :3] * 255
    pid = nearest(rgb, PALRGB); pid[~al] = -1
    ph = []
    for ax in (1, 0):
        a = np.moveaxis(pid, ax, 1); ch = (a[:, 1:] != a[:, :-1]) & (a[:, 1:] >= 0) & (a[:, :-1] >= 0)
        pos = (np.nonzero(ch)[1] + 1) % P; hst = np.bincount(pos, minlength=P); ph.append(int(hst.argmax()) if hst.sum() > 50 else 0)
    phx, phy = ph
    phx = phx - P if phx > P // 2 else phx; phy = phy - P if phy > P // 2 else phy
    pid = np.roll(np.roll(pid, -phy, 0), -phx, 1)
    m = pid >= 0; key = CI[m] * len(KEYS) + pid[m]
    cnt = np.bincount(key, minlength=N * N * len(KEYS)).reshape(N, N, len(KEYS))
    cov = cnt.sum(-1) / (P * P); T = cov >= 0.5
    g = np.array(KEYS)[cnt.argmax(-1)]; g[~T] = '.'
    return T, g


def mat_major(F, T):
    c = hx.cells(F['mid']).reshape(N, N, P * P); out = np.full((N, N), MI['hair'])
    for y, x in zip(*np.nonzero(T)):
        v = c[y, x][c[y, x] >= 0]
        if len(v): out[y, x] = np.bincount(v).argmax()
    return out


# ------------------------------------------------------------------ temporal helpers
def best_shift(prev_mask, cov, r=3):
    if prev_mask is None or not prev_mask.any() or cov.sum() == 0: return (0, 0)
    best, bs = -1, (0, 0)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            v = (cov * np.roll(np.roll(prev_mask, dy, 0), dx, 1)).sum() - 1e-3 * (abs(dx) + abs(dy))
            if v > best: best, bs = v, (dy, dx)
    return bs


def warp(a, s, fill):
    b = np.roll(np.roll(a, s[0], 0), s[1], 1); return b


# ------------------------------------------------------------------ one frame
def frame(F, prev, opt):
    S = stats(F); cnt, dep, ecov, pcov = S['cnt'], S['dep'], S['ecov'], S['pcov']
    tot = cnt.sum(-1)
    dom_p = pcov.argmax(-1)
    # previous frame warped per part (integer motion of each part)
    W = None
    bcov = S['bcov']; dom_b = bcov.argmax(-1)
    if prev is not None and opt['temporal'] and 'rpos' in F and 'rpos' in prev:
        # exact surface correspondence: each cell -> the previous cell showing the same rest-pose surface point (same dominant bone)
        from scipy.spatial import cKDTree
        pm = prev['rpos_ok']; py, px = np.nonzero(pm)
        key = lambda rp, b: np.concatenate([rp, (b[..., None] * 10.0)], -1)
        tree = cKDTree(key(prev['rpos'][pm], prev['dom_b'][pm]))
        cy, cx = np.nonzero(F['rpos_ok'])
        dist, j = tree.query(key(F['rpos'][cy, cx], dom_b[cy, cx]), distance_upper_bound=RPTOL)
        ok = np.isfinite(dist); W = {k: np.full((N, N), -1) for k in ('lab', 'band')}; W['fill'] = np.zeros((N, N), bool)
        W['valid'] = np.zeros((N, N), bool); W['src'] = np.full((N, N, 2), -1)
        for k in ('lab', 'band', 'fill'): W[k][cy[ok], cx[ok]] = prev[k][py[j[ok]], px[j[ok]]]
        W['valid'][cy[ok], cx[ok]] = True; W['src'][cy[ok], cx[ok]] = np.stack([py[j[ok]], px[j[ok]]], -1)
    elif prev is not None and opt['temporal']:
        pres = [b for b in range(bcov.shape[-1]) if bcov[..., b].sum() > 0.5]
        sh = {b: best_shift(prev['bmask'] == b, bcov[..., b]) for b in pres}
        W = {k: prev[k].copy() for k in ('lab', 'band', 'fill')}
        for b in pres:
            sel = dom_b == b
            for k in ('lab', 'band', 'fill'):
                W[k][sel] = np.roll(np.roll(prev[k], sh[b][0], 0), sh[b][1], 1)[sel]
        W['valid'] = np.ones((N, N), bool)
    # ---- fill + label vote
    fill = ecov >= 0.5
    if W is not None:
        amb = (ecov >= 0.5 - FAMB) & (ecov < 0.5 + FAMB) & W['valid']; fill = np.where(amb, W['fill'], fill)
    fill &= tot > 0.15
    wt = np.ones(NS); wt[[k for k in range(NS) if limb_of_seg(k) is not None]] = 1.25
    sc = cnt * wt
    near = np.argmin(np.where(cnt >= 0.2, dep, np.inf), -1)
    sc[np.arange(N)[:, None], np.arange(N)[None], near] *= 1.3
    lab = sc.argmax(-1)
    if W is not None:
        pl = W['lab']; ok = pl >= 0
        psc = np.take_along_axis(sc, np.maximum(pl, 0)[..., None], -1)[..., 0]
        keep = ok & (psc >= LKEEP * sc.max(-1)) & (psc > 0)
        lab = np.where(keep, pl, lab)
    lab = np.where(fill, lab, -1)
    # ---- projected master head (R's tex pass): texel-phase aligned, per-cell mode of exact master colours
    T = np.zeros((N, N), bool); texg = None
    if 'tex' in F:
        T, texg = tex_cells(F['tex'])
        headp = (lab >= 0) & (SEG_P[np.maximum(lab, 0)] == PI['head'])
        lab[headp & ~T] = -1
        hm = mat_major(F, T)
        lab[T] = seg(1, PI['head']) * 0 + hm[T] * NP + PI['head']
        fill = lab >= 0
    # ---- part hold: a rigid-ish group (head incl. hair/bow) whose sprite-level shape differs from the integer-shifted previous frame by
    # less than HOLD of its area keeps the previous shape + bands (motion below ~1 px is held, not redrawn)
    held = np.zeros((N, N), bool); held_band = None
    if prev is not None and opt['temporal'] and HOLD > 0:
        for gp in HOLD_GROUPS:
            cur = (lab >= 0) & np.isin(SEG_P[np.maximum(lab, 0)], gp)
            pg = (prev['lab'] >= 0) & np.isin(SEG_P[np.maximum(prev['lab'], 0)], gp)
            if not cur.any() or not pg.any(): continue
            s_ = best_shift(pg, pcov[..., gp].sum(-1), r=4)
            wl = np.roll(np.roll(prev['lab'], s_[0], 0), s_[1], 1); wb = np.roll(np.roll(prev['band'], s_[0], 0), s_[1], 1)
            wg = np.roll(np.roll(pg, s_[0], 0), s_[1], 1)
            U = cur | wg; mis = ((wl != lab) & U).sum() / max(1, U.sum())
            if mis < HOLD:
                # held region = the shifted previous group; cells the group left take the current non-group label
                lab = np.where(wg, wl, np.where(cur, -1 if False else lab, lab))
                lab[cur & ~wg] = np.where(np.isin(SEG_P[np.maximum(wl[cur & ~wg], 0)], gp), -1, wl[cur & ~wg])
                held |= wg; held_band = wb if held_band is None else np.where(wg, wb, held_band)
        fill = lab >= 0
    locked = np.zeros((N, N), bool)
    # ---- limb protection
    if opt['protect']:
        LM = limb_masks(F); skc = {}
        for q, mk in LM.items():
            ml, mn = nd.label(mk)  # hi-res slivers under ~1.5 sprite px are not limbs to protect
            if mn: mk = np.isin(ml, [k for k in range(1, mn + 1) if (ml == k).sum() >= 1.5 * P * P])
            if mk.sum() < 20: continue
            sk = skeletonize(mk); skc[q] = hx.cells(sk.astype(float)).sum((2, 3)) > 0
        # skeleton cells: nearest limb wins
        order = sorted(skc, key=lambda q: -np.nanmean(np.where(LM[q], F['dep'], np.nan)))  # far first, near overwrites
        for q in order:
            ss = limb_segs(q); c = skc[q]
            bestq = np.array(ss)[cnt[..., ss].argmax(-1)]
            set_ = c & ~(locked & ~limb_cells(lab, q))
            lab = np.where(set_, np.where(np.take_along_axis(cnt, bestq[..., None], -1)[..., 0] > 0, bestq, lab), lab)
            lab = np.where(set_ & (lab < 0), bestq, lab)
            locked |= set_
        for _ in range(2):
            for q in skc:
                ss = limb_segs(q); R = limb_cells(lab, q)
                if not R.any(): continue
                qc = cnt[..., ss].sum(-1); bestq = np.array(ss)[cnt[..., ss].argmax(-1)]
                ok = R & nd.binary_opening(R, np.ones((2, 2)))
                for y, x in zip(*np.nonzero(R & ~ok)):
                    best, blk = -1, None
                    for oy in (-1, 0):
                        for ox in (-1, 0):
                            ys, xs = y + oy, x + ox
                            if ys < 0 or xs < 0 or ys + 2 > N or xs + 2 > N: continue
                            cells = [(ys + a, xs + b) for a in (0, 1) for b in (0, 1)]
                            if any(locked[c] and not R[c] for c in cells): continue
                            v = sum(qc[c] for c in cells)
                            if v > best: best, blk = v, cells
                    if blk is None: continue
                    for c in blk:
                        if not R[c]:
                            lab[c] = bestq[c] if qc[c] > 0 else lab[y, x]
                    R = limb_cells(lab, q)
        fill = lab >= 0
        # stray limb crumbs: extra sprite pieces of a limb (< SPECK px) away from its main piece -> neighbour majority (non-limb)
        for q in skc:
            R = limb_cells(lab, q); rl, rn = nd.label(R, np.ones((3, 3)))
            if rn <= 1: continue
            sz = nd.sum(R, rl, range(1, rn + 1)); main = 1 + int(np.argmax(sz))
            for k in range(1, rn + 1):
                if k == main or sz[k - 1] >= SPECK: continue
                cm = rl == k; ring = nd.binary_dilation(cm, np.ones((3, 3))) & ~cm & ~R
                v = lab[ring][lab[ring] >= 0]
                lab[cm] = np.bincount(v).argmax() if len(v) else -1
        fill = lab >= 0
    lab = np.where(fill, lab, -1)
    # ---- silhouette clean: 1 px notches filled, 1 px spikes removed (limbs exempt)
    islimb = np.zeros((N, N), bool)
    for q in LIMBQ(): islimb |= limb_cells(lab, q)
    for _ in range(2):
        f = lab >= 0; pf = np.pad(f, 1); n4 = pf[:-2, 1:-1].astype(int) + pf[2:, 1:-1] + pf[1:-1, :-2] + pf[1:-1, 2:]
        notch = ~f & (n4 >= 3)
        if notch.any():
            pl = np.pad(lab, 1, constant_values=-1); cand = np.stack([pl[:-2, 1:-1], pl[2:, 1:-1], pl[1:-1, :-2], pl[1:-1, 2:]], -1)
            for y, x in zip(*np.nonzero(notch)):
                v = cand[y, x][cand[y, x] >= 0]; lab[y, x] = np.bincount(v).argmax()
        spike = f & (n4 <= 1) & ~islimb & ~locked
        lab[spike] = -1
    # smooth hem/hip curves: one 3x3 majority pass on the fill of skirt/torso/sleeve cells (limbs, head and locked cells exempt)
    if SMOOTH:
        f = lab >= 0; cnt9 = nd.uniform_filter(f.astype(float), 3) * 9
        Pp = np.where(f, SEG_P[np.maximum(lab, 0)], -1)
        soft = np.isin(Pp, [PI['skirt'], PI['torso'], PI['sleeve.L'], PI['sleeve.R']])
        nbsoft = nd.binary_dilation(soft, np.ones((3, 3)))
        add = ~f & (cnt9 >= 6) & nbsoft & ~np.isin(np.roll(Pp, 0), [PI['head']])
        rem = f & soft & (cnt9 <= 3) & ~locked
        if add.any():
            pl = np.pad(lab, 1, constant_values=-1)
            for y, x in zip(*np.nonzero(add)):
                v = pl[y:y + 3, x:x + 3].ravel(); v = v[v >= 0]
                if len(v): lab[y, x] = np.bincount(v).argmax()
        lab[rem] = -1
    # small enclosed holes (slits between arm and body that the erosion opened) -> filled, else they become dotted K rings
    hl, nh = nd.label(lab < 0)
    if nh:
        hs = nd.sum(np.ones_like(hl), hl, range(1, nh + 1))
        border = set(np.unique(np.concatenate([hl[0], hl[-1], hl[:, 0], hl[:, -1]])))
        for h in range(1, nh + 1):
            if hs[h - 1] <= HOLE and h not in border:
                hm = hl == h; ring = nd.binary_dilation(hm, CROSS) & ~hm
                v = lab[ring][lab[ring] >= 0]
                if len(v): lab[hm] = np.bincount(v).argmax()
    fill = lab >= 0
    # ---- interior separation lines (far side)
    ldep = np.where(fill, np.take_along_axis(dep, np.maximum(lab, 0)[..., None], -1)[..., 0], np.inf)
    P_ = np.where(fill, SEG_P[np.maximum(lab, 0)], -1); M_ = np.where(fill, SEG_M[np.maximum(lab, 0)], -1)
    B_ = np.vectorize(lambda p: BODY[PARTS[p]] if p >= 0 else -1)(P_)
    line = np.zeros((N, N), bool); dark = np.zeros((N, N), bool)
    if opt['sep']:
        hairg = {MI['hair'], MI['bow']}
        cand = []  # (far cell, near cell)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = lambda a: np.roll(np.roll(a, -dy, 0), -dx, 1)
            Bn, Mn, Pn, Dn = nb(B_), nb(M_), nb(P_), nb(ldep)
            both = fill & (Bn >= 0)
            far = both & (ldep > Dn)
            legs = np.isin(B_, [2, 3]) & np.isin(Bn, [2, 3]) & (B_ != Bn)
            armb = (np.isin(B_, [4, 5]) | np.isin(Bn, [4, 5])) & (B_ != Bn) & (ldep - Dn > DTHR)
            headm = (B_ == 1) & (Bn == 1) & ((np.isin(M_, list(hairg)) & (Mn == MI['skin'])) | ((M_ == MI['skin']) & np.isin(Mn, list(hairg))))
            hand = ((M_ == MI['skin']) & np.isin(P_, [PI['arm.L'], PI['arm.R']]) & np.isin(Mn, [MI['sleeve'], MI['dress']])) | \
                   ((Mn == MI['skin']) & np.isin(Pn, [PI['arm.L'], PI['arm.R']]) & np.isin(M_, [MI['sleeve'], MI['dress']]))
            if texg is not None: headm = headm & False
            obil = OBILINE & (((M_ == MI['obi']) & np.isin(Mn, [MI['dress'], MI['sleeve']])) | ((Mn == MI['obi']) & np.isin(M_, [MI['dress'], MI['sleeve']])))
            headm = headm | obil
            for y, x in zip(*np.nonzero(far & (legs | armb | headm | hand) & ~(T & nb(T)))):
                cand.append(((y, x), ((y + dy) % N, (x + dx) % N)))
        LQ = {}
        for q in LIMBQ(): LQ[q] = limb_cells(lab, q)
        def limb_at(c):
            for q, R in LQ.items():
                if R[c]: return q
            return None
        def still_wide(c):
            """True if marking c as line keeps every fill pixel of c's limb within the 5x5 window inside a 2x2 block of that limb"""
            q = limb_at(c)
            if q is None: return True
            y, x = c; y0, y1, x0, x1 = max(0, y - 3), min(N, y + 4), max(0, x - 3), min(N, x + 4)
            R0 = LQ[q][y0:y1, x0:x1] & ~line[y0:y1, x0:x1]; R = R0.copy(); R[y - y0, x - x0] = False
            if not R.any(): return False
            thin = lambda A: A & ~nd.binary_dilation(nd.binary_opening(np.pad(A, 1), np.ones((2, 2))), CROSS)[1:-1, 1:-1]  # 2x2 core + 1 px fringe
            inner = np.zeros_like(R); inner[max(0, y - 2 - y0):y + 3 - y0, max(0, x - 2 - x0):x + 3 - x0] = True
            return not (thin(R) & ~thin(R0) & inner).any()
        def run_len(c, d):
            q = limb_at(c)
            if q is None: return 99
            n = 1
            for sg in (1, -1):
                y, x = c
                while True:
                    y, x = y + sg * d[0], x + sg * d[1]
                    if not (0 <= y < N and 0 <= x < N) or not LQ[q][y, x] or line[y, x]: break
                    n += 1
            return n
        for fc, nc in cand:
            if line[fc] or line[nc]: continue
            d = (nc[0] - fc[0], nc[1] - fc[1])
            first = (nc, fc) if (run_len(fc, d) <= 2 and run_len(nc, d) >= 4) else (fc, nc)  # thin far limb: the near limb carries the line
            if still_wide(first[0]): line[first[0]] = True
            elif still_wide(first[1]): line[first[1]] = True
            else: dark[nc] = True  # no room: lit edge on the near side instead of a line
        # interior lines only as runs of >= MINRUN px (r10 rule: no dotted interior lines); leg|leg separations always stay
        lc, nlc = nd.label(line, np.ones((3, 3)))
        if nlc:
            sz = nd.sum(line, lc, range(1, nlc + 1)); legl = nd.maximum(np.isin(B_, [2, 3]), lc, range(1, nlc + 1))
            drop = np.array([0] + [int(z < MINRUN and not lg) for z, lg in zip(sz, legl)], bool)
            line &= ~drop[lc]
    # ---- shading
    lum = np.take_along_axis(S['lum'], np.maximum(lab, 0)[..., None], -1)[..., 0]
    bias = np.array([hx.BIAS.get(n, 1.0) for n in MN])[np.maximum(M_, 0)]; l = lum * bias
    band = np.where(l < hx.T1, 0, np.where(l > hx.T2, 2, 1))
    if W is not None:
        pb = W['band']; same = (W['lab'] == lab) & fill & (pb >= 0)
        hold = same & (((pb == 0) & (l < hx.T1 + HYS)) | ((pb == 2) & (l > hx.T2 - HYS)) | ((pb == 1) & (l >= hx.T1 - HYS) & (l <= hx.T2 + HYS)))
        band = np.where(hold, pb, band)
    if held_band is not None: band = np.where(held & fill, held_band, band)
    band = np.where(fill, band, -1)
    # near / far leg
    # far leg is fixed per view (no shade swap when the legs pass): her left leg is the far one when the camera is on her right side
    farleg = {'SE': PI['leg.L'], 'E': PI['leg.L'], 'NE': PI['leg.L'], 'SW': PI['leg.R'], 'W': PI['leg.R'], 'NW': PI['leg.R']}.get(opt.get('view'))
    g = np.full((N, N), '.', dtype='<U1')
    for j, n in enumerate(MN):
        for b in range(3):
            g[fill & (M_ == j) & (band == b)] = hx.RAMP[n][b]
    isleg = np.isin(P_, LEG)
    # legs: skin band (s, S on the hem row), red sock-top band (always >= 1 row between skin and sock), socks D + lit d stripe and a d rim
    # along the far leg (near leg only), boots ramp; the far leg is one step darker (S, R, D, boots down one band)
    g[fill & np.isin(P_, [PI['torso'], PI['skirt']]) & (M_ == MI['skin'])] = 'S'  # thigh skin weighted to the pelvis = skirt underside
    g[isleg & (M_ == MI['dress'])] = 'E'
    g[fill & (P_ == PI['skirt']) & (g == 'e')] = 'E'  # skirt: 2 ramp values only (E/R), no flickering highlight clusters
    skin_leg = isleg & (M_ == MI['skin']); g[skin_leg] = 's'
    above = np.roll(P_, 1, 0); g[skin_leg & ~np.isin(above, LEG) & (above >= 0)] = 'S'
    g[isleg & (M_ == MI['bow'])] = 'E'
    sock = isleg & (M_ == MI['socks']); g[sock] = 'D'
    up_m = np.roll(M_, 1, 0); up_p = np.roll(P_, 1, 0)
    g[sock & (up_m == MI['skin']) & (up_p == P_)] = 'E'
    for q in LEG:
        if q == farleg and opt['sep']:
            far = P_ == q
            g[far & (M_ == MI['skin'])] = 'S'; g[far & (g == 'E')] = 'R'
            bt = far & (M_ == MI['boots']); g[bt & (g == 'g')] = 'H'; g[bt & (g == 'H')] = 'h'
            continue
        sq = sock & (P_ == q) & ~line & (g == 'D')
        for y in range(N):
            xs = np.nonzero(sq[y])[0]
            if len(xs) < 2: continue
            runs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
            for r_ in runs:
                if len(r_) < 2: continue
                x = r_[1] if len(r_) >= 3 else r_[0]
                if l[y, x] > SHEEN: g[y, x] = 'd'
        if farleg is not None and opt['sep']:
            fl = (P_ == farleg) | (line & np.isin(B_, [2, 3]))
            nbf = nd.binary_dilation(fl, CROSS) & ~fl
            g[sq & nbf] = RIM
    # far-limb dark fallback for suppressed lines
    for a_, b_ in (('D', 'd'), ('S', 's'), ('R', 'E'), ('h', 'H'), ('H', 'g')):
        g[dark & (g == a_)] = b_
    g[line] = 'K'
    # surface lock: a fill cell showing the same surface point (rest-pose correspondence) and segment as in the previous frame keeps the
    # previous frame's exact shade unless its lum moved by more than LOCK (moving shading boundaries stick to the surface)
    if W is not None and 'src' in W and LOCK > 0:
        v = W['valid'] & fill & (g != 'K') & ~line
        sy, sx = W['src'][..., 0], W['src'][..., 1]
        pgc = np.where(v, prev['g'][np.maximum(sy, 0), np.maximum(sx, 0)], '.')
        plc = np.where(v, prev['lcell'][np.maximum(sy, 0), np.maximum(sx, 0)], 9)
        plb = np.where(v, prev['lab'][np.maximum(sy, 0), np.maximum(sx, 0)], -2)
        cls = np.vectorize(lambda c: CLS.get(c, c))
        okc = v & (plb == lab) & (pgc != 'K') & (np.abs(plc - l) < LOCK)
        okc &= cls(pgc) == cls(g)
        g[okc] = pgc[okc]
    if texg is not None:
        g[T] = texg[T]
        # head hold: the master head pixels are kept from the previous frame (integer-shifted) unless the projection changed > HOLDT
        if prev is not None and opt['temporal'] and prev.get('T') is not None and prev['T'].any() and HOLDT > 0:
            best = (-1, (0, 0))
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    pT = np.roll(np.roll(prev['T'], dy, 0), dx, 1); pg = np.roll(np.roll(prev['g'], dy, 0), dx, 1)
                    U = T | pT; eq = ((pg == g) & T & pT).sum() / max(1, U.sum())
                    if eq > best[0]: best = (eq, (dy, dx))
            eq, (dy, dx) = best
            if 1 - eq < HOLDT:
                pT = np.roll(np.roll(prev['T'], dy, 0), dx, 1); pg = np.roll(np.roll(prev['g'], dy, 0), dx, 1)
                keep = pT & T; g[keep] = pg[keep]
    # ---- outline outside the fill, pixel-perfect (not where the fill edge is already K, e.g. the master head's own outline)
    f = fill; pf = np.pad(f, 1)
    ring = ~f & (pf[:-2, 1:-1] | pf[2:, 1:-1] | pf[1:-1, :-2] | pf[1:-1, 2:])
    pnk = np.pad(f & (g != 'K'), 1); ring &= (pnk[:-2, 1:-1] | pnk[2:, 1:-1] | pnk[1:-1, :-2] | pnk[1:-1, 2:])
    g[ring] = 'K'
    k = g == 'K'
    for _ in range(2):
        pk = np.pad(k & ~f, 1); pf = np.pad(f, 1)
        n4f = pf[:-2, 1:-1] | pf[2:, 1:-1] | pf[1:-1, :-2] | pf[1:-1, 2:]
        Nn, Ss, Ww, Ee = pk[:-2, 1:-1], pk[2:, 1:-1], pk[1:-1, :-2], pk[1:-1, 2:]
        L = ((Nn & Ee) | (Ee & Ss) | (Ss & Ww) | (Ww & Nn)) & ~(Nn & Ss) & ~(Ee & Ww)
        rm = ring & k & ~n4f & L
        g[rm] = '.'; k = g == 'K'; ring &= ~rm
    g0 = g; g = hx.Z.clean_orphans(g, keep='WKd')
    if texg is not None: g[T] = g0[T]
    bmask = np.where(fill, dom_b, -1)
    st = {'lcell': l, 'T': T if texg is not None else None, 'rpos': F.get('rpos'), 'rpos_ok': F.get('rpos_ok'), 'dom_b': dom_b, 'line': line, 'lab': lab, 'band': band, 'fill': fill, 'bmask': bmask, 'g': g, 'mid': F['mid'], 'part': F['part'], 'lum': F['lum'],
          'farleg': farleg}
    return g, st


def reuse_unchanged(g, st, prev):
    """copy the previous output where the hi-res guide (matid + part + lum) of the cell and its 8 neighbours did not change"""
    if prev is None: return g
    same = (prev['mid'] == st['mid']) & (prev['part'] == st['part']) & (np.abs(prev['lum'] - st['lum']) < 0.01)
    c = hx.cells(same.astype(float)).min((2, 3)) > 0.5
    c = nd.binary_erosion(c, np.ones((3, 3)), border_value=0)
    out = g.copy(); out[c] = prev['g'][c]; return out


CLS = hx.CLS


def kill_flips(G, loop):
    n = len(G); G = [g.copy() for g in G]
    cls = lambda ch: CLS.get(ch, ch)
    vc = np.vectorize(cls)
    for _ in range(2):
        for t in range(n):
            if not loop and (t == 0 or t == n - 1): continue
            a, b, c = G[(t - 1) % n], G[t], G[(t + 1) % n]
            ca, cb, cc = vc(a), vc(b), vc(c)
            m = (a == c) & (b != a) & (ca == cb) & ~np.isin(ca, ['.', 'K'])
            b[m] = a[m]
    return G


def head_clear(mg_grid, neck_row):
    rows = np.arange(N)[:, None] < neck_row + 1
    return np.isin(mg_grid, [MI[k] for k in ('hair', 'skin', 'eyes', 'bow')]) & rows


def run(stem, info, opt):
    view = info['view']; frs = info['frames']; pdir = os.path.join(os.path.dirname(stem), 'parts')
    ensure_parts(stem, info, pdir)
    sh = align(stem, view)
    Fs = [load(stem, f['i'], sh['dx'], sh['dy'], pdir) for f in frs]
    if not all(F['part_ok'] for F in Fs): print('WARN part pass missing/mismatched -> fallback single leg part')
    loop = len(frs) > 2 and info.get('loop', True) and info['action'] not in ('jump',)
    prev = None; order = (list(range(len(Fs))) if loop and opt['temporal'] else []) + list(range(len(Fs)))
    out = [None] * len(Fs); sts = [None] * len(Fs)
    for n_, i in enumerate(order):
        g, st = frame(Fs[i], prev, {**opt, 'view': view})
        if opt['temporal']: g = reuse_unchanged(g, st, prev); st['g'] = g
        out[i], sts[i] = g, st; prev = st
    if opt['temporal']: out = kill_flips(out, loop)
    out = [hx.main_comp(hx.drop_bare_k(g)) for g in out]
    aud = [limb_audit(g, st, F) for g, st, F in zip(out, sts, Fs)]
    return out, sts, sh, aud


# ------------------------------------------------------------------ limb audit (round 3 gate)
LIMBS = {'leg.L': ([PI['leg.L']], None), 'leg.R': ([PI['leg.R']], None),
         'arm.L': ([PI['arm.L'], PI['sleeve.L']], None), 'arm.R': ([PI['arm.R'], PI['sleeve.R']], None),
         'hand.L': ([PI['arm.L']], MI['skin']), 'hand.R': ([PI['arm.R']], MI['skin'])}


def limb_audit(g, st, F):
    """per limb: VANISHED (visible in 3D, no sprite pixels), SPLIT (more 8-connected sprite pieces than the visible hi-res limb has),
    THIN (fill pixels outside a 2x2 core + 1 px fringe), DETACHED (a piece not touching the rest of the figure through <= 1 px of outline).
    Limb pixels = final non-outline pixels whose segment belongs to the limb."""
    lab = st['lab']; opaque = g != '.'; fillg = opaque & (g != 'K') & (lab >= 0)
    P_ = np.where(fillg, SEG_P[np.maximum(lab, 0)], -1); M_ = np.where(fillg, SEG_M[np.maximum(lab, 0)], -1)
    out = {}
    for name, (parts, mat) in LIMBS.items():
        L = np.isin(P_, parts) & ((M_ == mat) if mat is not None else True)
        hi = np.isin(F['part'], parts) & ((F['mid'] == mat) if mat is not None else True)
        hia = hi.sum() / (P * P)  # visible area in sprite px
        hl, hn = nd.label(nd.binary_closing(hi, np.ones((5, 5))), np.ones((3, 3)))
        hcomp = int(sum(1 for k in range(1, hn + 1) if (hl == k).sum() >= 2 * P * P)) if hn else 0
        Lc = L | (st['line'] & nd.binary_dilation(L, CROSS) & (g == 'K'))  # an interior line drawn inside the limb does not split it
        sl, sn = nd.label(Lc, np.ones((3, 3)))
        core = nd.binary_opening(np.pad(L, 1), np.ones((2, 2)))[1:-1, 1:-1]
        thin = int((L & ~nd.binary_dilation(core, CROSS)).sum())
        det = 0
        rest = opaque & ~L
        for k in range(1, sn + 1):
            c = (sl == k) & L
            if not (nd.binary_dilation(c, np.ones((3, 3)), iterations=2) & rest & (g != 'K')).any(): det += 1
        fl = []
        if hia >= 2 and L.sum() == 0: fl.append('VANISHED')
        if sn > max(1, hcomp): fl.append('SPLIT')
        if thin: fl.append('THIN')
        if det: fl.append('DETACHED')
        out[name] = {'px': int(L.sum()), 'hi_px': round(float(hia), 1), 'pieces': int(sn), 'hi_pieces': hcomp, 'thin': thin, 'detached': det, 'flags': fl}
    return out


def audit_report(aud, frs):
    bad = {f"f{f['i']:02d}": {k: v['flags'] for k, v in a.items() if v['flags']} for f, a in zip(frs, aud)}
    bad = {k: v for k, v in bad.items() if v}
    return {'frames': len(aud), 'failed_frames': len(bad), 'fails': bad, 'pass': not bad}


def main():
    jp = sys.argv[1]; info = json.load(open(jp)); stem = jp[:-5]
    if info['preview']:
        sys.argv = [sys.argv[0]] + sys.argv[1:]; import importlib.util as iu
        spec = iu.spec_from_file_location('r1', os.path.join(HERE, 'pixel_chain_r1.py')); m = iu.module_from_spec(spec); spec.loader.exec_module(m); m.main(); return
    opt = {'temporal': '--no-temporal' not in sys.argv, 'protect': '--no-protect' not in sys.argv, 'sep': '--no-sep' not in sys.argv}
    stamp = '--stamp' in sys.argv; view = info['view']; frs = info['frames']; durs = [int(f['ms']) for f in frs]
    G, sts, sh, aud = run(stem, info, opt)
    od = stem + '_px'; os.makedirs(od, exist_ok=True)
    ims, ims_h, grids_h = [], [], []
    if stamp:
        t, x0s, y0s = hx.stamp_of(view); R = info['rest']['head']; os.makedirs(od + '_hs', exist_ok=True)
    for f, g, st in zip(frs, G, sts):
        i = f['i']; hx.save(g, f'{od}/f{i:02d}', view); ims.append(hx.render(g, 4, BG))
        if stamp:
            H = f['pts']['head']; x0 = x0s + int(round(H[0] - R[0])); y0 = y0s + int(round(H[1] - R[1]))
            nk = int(round(f['pts']['neck'][1] - 32 + sh['dy']))
            mg = np.where(st['lab'] >= 0, SEG_M[np.maximum(st['lab'], 0)], -1)
            g2 = g.copy(); g2[head_clear(mg, nk)] = '.'; g2 = hx.paste(g2, t, x0, y0); g2 = hx.main_comp(hx.Z.clean_orphans(g2, keep='WKd'))
            hx.save(g2, f'{od}_hs/f{i:02d}', view); grids_h.append(g2); ims_h.append(hx.render(g2, 4, BG))
    ar = audit_report(aud, frs); json.dump({'summary': ar, 'per_frame': aud}, open(f'{stem}_limbs.json', 'w'), indent=0)
    print('LIMB_AUDIT', os.path.basename(stem), 'PASS' if ar['pass'] else f"FAIL {ar['failed_frames']}/{ar['frames']} frames", json.dumps(ar['fails'])[:400])
    res = {'limb_audit': ar, 'align': sh, 'chain': 'P2', 'opt': opt, 'farleg': [PARTS[s['farleg']] if s['farleg'] is not None else None for s in sts]}
    for tag, I_, G_ in (('', ims, G), ('_hs', ims_h, grids_h)):
        if not I_: continue
        gif(I_, durs, f'{stem}{tag}_4x.gif'); sheet(I_, f'{stem}{tag}_sheet.png', [f"f{f['i']:02d}" for f in frs], cols=min(8, len(I_)))
        res['band_churn' + tag] = hx.band_churn(G_) if len(G_) > 1 else None
        print('full', f'{stem}{tag}_4x.gif', sh)
    json.dump(res, open(f'{stem}_px.json', 'w'))


if __name__ == '__main__':
    main()
