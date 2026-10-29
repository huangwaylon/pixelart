"""pixel_chain.py STEM.json [--no-temporal] [--no-protect] [--no-sep]   (pixtools venv)   -- P's pixel step (round 5: one rule set for
the whole figure; no head/face special cases: no tex projection, no stamp, no face layer, no head hold).
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
Outputs: <stem>_px/fNN.{txt,png,json}, <stem>_4x.gif (mid-grey, render/gifio.py), <stem>_sheet.png, <stem>_px.json (+limb_audit),
<stem>_limbs.json (per-frame limb audit: VANISHED / SPLIT / THIN / DETACHED per leg, arm, hand)."""
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
FAMB = float(os.environ.get('FAMB', '0.2'))    # fill hysteresis half-band around .5 coverage
LKEEP = float(os.environ.get('LKEEP', '0.75'))  # keep the previous label if its score >= LKEEP x best
OBILINE = os.environ.get('OBILINE', '0') == '1'  # K line on the far side of obi|dress edges (master has them)
PROTECT_ARMS = os.environ.get('PROTECT_ARMS', '1') == '1'  # round 3: arms (sleeve tube + bag) get the 2 px guarantee too
SPECK_END = int(os.environ.get('SPECK_END', '10'))  # late limb crumbs (after lines/outline)
SPECK = int(os.environ.get('SPECK', '6'))  # limb crumbs smaller than this, detached from the limb's main piece, are relabelled
SHAPE = os.environ.get('SHAPE', '1') == '1'  # round 3 shape fixes (A-line skirt, smooth hem, skin cap, round toes)
HIPF = float(os.environ.get('HIPF', '0.35'))  # A-line envelope starts at this fraction of the skirt height (hip)
ALINE = float(os.environ.get('ALINE', '0.6'))  # skirt widening per row and side (px)
SKINMAX = int(os.environ.get('SKINMAX', '3'))  # max skin-band rows under the hem
ORPHAN = os.environ.get('ORPHAN', '1') == '1'  # round 6 orphan rule for every material
PZCLEAN = os.environ.get('PZCLEAN', '1') == '1'  # default on (round 8): active when the 8x colour pass <stem>_fNN_pv.png exists  # masters' pz.py cleanup (face pass) on the final grid, source = 8x colour render
EDGESKIN = os.environ.get('EDGESKIN', '1') == '1'  # round 8 global skin edge shading + mouth off the silhouette
COLOR = os.environ.get('COLOR', 'vote')  # colour stage: vote (material ramps + E2 textures) | ec0 (pz EC0 on the 8x colour render 'pv')
RIM = os.environ.get('RIM', 'g')  # near-leg rim tone along the leg|leg separation (d = sock sheen; g = boot light, stronger)
SMOOTH = os.environ.get('SMOOTH', '1') == '1'
HOLE = int(os.environ.get('HOLE', '4'))  # enclosed background holes up to this many px are filled
MINRUN = int(os.environ.get('MINRUN', '3'))
LSIG = float(os.environ.get('LSIG', '10'))  # hi-res lum smoothing inside a segment (8 = 1 sprite px)       # shade-band hysteresis margin (lum units)
SHEEN = float(os.environ.get('SHEEN', '0.42'))   # sock lit-stripe lum threshold
MAST = hx.SW + 'v2/m96/masters/EC0_{}_96.txt'
# materials: hx (hires3d) base 9 + round-5 face materials as ORDINARY materials (same vote, ramps, protection, lines as any other).
# R's guide colours for the new matids: rig/matids.json {"name": [r,g,b], ...} overrides/extends these defaults.
MATS = dict(hx.MATS)
MATS.update({'eye_white': (236, 236, 246), 'iris': (88, 64, 120), 'lash': (24, 16, 32), 'mouth': (190, 80, 90), 'blush': (235, 140, 150)})
_mj = os.path.join(EXP, 'rig', 'face_mats.json')  # R round 5 (exact sRGB guide colours); re-read on every run
if os.path.exists(_mj):
    _d = json.load(open(_mj)); MATS.update({k: tuple(v) for k, v in {**_d.get('base', {}), **_d.get('mats', {})}.items()})
MN = list(MATS); NM = len(MN); MI = {n: i for i, n in enumerate(MN)}; MCOL = np.array([MATS[k] for k in MN], float)
RAMP = dict(hx.RAMP); RAMP.update({'eye_white': 'WWW', 'iris': 'ggg', 'lash': 'KKK', 'mouth': 'mmm', 'blush': 'kkk', 'iris_top': 'hhh', 'iris_low': 'LLL',
             'brow': 'ggg', 'mouth_in': 'RRR', 'nose': 'SSS'})  # F's suggested ramps (rig/face_mats.json _doc)
if os.path.exists(_mj): RAMP.update({k: v for k, v in json.load(open(_mj)).get('ramps', {}).items()})
for _n in MN:  # any new matid without a ramp: its nearest locked-palette colour, flat
    if _n not in RAMP:
        _k = hx.KEYS[int(((np.array(hx.RGB, float) - np.array(MATS[_n], float)) ** 2).sum(1).argmin())]; RAMP[_n] = _k * 3
