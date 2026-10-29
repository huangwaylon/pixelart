"""rl_faceint.py (I, round 8 gate): PREVIEW FACE INTEGRITY.  Flags texture smears on the head in motion (lead, round 8: the illustration
texture streaked across cheek/jaw in walk SE f00, walk E f03, idle SE f06).

Reference = R's smooth preview of the REST pose in the same view, wearing the same expression texture as the frame (render_motion.py rest <V> --preview, cached per rig hash).  For every
motion frame, a similarity transform (scale + rotation + translation, least squares) is fitted from the rest face anchors to the frame's
face anchors (R's per-frame info `face`: eye/brow/cheek/mouth px, visible flags; the anchors are children of the head bone, so this is the
head transform as seen on screen).  Every rest face-skin pixel (skin colour: L > 60, a > 4; inside the anchor hull grown by 2 px, minus discs around the eyes, brows and
mouth, whose expressions legitimately change) is mapped into the frame; it is BAD if the frame colour there differs by dE76 > 25
from the rest colour (the head material is unlit, so the same surface point must keep its colour).
smear = bad / checked per frame; the gate is max smear <= GATE.  Anchors hidden in the frame are dropped; frames with < 3 shared anchors are skipped, and frames
with the head turned > TURN deg (3D turn, not modelled by the 2D fit) are reported separately, not gated.  N/NE/NW (no face) -> n/a."""
import os, json, glob, subprocess
import numpy as np
from PIL import Image

EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
GATE = 0.03
TURN = 12.0   # deg: frames with head |yaw| or |pitch| beyond this vs rest are 3D turns a 2D similarity can't model -> reported, not gated
DE = 25.0
EXCL = {'eye': 3.5, 'brow': 2.0, 'mouth': 3.0}   # 1x px radii of the feature discs left out of the check
NOFACE = ('N', 'NE', 'NW')


