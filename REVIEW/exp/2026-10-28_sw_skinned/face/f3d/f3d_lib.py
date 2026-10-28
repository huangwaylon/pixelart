"""f3d_lib.py (F, round 5) -- hi-res anime face TEXTURES for the 3D head (no pixel art on the mesh; the standard chain pixelizes them).

The m96 face (FACE_SPEC.md / eye_spec.json) is the DESIGN reference: shapes, proportions and colours are redrawn here as smooth vector art
(ellipses, thick bezier strokes) at 1024^2, in a planar UV over the head-bone frame.  Every feature is an ordinary MATERIAL (matid colour
in the guide pass, a flat palette ramp in the chain), so the pixel chain treats the face like any other surface.

UV contract (face_uv): head-bone REST frame (x = bone X (+x = screen right in the S view), y = along the bone (up), z = her front);
planar projection along -z:  u = (x - X0) / (X1 - X0),  v = (y - Y0) / (Y1 - Y0),  X0,X1,Y0,Y1 = -0.16, 0.16, -0.06, 0.26 m.
Only skin faces of the head with a front-facing rest normal (z_n > 0.15) carry the UV (others -> (-1,-1), the texture is CLIP-extended).
Texture: face_<key>_mid.png (matid colours, alpha = feature) + face_<key>_pv.png (palette colours, for the smooth preview), 1024^2 RGBA.
Design units: m96 S-master pixel coordinates (col, row), mapped to the head frame by
   x = (col - 64.0) * PXX,   y = Y_EYE + (52.0 - row) * PXY,    PXX = 1/67.88 m (one 1x sprite px), PXY = PXX / cos(30 deg) (camera elevation),
   Y_EYE = 0.125 m (iris line of the S master, ray-cast on the rest head).
Keys: <expr>[+b<half|closed>][+m<open|closed>]  (expr names as face_lib.EXPR)."""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); FACE = os.path.dirname(HERE); EXP = os.path.dirname(FACE)
sys.path.insert(0, FACE)
import face_lib as FL  # noqa: E402  (expression semantics: resolve(), names, aliases)
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
TEXN = int(os.environ.get('F3D_TEX', '1024'))
X0, X1, Y0, Y1 = -0.16, 0.16, -0.06, 0.26
PXX = 1 / 67.88; PXY = PXX / math.cos(math.radians(30)); Y_EYE = 0.125
CX = 64.0
# ---- feature materials (matid colour in the guide pass; ramp = flat palette char)
# ---- feature materials = ordinary materials of the chain.  eye_white / iris / lash / mouth / blush: R's rig/face_mats.json colours;
# iris_top / iris_low / brow / mouth_in / nose: F's additions (agreed in CONTRACT round 5; R adds them to face_mats.json, P the ramps)
_FM = json.load(open(os.path.join(EXP, 'rig', 'face_mats.json')))['mats'] if os.path.exists(os.path.join(EXP, 'rig', 'face_mats.json')) else {}
F_ADD = {'iris_top': (0, 128, 255), 'iris_low': (128, 255, 0), 'brow': (255, 128, 0), 'mouth_in': (255, 0, 128), 'nose': (0, 255, 255)}
_DEF = {'eye_white': (236, 236, 246), 'iris': (88, 64, 120), 'lash': (24, 16, 32), 'mouth': (190, 80, 90), 'blush': (235, 140, 150)}
RAMPS = {'lash': 'KKK', 'iris_top': 'hhh', 'iris': 'ggg', 'iris_low': 'LLL', 'eye_white': 'WWW', 'brow': 'ggg', 'mouth': 'mmm', 'mouth_in': 'RRR',
         'blush': 'kkk', 'nose': 'SSS'}
MATS = {m: (tuple(_FM.get(m, F_ADD.get(m, _DEF.get(m)))) if m in _FM else tuple(F_ADD.get(m, _DEF.get(m))), RAMPS[m]) for m in RAMPS}
PV = {m: r[0] for m, r in RAMPS.items()}
# feature size knobs (sprite px), tuned by rendering + pixelizing (f3d_iter)
K = dict(closed=float(os.environ.get('F3D_CLOSED', '1.35')), lash=float(os.environ.get('F3D_LASH', '1.0')), brow=float(os.environ.get('F3D_BROW', '1.3')), mouth=float(os.environ.get('F3D_MOUTH', '1.05')),
         iris_rx=float(os.environ.get('F3D_IRX', '2.05')), iris_ry=float(os.environ.get('F3D_IRY', '1.85')),
         catch=float(os.environ.get('F3D_CATCH', '1.3')), blush=float(os.environ.get('F3D_BLUSH', '1.0')))