BIAS = dict(hx.BIAS)
# dark-band (shadow) lum threshold per material; default hx.T1 = .22.  Skin is lower so skin (face, hands, thighs) sits mostly in s like the masters
T1M = {'skin': float(os.environ.get('SKIN_T1', '0.10'))}
# round 7: TEXTURED materials (e.g. R's illustration-textured head): their colour comes from the texture pass by E2 k-centroid per cell
# (the method that made the approved masters from the illustrations), snapped to the locked palette - a global per-material rule.
# Config in rig/face_mats.json: "textured": {"mats": ["hair", "skin", ...], "pass": "tex", "k": 3}.  Off when absent.
_TX = (json.load(open(_mj)).get('textured') if os.path.exists(_mj) else None) or {}
TEXMATS = set(os.environ.get('TEXMATS', ','.join(_TX.get('mats', []))).split(',')) - {''}
TEXPASS = _TX.get('pass', 'tex'); TEXK = int(os.environ.get('TEXK', 4))  # round 7 bench: k=4 best balance (R's json suggests 3)
# without an explicit list, every pixel the texture pass covers is textured (R r10: tex = unlit illustration colours, alpha = textured surface)
TEXALLOW = os.environ.get('TEXALLOW', 'all')  # palette lock for textured pixels: all keys, or the cell material's ramp ('mat')
TEXAUTO = os.environ.get('TEXAUTO', '1') == '1'; TEXPRE = os.environ.get('TEXPRE', '1') == '1'
THINF = {'iris': 2, 'eyes': 2, 'eye_white': 1, 'lash': 1, 'mouth': 1, 'iris_top': 1, 'iris_low': 1, 'brow': 1, 'mouth_in': 1, 'nose': 1}  # thin features: min width (1 = presence only, 2 = 2x2 core)
PARTS = ["torso", "head", "skirt", "leg.L", "leg.R", "arm.L", "arm.R", "sleeve.L", "sleeve.R"]; NP = len(PARTS); PI = {p: i for i, p in enumerate(PARTS)}
PCOL = np.array([((i + 1) * 25, 255 - (i + 1) * 25, (i * 67) % 256) for i in range(NP)], float) / 255
PCOL = np.where(PCOL <= 0.0031308, PCOL * 12.92, 1.055 * PCOL ** (1 / 2.4) - 0.055) * 255  # the byte attribute is read as linear -> sRGB out
NS = NM * NP
BODY = {'torso': 0, 'skirt': 0, 'head': 1, 'leg.L': 2, 'leg.R': 3, 'arm.L': 4, 'sleeve.L': 4, 'arm.R': 5, 'sleeve.R': 5}
SEG_M = np.arange(NS) // NP; SEG_P = np.arange(NS) % NP
LEG = (PI['leg.L'], PI['leg.R'])
CROSS = nd.generate_binary_structure(2, 1)


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
    mid = nearest(g[..., :3] * 255, MCOL); mid[~al] = -1; F['mid'] = mid
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
    if COLOR in ('ec0', 'composite') or PZCLEAN:
        pv = f'{stem}_f{i:02d}_pv.png'
        if os.path.exists(pv): F['pv'] = crop(hx.rd16(pv), dx, dy)
    if TEXMATS or TEXAUTO:
        tp = f'{stem}_f{i:02d}_{TEXPASS}.png'
        if os.path.exists(tp): F['texc'] = crop(hx.rd16(tp), dx, dy)
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
    MIRV = {'W': 'E', 'SW': 'SE', 'NW': 'NE'}  # views without a master: the mirrored opposite master (feet rule is mirror-safe)
    m = hx.read_grid(MAST.format(MIRV.get(view, view))) != '.'
    if view in MIRV: m = m[:, ::-1]
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
    for m, w in THINF.items():  # thin features (eyes, iris, lashes/brows, mouth): any part, ordinary material rule
        if m in MI: out[300 + MI[m]] = F['mid'] == MI[m]
    if PROTECT_ARMS:
        for s in 'LR':  # arm = upper arm / forearm cloth + sleeve bag (not the hand)
            q = PI['arm.' + s]; out[200 + q] = np.isin(F['part'], [q, PI['sleeve.' + s]]) & (F['mid'] != MI['skin']) & (F['mid'] >= 0)
    return out


ARMQ = {PI['arm.L']: PI['sleeve.L'], PI['arm.R']: PI['sleeve.R']}


def limb_of_seg(k):
    p = SEG_P[k]; m = SEG_M[k]
    if MN[m] in THINF: return 300 + m
    if p in LEG: return p
    if p in (PI['arm.L'], PI['arm.R']) and m == MI['skin']: return 100 + p
    if PROTECT_ARMS:
        for a_, sl_ in ARMQ.items():
            if p in (a_, sl_): return 200 + a_
    return None


def limb_cells(lab, q):
    if q >= 300: return (lab >= 0) & (SEG_M[np.maximum(lab, 0)] == q - 300)
    if q < 100: return (lab >= 0) & np.isin(SEG_P[np.maximum(lab, 0)], [q])
    if q >= 200: return (lab >= 0) & np.isin(SEG_P[np.maximum(lab, 0)], [q - 200, ARMQ[q - 200]]) & (SEG_M[np.maximum(lab, 0)] != MI['skin'])
    return (lab >= 0) & (SEG_P[np.maximum(lab, 0)] == q - 100) & (SEG_M[np.maximum(lab, 0)] == MI['skin'])


