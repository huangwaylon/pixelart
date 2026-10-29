"""r10.py (F, round 10): 1x-readable eyes/mouth in the expression illustrations, on top of the round-9 set (out_r9/), face region only.
  - SE (-> SW by R's flip): every OPEN eye becomes a solid dark almond (the eye's own non-skin shape, hull-filled: iris dark, lash band darker on top)
    with one bright 1.4 x 2 sprite-px catchlight and no white sclera/outline box (that pixelized into "glasses").
  - every CLOSED eye (blink, joyful, squint, hurt, wince-left) in S/SE/E becomes ONE thick curved lash stroke (skeleton of the main dark line,
    redrawn ~1.5 sprite px thick); the other dark fragments in the eye are cleared to skin (blinks left fragments).
  - effort mouths (mouth source 'effort'): a solid dark mouth shape with a 1 sprite-px white teeth band.
  - S: open eyes 1.1x more (iris), skin around the eyes 6 % lighter.
  python r10.py [S SE E]   -> out_r10/<V>/*.png + face_mask.png (+ index.json); OUTDIR overrides"""
import os, sys, json, glob, re
import numpy as np, cv2
from PIL import Image
from skimage.morphology import skeletonize
D = os.path.dirname(os.path.abspath(__file__)); SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
sys.path.insert(0, D)
import compose as C
import enhance as E
PX = 13.5   # illustration px per 1x sprite px (figure ~1300 px tall -> 96 px)
DARK, LASHC, MOUTHC = (58, 38, 40), (24, 14, 18), (92, 28, 38)


def lum(a): return a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114


def eye_state(nm):
    """(left_closed, right_closed, mouth_src) for a file name <face>[_half|_blink][_open] (screen left/right eye)"""
    parts = nm.split('_'); m = 'open' if parts[-1] == 'open' else ''
    if m: parts = parts[:-1]
    b = parts[-1] if parts[-1] in ('half', 'blink') else ''
    if b: parts = parts[:-1]
    e = '_'.join(parts); e = C.ALIAS.get(e, e)
    if e not in C.EXPR: return None
    eyes, mc, mo, closed = C.EXPR[e]
    ms = mo if m else mc
    if b == 'blink': return True, True, ms
    if isinstance(eyes, tuple): return eyes[0] in ('hurt', 'squint', 'blink', 'joyful'), b == 'blink', ms
    if closed: return True, True, ms
    return False, False, ms


def ellipse_mask(shape, c, ax, feather=2):
    m = np.zeros(shape, np.float32); cv2.ellipse(m, (int(c[0]), int(c[1])), (int(ax[0]), int(ax[1])), 0, 0, 360, 1.0, -1)
    return cv2.GaussianBlur(m, (0, 0), feather) if feather else m


def skin_of(img, mask):
    a = img[(mask > 128) & (lum(img) > 170) & (img[..., 0] > img[..., 1]) & (img[..., 1] > img[..., 2])]
    return np.median(a, 0) if len(a) else np.array([245, 205, 185], float)


def box_mask(shape, e, k=1.0):
    x, y, w, h = e['box']; cx, cy = x + w / 2, y + h / 2
    return ellipse_mask(shape, (cx, cy), (w * 0.5 * 1.22 * k, h * 0.5 * 1.22 * k), 0) > 0.5