_FIT = json.load(open(os.path.join(HERE, 'uvfit.json'))) if os.path.exists(os.path.join(HERE, 'uvfit.json')) and os.environ.get('F3D_NOFIT') != '1' else None


def _feats(x, y): return np.array([1, x, y, x * x, x * y, y * y, x ** 3, x * x * y, x * y * y, y ** 3], float)


def to_px(col, row):
    """m96 S design coords -> texture pixel coords: the calibrated fit on the real head (f3d_fit.py: features land on the master's S rows/cols),
    else the analytic planar map"""
    if _FIT:
        f = _feats(col - 64, row - 52); return float(f @ np.array(_FIT['cu'])) * TEXN / 1024, float(f @ np.array(_FIT['cv'])) * TEXN / 1024
    x = (col - CX) * PXX; y = Y_EYE + (52.0 - row) * PXY
    return (x - X0) / (X1 - X0) * TEXN, (Y1 - y) / (Y1 - Y0) * TEXN


_j = (to_px(65, 52)[0] - to_px(63, 52)[0]) / 2, (to_px(64, 53)[1] - to_px(64, 51)[1]) / 2
SX, SY = abs(_j[0]), abs(_j[1])   # texels per sprite px (x, y) at the face centre


class Canvas:
    def __init__(self, size=None):
        self.im = Image.new('RGBA', size or (TEXN, TEXN), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)

    def col(self, m): return MATS[m][0] + (255,)

    def ellipse(self, m, c, rx, ry):
        x, y = to_px(*c); self.d.ellipse([x - rx * SX, y - ry * SY, x + rx * SX, y + ry * SY], fill=self.col(m))

    def stroke(self, m, pts, w, taper=None):
        """thick polyline through m96-coord points (Catmull-Rom smoothed), width w sprite px (optionally tapered list)"""
        P_ = [to_px(*p) for p in pts]
        sm = []
        for i in range(len(P_) - 1):
            p0 = P_[max(0, i - 1)]; p1 = P_[i]; p2 = P_[i + 1]; p3 = P_[min(len(P_) - 1, i + 2)]
            for t in np.linspace(0, 1, 16, endpoint=False):
                t2, t3 = t * t, t * t * t
                sm.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
        sm.append(P_[-1])
        n = len(sm)
        for i, (x, y) in enumerate(sm):
            ww = w * (taper[0] + (taper[1] - taper[0]) * i / max(1, n - 1)) if taper else w
            r = ww * (SX + SY) / 4
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=self.col(m))

    def poly(self, m, pts):
        self.d.polygon([to_px(*p) for p in pts], fill=self.col(m))


