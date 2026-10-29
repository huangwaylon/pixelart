"""compose.py (F, round 7): illustration expression variants for the illustration-textured 3D head.
Gemini edits (raw/<V>_<expr>.png, gemini-3-pro-image with the turnE_final head as reference) are REGISTERED to the base head (ECC affine on the
hair/outline, face region excluded), then only the face region (data-driven from the diffs, feathered) is blended into the base illustration,
so everything outside the face stays pixel-identical.  Eyes+brows and mouth are separate regions, so one Gemini edit set gives every
face x blink x mouth combination M uses (R's lookup naming <face>[_half|_blink][_open]).
  python compose.py            -> out/<V>/<name>.png (full 752x1424 illustration), out/<V>/face_mask.png, out/index.json
  python compose.py check      -> fails loudly if any face/blink/mouth combination used in motion/*.json, motion/view/*.json, motion/variants/*.json
                                  has no exact file for every view (also checks face/tex3d, the round-5 set R's renderer still reads)
"""
import os, sys, json, glob
import numpy as np, cv2
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); FACE = os.path.dirname(D); EXP = os.path.dirname(FACE)
SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
BOX = json.load(open(f'{D}/src/boxes.json')) if os.path.exists(f'{D}/src/boxes.json') else None
FILES = {'S': 'iso_S', 'SE': 'iso_SE_fixed', 'E': 'iso_E'}
VIEWS = ['S', 'SE', 'E']
# expression -> (eyes source, closed-mouth source, open-mouth source, eyes already closed?)
EXPR = {
    'neutral':    ('base', 'base', 'surprised', False),
    'smile':      ('smile', 'smile', 'joyful', False),
    'joyful':     ('joyful', 'smile', 'joyful', True),
    'determined': ('determined', 'determined', 'effort', False),
    'focused':    ('determined', 'determined', 'effort', False),
    'effort':     ('effort', 'determined', 'effort', False),
    'surprised':  ('surprised', 'base', 'surprised', False),
    'squint':     ('squint', 'squint', 'hurt', True),
    'hurt':       ('hurt', 'squint', 'hurt', True),
    'wince':      (('hurt', 'half'), 'squint', 'hurt', False),   # one eye squeezed shut, the other half-closed
    'blink':      ('blink', 'base', 'surprised', True),
}
ALIAS = {'pained': 'hurt', 'pain': 'hurt', 'joy': 'joyful', 'cheerful': 'smile', 'dash': 'focused', 'land': 'squint', 'half_blink': 'neutral'}


def name(e, b='', m=''):
    return '_'.join(x for x in (e, b, m) if x)


def load_base(V):
    src = Image.open(f'{SW}v2/hair/turnE_final/{FILES[V]}.png').convert('RGB')
    x0, y0, x1, y1 = BOX[V]['box']; head = np.array(src.crop((x0, y0, x1, y1)).resize((900, 900), Image.LANCZOS)).astype(np.float32)
    return src, (x0, y0, x1, y1), head