def open_almond(img, blink, e, skin):
    """solid dark almond = hull of the eye content (pixels that differ from the blink drawing) inside the eye box; catchlight 1.4 x 2 px"""
    H, W = img.shape[:2]; em = box_mask((H, W), e, 1.05)
    ns = em & (np.abs(img - blink).max(-1) > 40) & (np.abs(img - skin).max(-1) > 30)
    ns = cv2.morphologyEx(ns.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    ns = cv2.morphologyEx(ns, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(ns)
    if n < 2: return img
    k = 1 + int(np.argmax(st[1:, 4])); cnts, _ = cv2.findContours((lab == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(max(cnts, key=cv2.contourArea)).astype(np.float32); mc = hull.reshape(-1, 2).mean(0)
    hull = (mc + (hull - mc) * float(os.environ.get('ALMOND', '0.86'))).astype(np.int32)   # a bit smaller than the bulged eye
    out0 = img.copy(); out0[em & (np.abs(img - skin).max(-1) > 30) & (np.abs(img - blink).max(-1) > 40)] = skin; img = out0
    fill = np.zeros((H, W), np.uint8); cv2.fillPoly(fill, [hull], 1); f = fill > 0
    x, y, ww, hh = cv2.boundingRect(hull); out = img.copy()
    out[f] = DARK; out[f & (np.arange(H)[:, None] < y + hh * 0.3)] = LASHC
    cm = np.zeros((H, W), np.uint8); cv2.ellipse(cm, (int(x + ww * 0.36), int(y + hh * 0.45)), (int(0.7 * PX), int(1.0 * PX)), 0, 0, 360, 1, -1)
    out[(cm > 0) & f] = 255
    return out


def closed_stroke(img, e, skin, curve=True, arc='U'):
    """closed eye -> ONE thick curved lash stroke: the eye's dark pixels (in the eye box) fitted by a quadratic (blink/joy) or kept and thickened (> <)"""
    H, W = img.shape[:2]; em = box_mask((H, W), e, 1.0); emc = box_mask((H, W), e, 1.3)
    dk = em & (lum(img) < 110)
    n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.morphologyEx(dk.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)))
    out = img.copy(); ns = emc & (np.abs(img - skin).max(-1) > 30) & ~(lum(img) < 70) | (emc & (lum(img) > 225)); ns &= emc; out[ns] = skin     # clear the eye box (no fragments)
    if n < 2: return out
    keep = [k for k in range(1, n) if st[k, 4] >= 0.25 * st[1:, 4].max()]
    main = np.isin(lab, keep)
    if curve:
        ys, xs = np.nonzero(main); cs = np.unique(xs)
        if len(cs) >= 5:
            my = np.array([ys[xs == c].mean() for c in cs]); pf = np.polyfit(cs, my, 2)
            half = (cs.max() - cs.min()) / 2; sag = 0.6 * PX / max(half, 1) ** 2      # >= 0.6 sprite px of curvature
            pf[0] = min(pf[0], -sag) if arc == 'U' else max(pf[0], sag)
            xm = (cs.max() + cs.min()) / 2; pf[1] = -2 * pf[0] * xm; pf[2] = np.mean(my) - np.polyval([pf[0], pf[1], 0], cs).mean()
            pts = np.stack([cs, np.polyval(pf, cs)], 1).astype(np.int32)
            cv2.polylines(out, [pts.reshape(-1, 1, 2)], False, LASHC, int(1.3 * PX), cv2.LINE_AA)
            return out
    th = cv2.dilate(main.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
    out[th] = LASHC
    return out


def effort_mouth(img, base, ysplit, core, skin):
    H, W = img.shape[:2]
    d = (np.abs(img - base).max(-1) > 40) & core; d[:ysplit + 8] = False
    d = cv2.morphologyEx(d.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(d)
    if n < 2: return img
    k = 1 + int(np.argmax(st[1:, 4])); x, y, w, h = st[k, :4]
    out = img.copy()
    mw, mh = min(max(w, 3.2 * PX), 4.0 * PX), min(max(h, 1.7 * PX), 2.2 * PX); cx, cy = x + w / 2, y + h / 2
    m = np.zeros((H, W), np.uint8); cv2.ellipse(m, (int(cx), int(cy)), (int(mw / 2), int(mh / 2)), 0, 0, 360, 1, -1)
    out[(lab == k) & (m == 0)] = skin
    out[m > 0] = MOUTHC
    t = (m > 0) & (np.abs(np.arange(H)[:, None] - cy) < 0.5 * PX) & (np.abs(np.arange(W)[None] - cx) < mw * 0.36)
    out[t] = 250
    return out


def main():
    views = sys.argv[1:] or ['S', 'SE', 'E']
    idx = json.load(open(f'{D}/out_r9/index.json')); rep = {}; od0 = os.environ.get('OUTDIR', f'{D}/out_r10')
    for V in views:
        src = np.array(Image.open(f'{SW}v2/hair/turnE_final/{C.FILES[V]}.png').convert('RGB')).astype(np.float32)
        mask = np.array(Image.open(f'{D}/out_r9/{V}/face_mask.png').convert('L')).astype(np.float32)
        eyes = idx['r9']['views'][V]['eyes']; ysplit = idx['r9']['views'][V]['ysplit']
        base = np.array(Image.open(f'{D}/out_r9/{V}/neutral.png').convert('RGB')).astype(np.float32)
        skin = skin_of(base, mask); core = mask > 128
        od = f'{od0}/{V}'; os.makedirs(od, exist_ok=True); n_ = 0
        for p in sorted(glob.glob(f'{D}/out_r9/{V}/*.png')):
            nm = os.path.basename(p)[:-4]
            if nm.startswith('face_mask'): continue
            st = eye_state(nm); img = np.array(Image.open(p).convert('RGB')).astype(np.float32)
            if st:
                lc, rc, ms = st
                es = sorted(eyes, key=lambda e: e['c'][0]); e_src = nm.split('_')[0]; e_src = C.ALIAS.get(e_src, e_src)
                curve = not (e_src in ('squint', 'hurt', 'wince') and '_blink' not in nm)
                blinkimg = np.array(Image.open(f'{D}/out_r9/{V}/neutral_blink.png').convert('RGB')).astype(np.float32)
                for j, e in enumerate(es):
                    c = e['c']; w, h = e['box'][2] * 1.22, e['box'][3] * 1.22
                    closed = (lc if j == 0 else rc) if len(es) == 2 else lc
                    if closed: img = closed_stroke(img, e, skin, curve, 'n' if e_src == 'joyful' and '_blink' not in nm else 'U')
                    elif V == 'SE': img = open_almond(img, blinkimg, e, skin)
                    elif V == 'S':
                        img = E.bulge(img, c, 0.62 * max(w, h) + 10, 1.1)
                        ring = ellipse_mask(img.shape[:2], c, (w * 0.95, h * 1.05), 6) - ellipse_mask(img.shape[:2], c, (w * 0.62, h * 0.7), 3)
                        sk = (np.abs(img - skin).max(-1) < 30) & (ring > 0.05)
                        img[sk] = np.minimum(255, img[sk] + (255 - img[sk]) * 0.25 * ring[sk][:, None])
                if ms == 'effort' and V != 'E': img = effort_mouth(img, base, ysplit, core, skin)
            al = mask[..., None] / 255
            Image.fromarray(np.clip(src * (1 - al) + img * al, 0, 255).astype(np.uint8)).save(f'{od}/{nm}.png'); n_ += 1
        Image.fromarray(mask.astype(np.uint8)).save(f'{od}/face_mask.png')
        rep[V] = n_; print(V, n_, 'files, skin', skin.round())
    i2 = dict(idx); i2['r10'] = rep; json.dump(i2, open(f'{od0}/index.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
