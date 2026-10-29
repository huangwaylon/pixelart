"""enhance.py (F, round 9): make the expression illustrations pixel-readable AT THE TEXTURE LEVEL (no chain special case).
For each view (S/SE/E) and every variant in out_r7/<V>/ (the round-7 aligned set), inside the face region only:
  1. eyes ~EYE_S (1.22) larger: a smooth bulge warp about each eye centre (centres/boxes from the base illustration, so every variant matches)
  2. lash line thicker + darker: dark strokes in the eye box darkened and grown by a min filter (LASH px)
  3. iris darker (mid-dark eye pixels x IRIS)
  4. catchlight bigger + pure white (near-white low-saturation eye pixels, dilated CATCH px)
  5. mouth darker/thicker, blush more saturated
The face mask grows by the eye bulge discs; outside it every file stays pixel-identical to turnE_final.  -> out/<V>/*.png + face_mask.png
  python enhance.py [S SE E]"""
import os, sys, json, glob, shutil
import numpy as np, cv2
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
FILES = {'S': 'iso_S', 'SE': 'iso_SE_fixed', 'E': 'iso_E'}
EYE_S = float(os.environ.get('EYE_S', '1.22')); LASH = int(os.environ.get('LASH', '5')); IRIS = float(os.environ.get('IRIS', '0.72'))
CATCH = int(os.environ.get('CATCH', '3')); MOUTH = float(os.environ.get('MOUTH', '0.7'))


def lum(a): return a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114


def eyes_of(base, mask, ysplit):
    """eye blobs: dark components in the face mask above the eye/mouth split (biggest 2; E: 1)"""
    L = lum(base); m = (mask > 128) & (L < 95); m[ysplit:] = False
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    comps = sorted([(st[k, cv2.CC_STAT_AREA], k) for k in range(1, n)], reverse=True)
    out = []
    for area, k in comps[:4]:
        x, y, w, h = st[k, :4]
        if area < 120 or w > 140 or h > 110: continue   # skip brows merged with hair, tiny specks
        if w < 0.9 * h * 0.6: continue
        out.append({'c': (float(x + w / 2), float(y + h * 0.55)), 'box': (int(x), int(y), int(w), int(h)), 'area': int(area)})
    return out