def limb_segs(q):
    return [k for k in range(NS) if limb_of_seg(k) == q]


def LIMBQ():
    return [*LEG, 100 + PI['arm.L'], 100 + PI['arm.R']] + ([200 + PI['arm.L'], 200 + PI['arm.R']] if PROTECT_ARMS else [])


KEYS = hx.KEYS; PALRGB = np.array(hx.RGB, float)


# ------------------------------------------------------------------ round 3 shape fixes (on the label grid, before the outline)
def _part(lab): return np.where(lab >= 0, SEG_P[np.maximum(lab, 0)], -1)


def _mat(lab): return np.where(lab >= 0, SEG_M[np.maximum(lab, 0)], -1)


def shape_fixes(lab, locked):
    """A-line skirt envelope, smooth hem line, skin-band height cap, rounded boot toes"""
    lab = lab.copy(); P_ = _part(lab); M_ = _mat(lab)
    sk = P_ == PI['skirt']
    rows = np.nonzero(sk.any(1))[0]
    if len(rows) > 3:
        # 1. A-line: below the hip row (HIPF of the skirt height) the skirt may widen by at most ALINE px per row and side; only the
        #    outer flare that is open to the background is shaved (never a hole inside the figure, never a sleeve/arm/leg cell)
        yh = rows[0] + int(HIPF * (rows[-1] - rows[0])); yh = rows[rows >= yh][0]  # skirt rows can be non-contiguous
        xs = np.nonzero(sk[yh])[0]; el, er = float(xs.min()), float(xs.max())
        for y in rows[rows > yh]:
            xs = np.nonzero(sk[y])[0]
            if not len(xs): continue
            el = max(float(xs.min()), el - ALINE); er = min(float(xs.max()), er + ALINE)
            L_, R_ = int(np.ceil(el - 1e-6)), int(np.floor(er + 1e-6))
            for x in range(xs.min(), L_):
                if lab[y, x] >= 0 and P_[y, x] == PI['skirt'] and (x == 0 or lab[y, x - 1] < 0) and not locked[y, x]: lab[y, x] = -1
                else: break
            for x in range(xs.max(), R_, -1):
                if lab[y, x] >= 0 and P_[y, x] == PI['skirt'] and (x == N - 1 or lab[y, x + 1] < 0) and not locked[y, x]: lab[y, x] = -1
                else: break
        P_ = _part(lab); sk = P_ == PI['skirt']
        # 2. hem line: where the hem is open to the background, its bottom row per column is median-smoothed (no stair-step corners)
        cols = np.nonzero(sk.any(0))[0]
        yb = np.full(N, -1)
        for x in cols:
            ys = np.nonzero(sk[:, x])[0]; y = ys.max()
            if y + 1 < N and lab[y + 1, x] < 0: yb[x] = y
        open_ = yb >= 0
        if open_.sum() >= 3:
            ys_ = yb.astype(float); sm = yb.copy()
            for x in np.nonzero(open_)[0]:
                nb = [ys_[k] for k in (x - 1, x, x + 1) if 0 <= k < N and open_[k]]
                if len(nb) == 3: sm[x] = int(np.median(nb))
            for x in np.nonzero(open_)[0]:
                if sm[x] < yb[x]: lab[sm[x] + 1:yb[x] + 1, x] = np.where(locked[sm[x] + 1:yb[x] + 1, x], lab[sm[x] + 1:yb[x] + 1, x], -1)
                elif sm[x] > yb[x]: lab[yb[x] + 1:sm[x] + 1, x] = lab[yb[x], x]
        P_ = _part(lab); M_ = _mat(lab); sk = P_ == PI['skirt']
    # 3. skin band: at most SKINMAX rows of leg skin directly under the skirt per column (more = the skirt rides up; extend the hem)
    for x in range(N):
        col = P_[:, x]
        for y in range(1, N):
            if col[y - 1] == PI['skirt'] and col[y] in LEG and M_[y, x] == MI['skin']:
                n = 0
                while y + n < N and P_[y + n, x] == col[y] and M_[y + n, x] == MI['skin']: n += 1
                if n > SKINMAX: lab[y:y + n - SKINMAX, x] = lab[y - 1, x]
    P_ = _part(lab); M_ = _mat(lab)
    # 4. rounded boot toes: convex boot corners open to the background on two sides are shaved (if the boot stays >= 3 wide there)
    f = lab >= 0
    boot = np.isin(P_, LEG) & (M_ == MI['boots'])
    pf = np.pad(f, 1)
    Nn, Ss, Ww, Ee = ~pf[:-2, 1:-1], ~pf[2:, 1:-1], ~pf[1:-1, :-2], ~pf[1:-1, 2:]
    conv = boot & (((Nn | Ss) & (Ww | Ee)))
    for y, x in zip(*np.nonzero(conv)):
        xs = np.nonzero(boot[y])[0]; run = ((xs >= x - 3) & (xs <= x + 3)).sum()
        if run >= 3 and not locked[y, x]: lab[y, x] = -1
    return lab


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
    locked = np.zeros((N, N), bool)
    # ---- limb protection
    if opt['protect']:
        LM = limb_masks(F); skc = {}
        for q, mk in LM.items():
            ml, mn = nd.label(mk)  # hi-res slivers under ~1.5 sprite px are not limbs to protect
            if mn:
                szs = [(ml == k).sum() for k in range(1, mn + 1)]
                keep = [k for k in range(1, mn + 1) if szs[k - 1] >= (0.35 if q >= 300 else 1.5) * P * P]
                if not keep and mk.sum() >= 2 * P * P: keep = [1 + int(np.argmax(szs))]  # visible enough to count (audit VANISHED rule): keep its largest piece
                mk = np.isin(ml, keep)
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
                if q >= 300 and THINF[MN[q - 300]] < 2: continue  # presence-only thin feature (lashes, brows, mouth)
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
            if q >= 300: continue  # thin features may legitimately be several pieces (two eyes)
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
    for q in LIMBQ() + [300 + MI[m] for m in THINF if m in MI]: islimb |= limb_cells(lab, q)
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
    if SHAPE: lab = shape_fixes(lab, locked)
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
        TXC = (hx.cells((F['texc'][..., 3] > 0.5).astype(float)).mean((2, 3)) >= 0.5) if 'texc' in F else None
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = lambda a: np.roll(np.roll(a, -dy, 0), -dx, 1)
            Bn, Mn, Pn, Dn = nb(B_), nb(M_), nb(P_), nb(ldep)
            both = fill & (Bn >= 0)
            far = both & (ldep > Dn)
            legs = np.isin(B_, [2, 3]) & np.isin(Bn, [2, 3]) & (B_ != Bn)
            armb = (np.isin(B_, [4, 5]) | np.isin(Bn, [4, 5])) & (B_ != Bn) & (ldep - Dn > DTHR)
            # material lines (any part): hair/bow over skin (fringe, side locks over cheeks/shoulders)
            headm = (np.isin(M_, list(hairg)) & (Mn == MI['skin'])) | ((M_ == MI['skin']) & np.isin(Mn, list(hairg)))
            hand = ((M_ == MI['skin']) & np.isin(P_, [PI['arm.L'], PI['arm.R']]) & np.isin(Mn, [MI['sleeve'], MI['dress']])) | \
                   ((Mn == MI['skin']) & np.isin(Pn, [PI['arm.L'], PI['arm.R']]) & np.isin(M_, [MI['sleeve'], MI['dress']]))
            obil = OBILINE & (((M_ == MI['obi']) & np.isin(Mn, [MI['dress'], MI['sleeve']])) | ((Mn == MI['obi']) & np.isin(M_, [MI['dress'], MI['sleeve']])))
            headm = headm | obil
            if TXC is not None: headm = headm & ~(TXC & nb(TXC))  # textured surfaces carry their own drawn lines: no material lines inside them
            for y, x in zip(*np.nonzero(far & (legs | armb | headm | hand))):
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
    bias = np.array([BIAS.get(n, 1.0) for n in MN])[np.maximum(M_, 0)]; l = lum * bias
    t1 = np.array([T1M.get(n, hx.T1) for n in MN])[np.maximum(M_, 0)]  # per-material dark threshold (global per material, any part)
    band = np.where(l < t1, 0, np.where(l > hx.T2, 2, 1))
    if W is not None:
        pb = W['band']; same = (W['lab'] == lab) & fill & (pb >= 0)
        hold = same & (((pb == 0) & (l < t1 + HYS)) | ((pb == 2) & (l > hx.T2 - HYS)) | ((pb == 1) & (l >= t1 - HYS) & (l <= hx.T2 + HYS)))
        band = np.where(hold, pb, band)
    band = np.where(fill, band, -1)
    # near / far leg
    # far leg is fixed per view (no shade swap when the legs pass): her left leg is the far one when the camera is on her right side
    farleg = {'SE': PI['leg.L'], 'E': PI['leg.L'], 'NE': PI['leg.L'], 'SW': PI['leg.R'], 'W': PI['leg.R'], 'NW': PI['leg.R']}.get(opt.get('view'))
    g = np.full((N, N), '.', dtype='<U1')
    for j, n in enumerate(MN):
        for b in range(3):
            g[fill & (M_ == j) & (band == b)] = RAMP[n][b]
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
    TXCELL = np.zeros((N, N), bool)
    if 'texc' in F and COLOR not in ('ec0', 'composite'):
        sel = fill & (np.isin(M_, [MI[m] for m in TEXMATS if m in MI]) if TEXMATS else True)
        g = textured_chars(g, F['texc'], sel, M_)
    if 'pv' in F and COLOR == 'composite' and 'texc' in F:
        # round 8 per-material composite: cells of a TEXTURED material (rig/face_mats.json, covered by the tex pass) take the masters' EC0
        # recipe colours (k-centroid + palette lock + pz cleanup incl. its face pass) computed on the 8x colour render; flat materials keep
        # the chain's colours.  The global rules (limb width/crumbs, outline, orphans, temporal) run on the composite afterwards.
        import p8_ec0
        e = p8_ec0.ec0_frame(np.clip(F['pv'] * 255, 0, 255).astype(np.uint8))
        txa = hx.cells((F['texc'][..., 3] > 0.5).astype(float)).mean((2, 3)) >= 0.5
        TXCELL = fill & txa & (np.isin(M_, [MI[m] for m in TEXMATS if m in MI]) if TEXMATS else True) & (e != '.')
        edge = fill & ~nd.binary_erosion(fill, CROSS, iterations=1)
        TXCELL &= ~((e == 'K') & edge)  # EC0's silhouette K would double the chain outline; its interior K (lashes, pupils) stays
        g = np.where(TXCELL, e, g)
    if 'pv' in F and COLOR == 'ec0':  # COLOR=ec0: the masters' E2 recipe (pz.py EC0 incl. its face pass) on the 8x colour render gives the colours of every fill
        # cell (body + head alike); the chain keeps geometry (fill, limb protection, lines, outline, temporal, orphans).  EC0's own K is kept
        # only in the interior (eyes, lashes, folds) - near our silhouette its outline would double ours.
        import p8_ec0
        e = p8_ec0.ec0_frame(np.clip(F['pv'] * 255, 0, 255).astype(np.uint8))
        edge = fill & ~nd.binary_erosion(fill, CROSS, iterations=1)
        take = fill & (e != '.') & ~((e == 'K') & edge)
        g = np.where(take, e, g)
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
    # limb width repair: limb fill pixels outside a 2x2 core + 1 px fringe (1 px slivers between lines, staircase tips) become outline,
    # as long as the limb keeps a core (it can't vanish this way)
    for q in LIMBQ():
        Lq = limb_cells(lab, q) & (g != 'K') & (g != '.')
        if not Lq.any(): continue
        core = nd.binary_opening(np.pad(Lq, 1), np.ones((2, 2)))[1:-1, 1:-1]
        if not core.any(): continue
        thin = Lq & ~nd.binary_dilation(core, CROSS)
        g[thin] = 'K'
    # late limb crumbs: after lines/outline, a limb piece < SPECK_END px that is not the limb's largest piece (e.g. a thigh peeking through a
    # skirt notch, a heel tip cut off by the far-leg line) is repainted with its surroundings and relabelled, so the limb stays one piece
    for q in LIMBQ():
        Lq = limb_cells(lab, q) & (g != 'K') & (g != '.')
        rl, rn = nd.label(Lq, np.ones((3, 3)))
        if rn <= 1: continue
        sz = nd.sum(Lq, rl, range(1, rn + 1)); main = 1 + int(np.argmax(sz))
        for k_ in range(1, rn + 1):
            if k_ == main or sz[k_ - 1] >= SPECK_END: continue
            cm = rl == k_; ring_ = nd.binary_dilation(cm, np.ones((3, 3))) & ~cm & ~Lq & (g != '.') & (g != 'K') & (lab >= 0)
            if ring_.any():
                v = lab[ring_]; nl = np.bincount(v).argmax(); cs = list(g[ring_ & (lab == nl)])
                lab[cm] = nl; g[cm] = max(set(cs), key=cs.count)
            else:
                g[cm] = 'K'  # enclosed by outline only: fold into the outline
    g0 = g; g = hx.Z.clean_orphans(g, keep='WKd')
    thinm = fill & np.isin(M_, [MI[m] for m in THINF if m in MI]); g[thinm] = g0[thinm]
    if 'texc' in F: txm = fill & (hx.cells((F['texc'][..., 3] > 0.5).astype(float)).mean((2, 3)) >= 0.5); g[txm] = g0[txm]  # texture colours: only the global orphan rule
    bmask = np.where(fill, dom_b, -1)
    st = {'txcell': TXCELL, 'lcell': l, 'rpos': F.get('rpos'), 'rpos_ok': F.get('rpos_ok'), 'dom_b': dom_b, 'line': line, 'lab': lab, 'band': band, 'fill': fill, 'bmask': bmask, 'g': g, 'mid': F['mid'], 'part': F['part'], 'lum': F['lum'],
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


def run(stem, info, opt):
    view = info['view']; frs = info['frames']; pdir = os.path.join(os.path.dirname(stem), 'parts')
    ensure_parts(stem, info, pdir)
    sh = align(stem, view)
    Fs = [load(stem, f['i'], sh['dx'], sh['dy'], pdir) for f in frs]
    if not all(F['part_ok'] for F in Fs): print('WARN part pass missing/mismatched -> fallback single leg part')
    loop = is_loop(info)
    prev = None; order = (list(range(len(Fs))) if loop and opt['temporal'] else []) + list(range(len(Fs)))
    out = [None] * len(Fs); sts = [None] * len(Fs)
    for n_, i in enumerate(order):
        g, st = frame(Fs[i], prev, {**opt, 'view': view})
        if opt['temporal']: g = reuse_unchanged(g, st, prev); st['g'] = g
        out[i], sts[i] = g, st; prev = st
    if opt['temporal']: out = kill_flips(out, loop)
    if ORPHAN: out = [orphan_rule(g, st) for g, st in zip(out, sts)]
    if PZCLEAN: out = [pz_cleanup(g, F, st) for g, F, st in zip(out, Fs, sts)]
    if EDGESKIN: out = [edge_skin_rule(g) for g in out]  # after the masters' cleanup so its face pass sees the plain skin
    out = [hx.main_comp(hx.drop_bare_k(g)) for g in out]
    if opt.get('smear', True):
        out, smk = apply_smear(out, info)
        if smk: print('SMEAR frames', [f"f{info['frames'][k]['i']:02d}" for k in smk], 'travel', np.round(travel_dir(info), 2).tolist())
    aud = [limb_audit(g, st, F) for g, st, F in zip(out, sts, Fs)]
    return out, sts, sh, aud


# ------------------------------------------------------------------ round 4: smear frames (dash burst)
AZV = {"SE": (1, 1), "E": (1, 0), "S": (0, 1), "SW": (-1, 1), "NE": (1, -1), "N": (0, -1), "W": (-1, 0), "NW": (-1, -1)}
SMEAR_NEAR, SMEAR_FAR, STREAK = 'k', 'm', ('W', 'k')  # locked-palette stand-ins for ANIM_DIRECTION pink_1 / pink_0 / steel_2+pink_0


def travel_dir(info):
    """screen direction (x right, y down) of her forward (+Y, turned by the view yaw) through the game camera (30 deg elevation)"""
    ax, ay = AZV.get(info['view'], (0, 1)); c = np.array([ax, ay, 0.0]); c /= np.linalg.norm(c)
    el = np.radians(30); cam = np.array([c[0] * np.cos(el), c[1] * np.cos(el), np.sin(el)]); d = -cam / np.linalg.norm(cam)
    right = np.cross(d, [0, 0, 1.0]); right /= np.linalg.norm(right); up = np.cross(right, d)
    yaw = np.radians(float(info.get('yaw') or 0)); F = np.array([-np.sin(yaw), np.cos(yaw), 0.0])
    return np.array([F @ right, -(F @ up)])


def motion_frames(info):
    act = info['action']
    for m in (f'{EXP}/motion/{act}.json', f'{EXP}/motion/view/{act}.json', f'{EXP}/motion/variants/{act}.json'):
        if os.path.exists(m): return json.load(open(m))['frames']
    return []


def smear_frames(info):
    """motion frames whose 'key' contains SMEAR (M's dash burst) or that carry "smear": true"""
    mf = motion_frames(info); out = []
    for k, f in enumerate(info['frames']):
        m = mf[f['i']] if f['i'] < len(mf) else {}
        if 'smear' in str(m.get('key', '')).lower() or m.get('smear') or f.get('smear'): out.append(k)
    return out


def apply_smear(G, info):
    """ANIM_DIRECTION 4.3 dash travel, palette-locked: smear 1 = 2 flat afterimages of the last pre-smear pose 6/12 px back along the
    travel (near k, far m) + 3-4 speed lines (1 px, 8-14 px, W/k alternating) from the trailing edge; smear 2 = 1 afterimage at 8 px (m)
    + speed lines.  Solid, hard-edged, no outline, never over the body (the stretched body itself is M's stretched pose)."""
    sm = smear_frames(info)
    if not sm: return G, []
    v = travel_dir(info); L = float(np.hypot(*v)); u = v / max(L, 1e-6); sc = max(L, 0.35)
    G = [g.copy() for g in G]
    base = None
    for k in range(len(G)):
        if k in sm:
            order = sm.index(k)
            src = G[base] if base is not None else G[k]
            sil = src != '.'
            ghosts = [(6, SMEAR_NEAR), (12, SMEAR_FAR)] if order == 0 else [(8, SMEAR_FAR)]
            g = G[k]
            for dist, ch in ghosts[::-1]:
                dy, dx = int(round(-u[1] * dist * sc)), int(round(-u[0] * dist * sc))
                gm = np.roll(np.roll(sil, dy, 0), dx, 1)
                g[gm & (g == '.')] = ch
            # speed lines from the trailing edge: 3-4 rows spread over the body height
            body = G[k] != '.'
            ys = np.nonzero(body.any(1))[0]
            if len(ys):
                rows = np.linspace(ys.min() + 0.2 * (ys.max() - ys.min()), ys.min() + 0.85 * (ys.max() - ys.min()), 4 if order == 0 else 3).astype(int)
                for n, y in enumerate(rows):
                    xs = np.nonzero(body[y])[0]
                    if not len(xs): continue
                    x0 = xs.min() if u[0] > 0 else xs.max()  # trailing edge (opposite the travel)
                    ln = 14 - 3 * n if order == 0 else 10 - 2 * n
                    for t in range(2, 2 + ln):
                        yy, xx = int(round(y - u[1] * t * 0.5)), int(round(x0 - np.sign(u[0] or 1) * t))
                        if 0 <= yy < N and 0 <= xx < N and g[yy, xx] == '.': g[yy, xx] = STREAK[n % 2]
            G[k] = g
        else:
            base = k
    return G, sm


def pz_cleanup(g, F, st=None):
    """PZCLEAN=1: the masters' E2 cleanup stage (pz.py cleanup(): data-driven face-feature pass from the source colours + orphans + skin
    specks + outline gaps) run on the chain's grid with the 8x colour render as its source - the same code the masters used, applied to
    the whole frame (it finds the face itself from the skin hull of the source)."""
    if 'pv' not in F: return g
    sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'); import pz as PZ_
    hi = np.clip(F['pv'] * 255, 0, 255); al = hi[..., 3] > 127; x = hi[..., :3].copy(); x[~al] = 255
    a = g != '.'; ys, xs = np.nonzero(a); oy, y1, ox, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    xf = x[oy * P:y1 * P, ox * P:x1 * P]; mf = al[oy * P:y1 * P, ox * P:x1 * P]
    if mf.sum() == 0: return g
    try:
        c = PZ_.cleanup(g.copy(), xf, mf, y1 - oy, ox, oy, hx.KEYS, np.array(hx.RGB, float))
    except Exception as e:
        print('WARN pz cleanup', repr(e)[:120]); return g
    if st is not None:  # round 9, global: limb cells (legs, arms, hands) and designed thin-feature materials (eyes, lashes, mouth...) are not
        # rewritten by the cleanup - it would thin limbs (its outline-gap/skin-speck passes) and erase flat-face features
        lab = st['lab']; keep = np.zeros(g.shape, bool)
        for q in LIMBQ(): keep |= limb_cells(lab, q)
        keep |= (lab >= 0) & np.isin(_mat(lab), [MI[m] for m in THINF if m in MI])
        keep &= (g != '.')
        c[keep] = g[keep]
    return c


def textured_chars(g, tex, sel, M_):
    """E2 k-centroid (pz.kcentroid, k=TEXK, line-aware) of the texture pass per cell, snapped in Lab to the material's allowed palette chars"""
    if not sel.any(): return g
    al = tex[..., 3] > 0.5; img = tex[..., :3] * 255; img[~al] = 255
    lo = hx.PZ.kcentroid(img, TEXK, line=True, prefilter=TEXPRE)
    lab = hx.Z.rgb2lab(lo); plab = hx.Z.rgb2lab(hx.RGB)
    d = ((lab[:, :, None, :] - plab[None, None]) ** 2).sum(-1)
    g = g.copy()
    for j in np.unique(M_[sel]):
        allow = (_TX.get('allow', {}).get(MN[j]) or hx.ALLOW.get(MN[j])) if TEXALLOW == 'mat' else None  # R's per-material allow list; 'all' = any key
        cols = [hx.CH[c] for c in allow] if allow else list(range(len(hx.KEYS)))
        m = sel & (M_ == j) & hx.cells(al.astype(float)).mean((2, 3)).__ge__(0.5)
        g[m] = np.array(hx.KEYS)[np.array(cols)[d[m][:, cols].argmin(1)]]
    return g


FEATURE_CHARS = set(os.environ.get('FEATURE_CHARS', 'Wmk'))  # palette feature colours (eye white/highlight, mouth/nose dot, blush): 1 px is a feature


def orphan_rule(g, st):
    """round 6/7, every pixel (faces and textures included): a fill pixel with no same-colour 8-neighbour is an orphan.  A shade speck (a
    neighbour of the same colour class exists, hx.CLS: hair/skin/red/obi/sock...) takes the most common same-class neighbour colour; a lone
    pixel of another class takes the 4-neighbour majority (or folds into the outline when boxed in by K) - unless it is a palette feature
    colour (W, m, k) or a designed thin-feature material (THINF presence-only), which are features, not specks."""
    g = g.copy(); lab = st['lab']; M_ = _mat(lab); H, W = g.shape
    cl = np.vectorize(lambda c: CLS.get(c, c))
    for _ in range(2):
        pg = np.pad(g, 1, constant_values='.'); pc_ = np.pad(cl(g), 1, constant_values='.')
        nb = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
        same = sum((pg[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] == g).astype(int) for dy, dx in nb)
        cand = (g != '.') & (g != 'K') & (same == 0) & (lab >= 0)
        if st.get('txcell') is not None: cand &= ~st['txcell']  # textured (EC0) pixels: its face pass already decided; only the speck rule below
        if not cand.any(): break
        out = g.copy()
        for y, x in zip(*np.nonzero(cand)):
            c0 = pc_[1 + y, 1 + x]
            cs = [pg[1 + y + dy, 1 + x + dx] for dy, dx in nb if pc_[1 + y + dy, 1 + x + dx] == c0 and pg[1 + y + dy, 1 + x + dx] not in '.K']
            if cs: out[y, x] = max(set(cs), key=cs.count); continue
            if g[y, x] in FEATURE_CHARS or (MN[M_[y, x]] in THINF and THINF[MN[M_[y, x]]] < 2): continue
            c4 = [pg[1 + y + dy, 1 + x + dx] for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)) if pg[1 + y + dy, 1 + x + dx] not in '.K']
            if c4: out[y, x] = max(set(c4), key=c4.count)
            else:
                c8 = [pg[1 + y + dy, 1 + x + dx] for dy, dx in nb if pg[1 + y + dy, 1 + x + dx] not in '.K']
                out[y, x] = max(set(c8), key=c8.count) if c8 else 'K'  # a lone fill pixel boxed in by outline folds into the outline
        g = out
    return speck_rule(g)