def lab(rgb):
    x = rgb.astype(float) / 255.
    x = np.where(x > 0.04045, ((x + 0.055) / 1.055) ** 2.4, x / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = x @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def rest_preview(V, blend, cache, combos=None):
    """rest-pose preview(s) in view V.  combos = list of {face, blink, mouth}: one identity-pose frame per expression (one Blender call),
    so each motion frame is compared with the rest pose wearing the SAME expression texture -> {face_tex: (info frame, rgba)} + '_any'."""
    d = f'{cache}/{V}'; mj = f'{d}/restexpr.json'
    combos = combos or [{}]
    want = json.dumps(combos, sort_keys=True)
    if not (os.path.exists(f'{d}/want.json') and open(f'{d}/want.json').read() == want and glob.glob(f'{d}/restexpr_{V}_f00_pv.png')):
        os.makedirs(d, exist_ok=True)
        for q in glob.glob(f'{d}/*'): os.remove(q)
        M = {'action': 'restexpr', 'fps': 24, 'loop': False, 'timing_ms': [100] * len(combos),
             'frames': [{'t': i, 'root': {'loc': [0, 0, 0]}, 'bones': {}, **{k: v for k, v in c.items() if v is not None}} for i, c in enumerate(combos)]}
        json.dump(M, open(mj, 'w'))
        subprocess.run([BL, '-b', blend, '-P', f'{EXP}/render/render_motion.py', '--', mj, V, d, '--preview', '--no-post'], capture_output=True, text=True)
        open(f'{d}/want.json', 'w').write(want)
    pj = f'{d}/restexpr_{V}.json'
    if not os.path.exists(pj): return None
    info = json.load(open(pj)); ref = {}
    for f in info['frames']:
        p = f"{d}/restexpr_{V}_f{f['i']:02d}_pv.png"
        if os.path.exists(p): ref.setdefault(f.get('face_tex') or '_any', (f, np.array(Image.open(p).convert('RGBA'))))
    if ref: ref['_any'] = ref.get('_any') or next(iter(ref.values()))
    return {'info': info, 'ref': ref}


def _pts(face, SC, dxdy, names=None):
    out = {}
    for k, v in (face or {}).items():
        if k.startswith('_') or 'px' not in v: continue
        if names is not None and k not in names: continue
        out[k] = (np.array([(v['px'][0] + 32 - dxdy[0]) * SC, (v['px'][1] + 32 - dxdy[1]) * SC]), bool(v.get('visible', True)))
    return out


def similarity(A, B):
    """least-squares similarity B ~ s R A + t (Umeyama)"""
    ma, mb = A.mean(0), B.mean(0); a, b = A - ma, B - mb
    U, S, Vt = np.linalg.svd(b.T @ a / len(A)); D = np.eye(2)
    if np.linalg.det(U @ Vt) < 0: D[1, 1] = -1
    R = U @ D @ Vt; s = (S * np.diag(D)).sum() / max(1e-9, (a ** 2).sum() / len(A))
    return s * R, mb - s * R @ ma


def check(pv_dir, stem, V, rest):
    if V in NOFACE or not rest or not rest.get('ref'): return None
    info = json.load(open(f'{pv_dir}/{stem}.json')); SC = info['scale']; dxdy = info.get('out_dxdy', [0, 0])
    prep = {}

    def region(key):
        if key in prep: return prep[key]
        rf, rimg = rest['ref'].get(key) or rest['ref']['_any']
        rP = _pts(rf.get('face'), SC, dxdy); H, W = rimg.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]
        hull = np.array([p for p, vis in rP.values() if vis])
        if len(hull) < 3: prep[key] = None; return None
        x0, y0 = hull.min(0) - 2 * SC; x1, y1 = hull.max(0) + 2 * SC
        reg = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1) & (rimg[..., 3] > 200)
        for k, (p, _) in rP.items():
            r = next((v for n, v in EXCL.items() if k.startswith(n)), None)
            if r: reg &= (xx - p[0]) ** 2 + (yy - p[1]) ** 2 > (r * SC) ** 2
        Lr = lab(rimg[..., :3]); reg &= (Lr[..., 0] > 60) & (Lr[..., 1] > 4)  # rest SKIN only (hair moves with its springs, legitimately)
        ys, xs = np.nonzero(reg); prep[key] = (rP, np.stack([xs, ys], 1).astype(float), Lr[ys, xs], W, H, key in rest['ref'])
        return prep[key]
    res = []
    for k, f in enumerate(info['frames']):
        R_ = region(f.get('face_tex') or '_any')
        if R_ is None: res.append({'i': f['i'], 'smear': None, 'skip': 'rest anchors'}); continue
        rP, P0, L0, W, H, same_expr = R_
        fP = _pts(f.get('face'), SC, dxdy)
        common = [n for n in rP if n in fP and rP[n][1] and fP[n][1]]   # anchors visible in both (far-side / occluded ones dropped)
        hd = (f.get('face') or {}).get('_head') or {}
        turned = max(abs(hd.get('yaw', 0)), abs(hd.get('pitch', 0))) > TURN
        if len(common) < 3:
            res.append({'i': f['i'], 'smear': None, 'skip': 'anchors'}); continue
        A = np.array([rP[n][0] for n in common]); B = np.array([fP[n][0] for n in common]); M, t = similarity(A, B)
        q = np.rint(P0 @ M.T + t).astype(int)
        p = f"{pv_dir}/{stem}_f{f['i']:02d}_pv.png"
        if not os.path.exists(p): res.append({'i': f['i'], 'smear': None, 'skip': 'no frame'}); continue
        img = np.array(Image.open(p).convert('RGBA'))
        ok = (q[:, 0] >= 0) & (q[:, 0] < W) & (q[:, 1] >= 0) & (q[:, 1] < H)
        qq = q[ok]; al = img[qq[:, 1], qq[:, 0], 3] > 200
        L1 = lab(img[qq[al, 1], qq[al, 0], :3]); de = np.sqrt(((L1 - L0[ok][al]) ** 2).sum(-1))
        bad = de > DE
        res.append({'i': f['i'], 'smear': round(float(bad.mean()) if len(bad) else 0.0, 4), 'checked': int(len(bad)), 'turned': turned,
                    'yaw': hd.get('yaw'), 'pitch': hd.get('pitch'), 'expr_ref': same_expr, 'face_tex': f.get('face_tex'),
                    'fit_err_px': round(float(np.abs(A @ M.T + t - B).max() / SC), 2)})
    G = [r for r in res if r['smear'] is not None and not r.get('turned')]; vals = [r['smear'] for r in G]
    T = [r for r in res if r['smear'] is not None and r.get('turned')]
    return {'max': max(vals) if vals else None, 'mean': round(float(np.mean(vals)), 4) if vals else None,
            'bad_frames': [r['i'] for r in G if r['smear'] > GATE], 'gated': len(G),
            'turned_max': max((r['smear'] for r in T), default=None), 'turned': len(T),
            'skipped': sum(1 for r in res if r['smear'] is None), 'frames': res}