def register(base, var, mask=None):
    """ECC affine of var onto base (grayscale), optional mask = region to use (outside the face)"""
    g0 = cv2.cvtColor(base.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    g1 = cv2.cvtColor(var.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    g0 = cv2.GaussianBlur(g0, (0, 0), 2); g1 = cv2.GaussianBlur(g1, (0, 0), 2)
    W = np.eye(2, 3, dtype=np.float32)
    try:
        _, W = cv2.findTransformECC(g0, g1, W, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6),
                                    None if mask is None else mask.astype(np.uint8), 5)
    except cv2.error:
        pass
    out = cv2.warpAffine(var, W, (900, 900), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    return out, W


def build():
    index = {}
    for V in VIEWS:
        src, box, base = load_base(V); od = f'{D}/out/{V}'; os.makedirs(od, exist_ok=True)
        raws = {os.path.basename(p)[:-4].split('_', 1)[1]: p for p in glob.glob(f'{D}/raw/{V}_*.png') if not p.endswith('_1.png')}
        var = {}
        for e, p in raws.items():
            v = np.array(Image.open(p).convert('RGB').resize((900, 900), Image.LANCZOS)).astype(np.float32)
            var[e], _ = register(base, v)
        # face region: where the edits differ from the base, in the central part of the head; refine the registration without it
        dif = {e: (np.abs(v - base).max(-1) > 40) for e, v in var.items()}
        U = np.zeros((900, 900), bool)
        for e, m in dif.items(): U |= m
        U = cv2.morphologyEx(U.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0
        n, lab, st, _ = cv2.connectedComponentsWithStats(U.astype(np.uint8))
        keep = np.zeros_like(U)
        for k in range(1, n):
            if st[k, cv2.CC_STAT_AREA] > 400: keep |= lab == k
        ys, xs = np.nonzero(keep)
        face = np.zeros((900, 900), np.uint8)
        if len(xs):
            cx, cy = np.median(xs), np.median(ys)
            # the face blob = components near the central feature cluster (the hair also moves a little in some edits; keep it out)
            for k in range(1, n):
                if st[k, cv2.CC_STAT_AREA] <= 400: continue
                bx, by = st[k, 0] + st[k, 2] / 2, st[k, 1] + st[k, 3] / 2
                if abs(bx - cx) < 260 and abs(by - cy) < 220: face |= (lab == k).astype(np.uint8)
        face = cv2.morphologyEx(face, cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))
        face = cv2.dilate(face, np.ones((21, 21), np.uint8))
        out_mask = (face == 0).astype(np.uint8)
        for e in var:   # second registration pass on the non-face area only
            v = np.array(Image.open(raws[e]).convert('RGB').resize((900, 900), Image.LANCZOS)).astype(np.float32)
            var[e], W = register(base, v, out_mask)
        # eye / mouth split from the blink (eyes only) and smile/joyful (mouth) diffs
        # eye / mouth split from the row profiles of the blink diff (eyes only) and the joyful/smile diff (mouth peak below the eyes)
        def prof(m, ax): return np.convolve((m & (face > 0)).sum(ax).astype(float), np.ones(31) / 31, 'same')
        bd = np.abs(var.get('blink', base) - base).max(-1) > 40
        md = np.abs(var.get('joyful', var.get('smile', base)) - base).max(-1) > 40
        ye = int(np.argmax(prof(bd, 1))); pm = prof(md, 1); pm[:ye + 90] = 0; ym = int(np.argmax(pm)) if pm.max() > 0 else ye + 140
        pe = prof(bd, 1); rows_ = np.nonzero(pe > pe.max() * 0.12)[0]; rows_ = rows_[rows_ < ym - 20]
        eye_bot = int(rows_.max()) if len(rows_) else ye + 40
        ysplit = int(max(eye_bot + 12, 0.35 * ye + 0.65 * ym)); ysplit = min(ysplit, ym - 25)
        print(V, 'eye peak', ye, 'eye bottom', eye_bot, 'mouth peak', ym)
        xsplit = None
        if V != 'E':
            pc = prof(bd & (np.arange(900)[:, None] < ysplit), 0); xs_ = np.nonzero(pc > pc.max() * 0.15)[0]
            if len(xs_): c0, c1 = xs_.min(), xs_.max(); xsplit = int(c0 + 30 + np.argmin(pc[c0 + 30:c1 - 30])) if c1 - c0 > 80 else None
        fe = cv2.GaussianBlur(face.astype(np.float32), (0, 0), 6)
        yy = np.arange(900)[:, None] * np.ones((1, 900)); xx = np.ones((900, 1)) * np.arange(900)[None]
        def soft(cond): return cv2.GaussianBlur(cond.astype(np.float32), (0, 0), 5)
        EYES = fe * soft(yy < ysplit); MOUTH = fe * soft(yy >= ysplit)
        EL = EYES * soft(xx < xsplit) if xsplit else EYES; ER = EYES * soft(xx >= xsplit) if xsplit else EYES * 0
        def comp(eyes, mouth):
            img = base.copy()
            if isinstance(eyes, tuple):   # (left eye src, right eye src) - screen left/right
                for src_, M_ in ((eyes[0], EL), (eyes[1], ER if xsplit else EL * 0)):
                    s_ = base if src_ == 'base' else var.get(src_, base); img = img * (1 - M_[..., None]) + s_ * M_[..., None]
            else:
                s_ = base if eyes == 'base' else var.get(eyes, base); img = img * (1 - EYES[..., None]) + s_ * EYES[..., None]
            s_ = base if mouth == 'base' else var.get(mouth, base); img = img * (1 - MOUTH[..., None]) + s_ * MOUTH[..., None]
            return img
        def paste(img900):
            x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
            small = np.array(Image.fromarray(np.clip(img900, 0, 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)).astype(np.float32)
            ms = np.array(Image.fromarray((fe * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)).astype(np.float32)[..., None] / 255
            full = np.array(src).astype(np.float32); reg = full[y0:y1, x0:x1]
            full[y0:y1, x0:x1] = reg * (1 - ms) + small * ms
            return Image.fromarray(np.clip(full, 0, 255).astype(np.uint8))
        names = {}
        for e, (eyes, mc, mo, closed) in EXPR.items():
            for b in ('', 'half', 'blink'):
                for m in ('', 'open'):
                    ey = eyes
                    if b and not closed:
                        if isinstance(ey, tuple): ey = (ey[0], 'blink' if b == 'blink' else 'half')
                        else: ey = 'blink' if b == 'blink' else 'half'
                    nm = name(e, b, m); img = comp(ey, mo if m == 'open' else mc); paste(img).save(f'{od}/{nm}.png'); names[nm] = [str(ey), mo if m else mc]
            for a, t in ALIAS.items():
                if t == e:
                    for b in ('', 'half', 'blink'):
                        for m in ('', 'open'):
                            os.system(f'cp "{od}/{name(e, b, m)}.png" "{od}/{name(a, b, m)}.png"')
        Image.fromarray((fe * 255).astype(np.uint8)).save(f'{od}/face_mask_head900.png')
        x0, y0, x1, y1 = box; fm = np.zeros((src.size[1], src.size[0]), np.uint8)
        fm[y0:y1, x0:x1] = np.array(Image.fromarray((fe * 255).astype(np.uint8)).resize((x1 - x0, y1 - y0), Image.BILINEAR))
        Image.fromarray(fm).save(f'{od}/face_mask.png')
        index[V] = {'box': list(box), 'ysplit900': int(ysplit), 'xsplit900': xsplit, 'have': sorted(var), 'names': names}
        print(V, 'variants', sorted(var), 'split', ysplit, xsplit, len(names), 'files')
    json.dump(index, open(f'{D}/out/index.json', 'w'), indent=1)


def combos():
    c = set()
    for p in glob.glob(f'{EXP}/motion/*.json') + glob.glob(f'{EXP}/motion/view/*.json') + glob.glob(f'{EXP}/motion/variants/*.json'):
        try: d = json.load(open(p))
        except Exception: continue
        for f in d.get('frames', []):
            bl = f.get('blink', 0) or 0
            try: bl = float(bl)
            except Exception: bl = 1.0 if str(bl) in ('closed', 'blink') else 0.5 if str(bl) == 'half' else 0.0
            b = 'blink' if bl >= 0.75 else 'half' if bl >= 0.25 else ''; m = 'open' if str(f.get('mouth', '')) == 'open' else ''
            c.add((str(f.get('face', 'neutral')), b, m, os.path.basename(p)))
    return c


def check():
    bad = []; seen = {}
    for e, b, m, src in combos(): seen.setdefault(name(e, b, m), set()).add(src)
    for nm, srcs in sorted(seen.items()):
        for V in VIEWS:
            if not os.path.exists(f'{D}/out/{V}/{nm}.png'): bad.append(f'illus {V}: {nm}  (used in {sorted(srcs)[:3]})')
        if not os.path.exists(f'{FACE}/tex3d/{nm}.png'): bad.append(f'tex3d: {nm}  (used in {sorted(srcs)[:3]})')
    print(f'face combos used by motion: {len(seen)} -> {sorted(seen)}')
    if bad:
        print('MISSING FACE TEXTURES:\n  ' + '\n  '.join(bad)); sys.exit(1)
    print('FACE_COVERAGE_OK')


if __name__ == '__main__':
    check() if sys.argv[1:] and sys.argv[1] == 'check' else build()