def speck_rule(g):
    """global: a near-white singleton (W/Q/L) with no skin-class pixel within 2 px is a hair speck (back views), not an eye catchlight -> the
    most common neighbour colour"""
    H, W = g.shape; pg = np.pad(g, 2, constant_values='.')
    skin = np.isin(pg, list('sSmk'))
    near_skin = sum(skin[2 + dy:2 + dy + H, 2 + dx:2 + dx + W] for dy in range(-2, 3) for dx in range(-2, 3)) > 0
    same = sum((pg[2 + dy:2 + dy + H, 2 + dx:2 + dx + W] == g) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    bad = np.isin(g, list('WQL')) & (same == 0) & ~near_skin
    out = g.copy()
    for y, x in zip(*np.nonzero(bad)):
        nb = [pg[2 + y + dy, 2 + x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and pg[2 + y + dy, 2 + x + dx] not in '.K']
        if nb: out[y, x] = max(set(nb), key=nb.count)
    return out


def edge_skin_rule(g):
    """global skin rules at the silhouette: (1) skin pixels touching the outline on the shadow side (light from screen-left/top: the right and
    bottom neighbours) take the skin shadow S - profile jaw/nose/hands read as form; (2) mouth (m) never sits on the silhouette edge -> S"""
    H, W = g.shape; pg = np.pad(g, 1, constant_values='.'); out = g.copy()
    outer = lambda c: c in '.K'
    R_, D_ = pg[1:-1, 2:], pg[2:, 1:-1]; L_, U_ = pg[1:-1, :-2], pg[:-2, 1:-1]
    sh = (g == 's') & ((np.isin(R_, list('.K'))) | (np.isin(D_, list('.K'))))
    # only where the outside really is background beyond the outline (silhouette), not an interior K line
    pg2 = np.pad(g, 2, constant_values='.')
    bg_near = sum((pg2[2 + dy:2 + dy + H, 2 + dx:2 + dx + W] == '.') for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2)) > 0
    out[sh & bg_near] = 'S'
    mo = (g == 'm') & bg_near & ((np.isin(R_, list('.K'))) | np.isin(L_, list('.K')) | np.isin(D_, list('.K')) | np.isin(U_, list('.K')))
    out[mo] = 'S'
    return out


def is_loop(info):
    return len(info['frames']) > 2 and info.get('loop', True) and not str(info['action']).startswith(('jump', 'dash', 'hurt'))


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
        hl, hn = nd.label(hi, np.ones((3, 3)))  # visible pieces in 3D (a limb crossing behind another one is legitimately 2 pieces)
        hcomp = int(sum(1 for k in range(1, hn + 1) if (hl == k).sum() >= P * P)) if hn else 0
        Lc = L | (st['line'] & nd.binary_dilation(L, CROSS) & (g == 'K'))  # an interior line drawn inside the limb does not split it
        sl, sn = nd.label(Lc, np.ones((3, 3)))
        core = nd.binary_opening(np.pad(L, 1), np.ones((2, 2)))[1:-1, 1:-1]
        thin = int((L & ~nd.binary_dilation(core, CROSS)).sum())
        det = 0
        rest = opaque & ~L
        for k in range(1, sn + 1):
            c = (sl == k) & L  # attached = within 1 px of outline of any other figure fill (another piece of the same limb counts:
            if not (nd.binary_dilation(c, np.ones((3, 3)), iterations=2) & opaque & (g != 'K') & ~c).any(): det += 1  # a shin behind its thigh)
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
    view = info['view']; frs = info['frames']; durs = [int(f['ms']) for f in frs]
    G, sts, sh, aud = run(stem, info, opt)
    od = stem + '_px'; os.makedirs(od, exist_ok=True)
    ims, ims_h, grids_h = [], [], []
    for f, g, st in zip(frs, G, sts):
        i = f['i']; hx.save(g, f'{od}/f{i:02d}', view); ims.append(hx.render(g, 4, BG))
    ar = audit_report(aud, frs); json.dump({'summary': ar, 'per_frame': aud}, open(f'{stem}_limbs.json', 'w'), indent=0)
    print('LIMB_AUDIT', os.path.basename(stem), 'PASS' if ar['pass'] else f"FAIL {ar['failed_frames']}/{ar['frames']} frames", json.dumps(ar['fails'])[:400])
    res = {'limb_audit': ar, 'align': sh, 'chain': 'P2', 'opt': opt, 'farleg': [PARTS[s['farleg']] if s['farleg'] is not None else None for s in sts]}
    for tag, I_, G_ in (('', ims, G),):
        if not I_: continue
        gif(I_, durs, f'{stem}{tag}_4x.gif'); sheet(I_, f'{stem}{tag}_sheet.png', [f"f{f['i']:02d}" for f in frs], cols=min(8, len(I_)))
        res['band_churn' + tag] = hx.band_churn(G_) if len(G_) > 1 else None
        print('full', f'{stem}{tag}_4x.gif', sh)
    json.dump(res, open(f'{stem}_px.json', 'w'))


if __name__ == '__main__':
    main()