# ---------------------------------------------------------------- the eye (screen-left eye in m96 S coords; right eye = mirrored lid,
# unmirrored iris highlight side).  ox = column offset of the eye (left 0, right +10 = master front_right x0 66 vs 56).
def iris(cv, cx, cy, rx, ry, clip_top=None, clip_bot=None):
    """iris ellipse in 3 bands (h top, g middle, L bottom), pupil K right of centre, catchlight W 1x2 upper-left"""
    x, y = to_px(cx, cy); X0_, X1_ = x - rx * SX, x + rx * SX; Y0_, Y1_ = y - ry * SY, y + ry * SY
    lay = Image.new('RGBA', cv.im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([X0_, Y0_, X1_, Y1_], fill=cv.col('iris'))
    band = Image.new('L', cv.im.size, 0); bd = ImageDraw.Draw(band)
    bd.rectangle([0, 0, TEXN, y - ry * SY * float(os.environ.get('F3D_IRTOP', '0.25'))], fill=1)      # top -> h
    bd.rectangle([0, y + ry * SY * float(os.environ.get('F3D_IRLOW', '0.62')), TEXN, TEXN], fill=2)   # bottom rim -> L
    a = np.array(lay); b = np.array(band); m = a[..., 3] > 0
    a[m & (b == 1), :3] = MATS['iris_top'][0]; a[m & (b == 2), :3] = MATS['iris_low'][0]
    lay = Image.fromarray(a); d = ImageDraw.Draw(lay)
    px_, py_ = to_px(cx + 0.55, cy - 0.05)
    d.ellipse([px_ - 0.62 * SX, py_ - 0.85 * SY, px_ + 0.62 * SX, py_ + 0.85 * SY], fill=cv.col('lash'))
    cx_, cy_ = to_px(cx - 0.55, cy - 0.45); c = K['catch']
    d.ellipse([cx_ - 0.55 * c * SX, cy_ - 0.95 * c * SY, cx_ + 0.55 * c * SX, cy_ + 0.95 * c * SY], fill=cv.col('eye_white'))
    if clip_top is not None or clip_bot is not None:
        a = np.array(lay)
        if clip_top is not None: a[:int(to_px(0, clip_top)[1])] = 0
        if clip_bot is not None: a[int(to_px(0, clip_bot)[1]):] = 0
        lay = Image.fromarray(a)
    cv.im.alpha_composite(lay)


def eye(cv, side, state):
    """side 'L' (screen-left, outer corner on the left) | 'R'; state: open, focused, surprised, half, closed, joy, effort, pain"""
    s = 1 if side == 'L' else -1
    mx = lambda c: c if side == 'L' else 2 * CX - c   # mirror the lid geometry about the face centre
    ic = 59.0 if side == 'L' else 69.0                  # iris centre column (left / right eye)
    W = K['lash']
    if state in ('open', 'focused', 'surprised', 'half'):
        lift = {'open': 0.0, 'focused': 0.0, 'surprised': -0.9, 'half': 1.0}[state]
        iy = 52.55 + (-0.25 if state == 'surprised' else 0)
        iry = K['iris_ry'] * (1.12 if state == 'surprised' else 1.0)
        iris(cv, ic, iy, K['iris_rx'], iry, clip_top=50.6 + lift + 0.2 if state == 'half' else None)
        # upper lash: thick dome, outer corner low + thick, inner end thinner; wing up-and-out from the outer end
        lid = [(mx(55.9), 52.0 + lift * 0.5), (mx(56.9), 50.95 + lift), (mx(58.6), 50.45 + lift), (mx(60.3), 50.7 + lift), (mx(61.0), 51.3 + lift)]
        cv.stroke('lash', lid, W, taper=(1.25, 0.7))
        cv.stroke('lash', [(mx(56.4), 51.0 + lift), (mx(55.3), 50.2 + lift)], W * 0.85, taper=(1.0, 0.6))   # cat-eye wing
        if state == 'surprised':
            cv.stroke('lash', [(mx(57.2), 49.55), (mx(59.0), 49.15), (mx(60.6), 49.6)], W * 0.7)
        if state == 'focused':   # raised lower lid line (intent glare)
            cv.stroke('lash', [(mx(57.0), 54.05), (mx(59.0), 54.3), (mx(60.9), 53.95)], W * 0.95)
    W = max(W, K.get('closed', 1.35)) if state in ('closed', 'joy', 'effort', 'pain') else W   # 1-px closed-eye lines need >= 1.35 px to survive the vote
    if state == 'closed':      # U arc + wing
        cv.stroke('lash', [(mx(55.8), 52.6), (mx(57.4), 53.75), (mx(59.3), 53.9), (mx(60.9), 53.35)], W, taper=(1.2, 0.8))
        cv.stroke('lash', [(mx(56.1), 52.9), (mx(55.2), 52.3)], W * 0.8)
    elif state == 'joy':         # n arc (^)
        cv.stroke('lash', [(mx(56.0), 53.0), (mx(57.2), 51.6), (mx(58.6), 51.25), (mx(60.0), 51.7), (mx(60.9), 52.9)], W)
        cv.stroke('lash', [(mx(56.2), 52.6), (mx(55.3), 52.0)], W * 0.8)
    elif state == 'effort':      # squeezed: slanted line stepping down toward the nose
        cv.stroke('lash', [(mx(55.9), 51.6), (mx(57.8), 51.8), (mx(59.5), 52.7), (mx(61.0), 52.8)], W * 1.05)
    elif state == 'pain':        # > (left) / < (right) chevron
        cv.stroke('lash', [(mx(56.0), 50.6), (mx(58.0), 51.4), (mx(60.6), 51.9)], W)
        cv.stroke('lash', [(mx(60.6), 51.9), (mx(58.0), 52.5), (mx(56.0), 53.3)], W)


BROWS = {   # m96 brow rows 46-48 (lash-4..lash-2) for the screen-left eye; inner end (toward the nose) = right
    'neutral': [(57.2, 48.7), (58.4, 47.75), (60.0, 47.55), (61.3, 47.8)],
    'cheerful': [(57.2, 47.7), (58.4, 46.75), (60.0, 46.55), (61.3, 46.8)],
    'surprised': [(57.0, 47.9), (58.2, 46.5), (59.8, 46.2), (61.2, 46.9)],
    'determined': [(56.9, 46.4), (58.6, 46.9), (60.1, 47.8), (61.3, 48.6)],
    'focused': [(56.9, 47.3), (58.6, 47.8), (60.1, 48.7), (61.2, 49.5)],
    'pain': [(57.0, 48.6), (58.6, 48.3), (60.2, 47.5), (61.2, 46.9)],
    'embarrassed': [(57.2, 48.2), (58.6, 47.9), (60.2, 47.3), (61.2, 46.8)],
}
BROW_OF = {'neutral': 'neutral', 'blink_half': 'neutral', 'blink_closed': 'neutral', 'cheerful': 'cheerful', 'joy': 'cheerful', 'surprised': 'surprised',
           'determined': 'determined', 'effort': 'determined', 'shout': 'determined', 'focused': 'focused', 'pain': 'pain', 'embarrassed': 'embarrassed'}


def brows(cv, kind, only=None):
    pts = BROWS[BROW_OF.get(kind, 'neutral')]
    dy = float(os.environ.get('F3D_BROWDY', '0.6'))   # brows a little under the fringe edge (the chain's hair|face line sits on the edge)
    for side in (only or 'LR'):
        p = [(x, y + dy) for x, y in pts] if side == 'L' else [(2 * CX - x, y + dy) for x, y in pts]
        cv.stroke('brow', p, K['brow'], taper=(0.9, 1.1))


def mouth(cv, m):
    """mouth by face_lib template name (or a list template from face_lib) -> smooth shapes; centred on the m96 S mouth (cols 62-65, rows 56-58)"""
    key = m if isinstance(m, str) else {tuple(FL.SMILE_CLOSED): 'smile', tuple(FL.MOUTH_FLAT): 'flat', tuple(FL.MOUTH_SMALL_O): 'o',
                                         tuple(FL.MOUTH_GRIT): 'grit', tuple(FL.MOUTH_GRIT_OPEN): 'grit_open', tuple(FL.MOUTH_HURT): 'frown',
                                         tuple(FL.MOUTH_FOCUS): 'focus'}.get(tuple(m), 'neutral')
    W = K['mouth']
    if key in ('neutral', 'blink_half', 'blink_closed', 'embarrassed'):
        cv.stroke('mouth', [(62.9, 57.5), (64.0, 57.62), (65.1, 57.5)], W)
    elif key == 'smile':
        cv.stroke('mouth', [(62.3, 57.2), (63.2, 58.2), (64.8, 58.2), (65.7, 57.2)], W)
    elif key == 'flat' or key == 'determined':
        cv.stroke('mouth', [(62.3, 57.5), (65.7, 57.5)], W)
    elif key == 'focus':
        cv.stroke('mouth', [(62.4, 57.5), (64.9, 57.5)], W)
    elif key == 'frown':
        cv.stroke('mouth', [(62.3, 58.6), (63.3, 57.6), (64.7, 57.6), (65.7, 58.6)], W)
    elif key in ('cheerful', 'joy'):
        big = key == 'joy'
        cv.poly('mouth_in', [(62.0, 56.4), (66.0, 56.4), (65.3, 57.9 + big * 0.6), (64.0, 58.4 + big * 0.8), (62.7, 57.9 + big * 0.6)])
        if big: cv.ellipse('blush', (64.0, 58.4), 1.0, 0.55)
    elif key == 'o':
        cv.ellipse('mouth_in', (64.0, 57.9), 1.05, 1.0)
    elif key in ('grit', 'grit_open'):
        cv.poly('mouth', [(62.2, 56.9), (65.8, 56.9), (65.8, 58.15), (62.2, 58.15)])
        cv.poly('eye_white', [(62.85, 57.2), (65.15, 57.2), (65.15, 57.85), (62.85, 57.85)])
        if key == 'grit_open': cv.ellipse('mouth_in', (64.0, 58.6), 1.0, 0.55)
    elif key in ('shout', 'effort', 'pain'):
        cv.ellipse('mouth_in', (64.0, 57.9), 1.6, 1.25)
    else:
        cv.stroke('mouth', [(62.9, 57.5), (65.1, 57.5)], W)


def blush(cv, kind):
    if kind is None: return
    r = K['blush'] * (1.12 if kind in ('cheerful', 'joy', 'embarrassed') else 1.0)
    for c in (58.9, 69.1): cv.ellipse('blush', (c, 56.0), 2.05 * r, 0.95 * r)


EYE_STATE = {'neutral': 'open', 'cheerful': 'open', 'determined': 'open', 'shout': 'open', 'embarrassed': 'open', 'focused': 'focused',
             'surprised': 'surprised', 'blink_half': 'half', 'blink_closed': 'closed', 'joy': 'joy', 'effort': 'effort', 'pain': 'pain'}


def face_key(expr, blink=None, mouth_=None):
    k = FL.ALIASES.get(expr, expr) if expr else 'neutral'
    if isinstance(blink, (int, float)) and not isinstance(blink, bool): blink = 'closed' if blink >= 0.75 else ('half' if blink >= 0.25 else None)
    return k + (f'+b{blink}' if blink in ('half', 'closed') else '') + (f'+m{mouth_}' if mouth_ in ('open', 'closed') else '')


# ---------------------------------------------------------------- profile (E / W) side features
# The masters draw the profile eye/brow/blush much further round the head than the S design: in E the S-design eye sits at the front corner
# and foreshortens to nothing (P: "no face in E").  The side of the head (texture u < SIDE_U, mirrored for W) carries the m96 E-profile
# eye/brow/blush, placed by INVERSE warping through the E calibration (out/calR/rest_E: texel -> E sprite px), so they land on the E master
# position and size.  In S that strip is the cheek edge under the side locks; in SE it extends the near eye's outer corner (the 3D "wrap" cheat).
SIDE_U = int(os.environ.get('F3D_SIDEU', '72')); E_OFF = 16   # E master profile eye x0 72 = S left eye x0 56 + 16
_SIDE = None


def _side_map():
    global _SIDE
    if _SIDE is None:
        p = os.path.join(HERE, 'out', 'calR', 'rest_E_f00_guide.png')
        if not os.path.exists(p): _SIDE = False; return _SIDE
        al = json.load(open(os.path.join(EXP, 'rig', 'align.json')))['E']; lift = (al['dx'] - al.get('reg_dx', al['dx']), al['dy'] - al.get('reg_dy', al['dy']))
        a = np.array(Image.open(p).convert('RGBA')).astype(float); m = (a[..., 3] > 250) & (np.abs(a[..., 2] - 77) <= 2); ys, xs = np.nonzero(m)
        sx = (xs + .5) / 8 - 32 + al['dx'] - lift[0]; sy = (ys + .5) / 8 - 32 + al['dy'] - lift[1]
        u = a[ys, xs, 0] / 255 * TEXN; v = a[ys, xs, 1] / 255 * TEXN
        from scipy.interpolate import griddata
        keep = u < SIDE_U + 24
        gu, gv = np.meshgrid(np.arange(SIDE_U) + .5, np.arange(TEXN) + .5)
        cx = griddata((u[keep], v[keep]), sx[keep], (gu, gv), method='linear'); cy = griddata((u[keep], v[keep]), sy[keep], (gu, gv), method='linear')
        _SIDE = (cx, cy)
    return _SIDE


def side_layer(ex, eL):
    """RGBA texture layer with the E-profile eye/brow/blush for the left side (u < SIDE_U) and its mirror (right side)"""
    sm = _side_map()
    if not sm: return None
    global to_px, SX, SY
    S0 = 16; ox, oy = 50.0, 42.0
    keep = (to_px, SX, SY)
    to_px = lambda c, r: ((c - ox) * S0, (r - oy) * S0); SX = SY = S0
    try:
        cv = Canvas((20 * S0, 20 * S0))
        if ex['blush'] is not None: cv.ellipse('blush', (57.6, 56.0), 1.6 * K['blush'], 0.95 * K['blush'])   # E blush (72,55) front patch, E_OFF-shifted
        brows(cv, ex['brow'], only='L')
        eye(cv, 'L', eL)
    finally:
        to_px, SX, SY = keep
    R = np.array(cv.im); cx, cy = sm
    gx = ((cx - E_OFF) - ox) * S0; gy = (cy - oy) * S0
    ok = np.isfinite(gx) & np.isfinite(gy) & (gx >= 0) & (gy >= 0) & (gx < R.shape[1]) & (gy < R.shape[0])
    lay = np.zeros((TEXN, TEXN, 4), np.uint8)
    sub = np.zeros((TEXN, SIDE_U, 4), np.uint8); sub[ok] = R[gy[ok].astype(int), gx[ok].astype(int)]
    lay[:, :SIDE_U] = sub; lay[:, TEXN - SIDE_U:] = np.maximum(lay[:, TEXN - SIDE_U:], sub[:, ::-1])
    return Image.fromarray(lay)


def draw(key):
    """key -> (mid RGBA, pv RGBA) images"""
    parts = key.split('+'); e = parts[0]; b = next((p[1:] for p in parts if p.startswith('b')), None); mo = next((p[1:] for p in parts if p.startswith('m')), None)
    ex = FL.resolve(e, b, mo)
    cv = Canvas()
    blush(cv, ex['blush'])
    cv.ellipse('nose', (63.55, 55.0), 0.55, 0.95)
    brows(cv, ex['brow'])
    eL = EYE_STATE.get(FL.ET.expr_key(ex['eye']), 'open'); eR = eL
    if ex.get('wink'): eL = 'joy'
    if ex.get('eye1'): eR = EYE_STATE.get(FL.ET.expr_key(ex['eye1']), eR)
    eye(cv, 'L', eL); eye(cv, 'R', eR)
    if ex.get('tear'):
        for c in (56.6, 71.4): cv.poly('eye_white', [(c - 0.45, 54.2), (c + 0.45, 54.2), (c + 0.5, 56.2), (c - 0.5, 56.2)])
    mouth(cv, ex['mouth'])
    mid = cv.im
    if os.environ.get('F3D_SIDE', '1') == '1':
        sl = side_layer(ex, eL)
        if sl is not None: sl.alpha_composite(mid); mid = sl   # front (S design) features win where they overlap
    a = np.array(mid); pv = np.zeros_like(a)
    sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
    import hx
    rgb = {k: hx.RGB[i] for i, k in enumerate(hx.KEYS)}
    for m, (c, _) in MATS.items():
        sel = (a[..., 3] > 0) & np.all(a[..., :3] == c, -1); pv[sel, :3] = rgb[PV[m]]; pv[sel, 3] = 255
    return mid, Image.fromarray(pv)


ALL_EXPR = ['neutral', 'smile', 'smile_open', 'joyful', 'determined', 'focused', 'effort', 'strain', 'shout', 'surprised', 'squint', 'hurt', 'wince',
            'hurt_tear', 'wink', 'blink', 'half_blink']


def r_name(expr, blink=None, mouth_=None):
    """R's render_motion.face_tex() file name: <face>[_blink|_half][_open]"""
    return '_'.join(x for x in (expr, {'closed': 'blink', 'half': 'half'}.get(blink, ''), 'open' if mouth_ == 'open' else '') if x)


M_NAMES = {'joyful': ['joyful', 'joy'], 'smile_open': ['smile_open', 'cheerful'], 'hurt': ['hurt', 'pain', 'pained'], 'squint': ['squint', 'land'],
           'focused': ['focused', 'dash'], 'blink': ['blink', 'blink_closed'], 'half_blink': ['half_blink', 'blink_half']}


def build(keys=None, od=None):
    """face/tex3d/<name>.png (matid-coded, alpha 0 = keep base skin) + <name>_col.png (palette colours, preview), every expression x
    (open | half | blink) x (default | open mouth), in R's lookup naming; aliases are written as copies"""
    od = od or os.path.join(FACE, 'tex3d'); os.makedirs(od, exist_ok=True)
    keys = []
    for e in ALL_EXPR:
        for b in (None, 'half', 'closed'):
            for m in (None, 'open'):
                k = face_key(e, b, m); mid, pv = draw(k); keys.append(k)
                for nm in M_NAMES.get(e, [e]):
                    n = r_name(nm, b, m); mid.save(f'{od}/{n}.png'); pv.save(f'{od}/{n}_col.png')
    json.dump({'uv': 'R face_uv (rig/build_head3d.py), layout calibrated by face/f3d/f3d_fit.py', 'fit': _FIT, 'tex': TEXN, 'mats': {m: list(c) for m, (c, r) in MATS.items()}, 'ramps': {m: r for m, (c, r) in MATS.items()},
               'keys': keys, 'knobs': K}, open(f'{od}/face_tex3d.json', 'w'), indent=1)
    print('face textures', len(keys), '->', od)


if __name__ == '__main__':
    build()