def eyes_from_blink(base, blink, mask, ysplit):
    """eye blobs = where the open eye differs from the blink (eye-only change; never merges with hair or brows)"""
    d = (np.abs(base - blink).max(-1) > 45) & (mask > 128); d[ysplit:] = False
    d = cv2.morphologyEx(d.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    d = cv2.morphologyEx(d, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(d)
    out = []
    for k in sorted(range(1, n), key=lambda k: -st[k, 4])[:2]:
        x, y, w, h, area = st[k]
        if area < 150: continue
        out.append({'c': (float(x + w / 2), float(y + h * 0.55)), 'box': (int(x), int(y), int(w), int(h)), 'area': int(area)})
    return out


def bulge(img, c, R, s):
    H, W = img.shape[:2]; yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - c[0], yy - c[1]; r = np.sqrt(dx * dx + dy * dy) + 1e-6
    f = 1 + (s - 1) * np.clip(1 - (r / R) ** 2, 0, 1) ** 2
    return cv2.remap(img, (c[0] + dx / f).astype(np.float32), (c[1] + dy / f).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def process(img, eyes, ysplit, mask_core):
    a = img.astype(np.float32)
    for e in eyes:
        x, y, w, h = e['box']; R = 0.62 * max(w, h) + 14
        a = bulge(a, e['c'], R, EYE_S)
    out = a.copy(); H, W = out.shape[:2]
    for e in eyes:
        x, y, w, h = e['box']; cx, cy = e['c']; w2, h2 = w * EYE_S, h * EYE_S
        # soft elliptical eye mask (not a box: brows / hair / cheek stay untouched)
        em = np.zeros((H, W), np.float32)
        cv2.ellipse(em, (int(cx), int(cy)), (int(w2 * 0.58), int(h2 * 0.62)), 0, 0, 360, 1.0, -1)
        em = cv2.GaussianBlur(em, (0, 0), 3); emb = em > 0.5
        sub = out.copy(); Ls = lum(sub); sat = sub.max(-1) - sub.min(-1)
        iris = emb & (Ls > 45) & (Ls < 165) & (sat > 18)
        hull = cv2.morphologyEx(iris.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        cnts, _ = cv2.findContours(hull, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        fill = np.zeros((H, W), np.uint8); cv2.drawContours(fill, cnts, -1, 1, -1); fill = fill > 0
        cat = fill & (sub.min(-1) > 200) & (sat < 40)          # catchlight = near-white INSIDE the iris only (not the sclera)
        sub[iris] *= IRIS                                        # darker iris
        dark = emb & (lum(sub) < 75)
        mn = cv2.erode(sub, np.ones((LASH, LASH), np.uint8))
        up = np.zeros((H, W), bool); up[: int(cy + h2 * 0.05)] = True
        grow = emb & up & (cv2.dilate(dark.astype(np.uint8), np.ones((LASH, LASH), np.uint8)) > 0) & (lum(mn) < 90) & ~fill
        sub[grow] = mn[grow]; sub[dark] *= 0.6                   # thicker, darker lash line
        if cat.any():
            catg = (cv2.dilate(cat.astype(np.uint8), np.ones((2 * CATCH + 1, 2 * CATCH + 1), np.uint8)) > 0) & fill
            sub[catg] = 255                                      # bigger, pure-white catchlight
        out = out * (1 - em[..., None]) + sub * em[..., None]
    # mouth + blush below the split (inside the face core), feathered across the split line
    L = lum(out); fm = np.zeros(L.shape, np.float32); fm[ysplit + 10:] = 1; fm = cv2.GaussianBlur(fm, (0, 0), 6) * mask_core
    lowb = fm > 0.5
    mouth = lowb & (L < 150) & ((out[..., 0] - out[..., 2]) < 90)
    mn = cv2.erode(out, np.ones((3, 3), np.uint8)); mg = lowb & (cv2.dilate(mouth.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & (lum(mn) < 140)
    o2 = out.copy(); o2[mg] = mn[mg]; o2[mouth | mg] *= MOUTH
    red = np.clip(((out[..., 0] - out[..., 1]) - 40) / 50, 0, 1) * (out[..., 0] > 190)   # smooth blush weight (no speckle)
    red = cv2.GaussianBlur(red.astype(np.float32), (0, 0), 4) * lowb
    o2[..., 1] *= 1 - 0.14 * red; o2[..., 2] *= 1 - 0.14 * red
    out = out * (1 - fm[..., None]) + o2 * fm[..., None]
    return np.clip(out, 0, 255)


def main():
    views = sys.argv[1:] or ['S', 'SE', 'E']
    idx = json.load(open(f'{D}/out_r7/index.json')); rep = {}
    for V in views:
        src = np.array(Image.open(f'{SW}v2/hair/turnE_final/{FILES[V]}.png').convert('RGB')).astype(np.float32)
        mask = np.array(Image.open(f'{D}/out_r7/{V}/face_mask.png').convert('L'))
        x0, y0, x1, y1 = idx[V]['box']; ysplit = int(y0 + idx[V]['ysplit900'] * (y1 - y0) / 900)
        base = np.array(Image.open(f'{D}/out_r7/{V}/neutral.png').convert('RGB')).astype(np.float32)
        blink = np.array(Image.open(f'{D}/out_r7/{V}/neutral_blink.png').convert('RGB')).astype(np.float32)
        eyes = eyes_from_blink(base, blink, mask, ysplit) or eyes_of(base, mask, ysplit)
        if V == 'E': eyes = eyes[:1]
        else: eyes = sorted(sorted(eyes, key=lambda e: -e['area'])[:2], key=lambda e: e['c'][0])
        newm = mask.copy().astype(np.float32)
        for e in eyes:
            x, y, w, h = e['box']; R = 0.62 * max(w, h) + 14
            cv2.circle(newm, (int(e['c'][0]), int(e['c'][1])), int(R * 1.15), 255, -1)
        newm = cv2.GaussianBlur(newm, (0, 0), 3); core = newm > 128
        od = f"{os.environ.get('OUTDIR', D + '/out')}/{V}"; os.makedirs(od, exist_ok=True)
        for p in sorted(glob.glob(f'{D}/out_r7/{V}/*.png')):
            nm = os.path.basename(p)
            if nm.startswith('face_mask'): continue
            v = np.array(Image.open(p).convert('RGB')).astype(np.float32)
            pv = process(v, eyes, ysplit, core)
            al = newm[..., None] / 255
            Image.fromarray(np.clip(src * (1 - al) + pv * al, 0, 255).astype(np.uint8)).save(f'{od}/{nm}')
        Image.fromarray(newm.astype(np.uint8)).save(f'{od}/face_mask.png')
        rep[V] = {'eyes': eyes, 'ysplit': ysplit}
        print(V, 'eyes', [(round(e['c'][0]), round(e['c'][1]), e['box'][2:]) for e in eyes])
    idx2 = json.load(open(f'{D}/out_r7/index.json')); idx2['r9'] = {'params': {'EYE_S': EYE_S, 'LASH': LASH, 'IRIS': IRIS, 'CATCH': CATCH, 'MOUTH': MOUTH}, 'views': rep}
    json.dump(idx2, open(os.environ.get('OUTDIR', D + '/out') + '/index.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
