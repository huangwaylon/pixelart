"""Prototype (a) eyes/brows as a flat texture on the 3D head vs (b) pixel templates stamped at the 3D face anchors,
on cached passes + final frames of build 20261030_66119a7. Face clearing for both: hi-res pixels whose REST position (rpos pass)
falls in the front face-feature chart region (rig/tex/face_mask_S.png dilated 1 px) -> block coverage >= .5 -> skin."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from facesys import *
from scipy import ndimage as nd
import surfanchor as SA
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
FMASK = np.asarray(Image.open(REL.replace('release/', '') + 'rig/tex/face_mask_S.png').convert('L')) > 128
FMASK_D = nd.binary_dilation(FMASK, iterations=1)
EXMAP = {'neutral': 'open', 'smile': 'open', 'joyful': 'happy', 'joy': 'happy', 'determined': 'determined', 'focused': 'determined',
         'effort': 'determined', 'surprised': 'surprised', 'pained': 'hurt', 'wince': 'hurt', 'squint': 'half'}
def expr_of(f):
    e = EXMAP.get(f.get('face', 'neutral'), 'open'); b = f.get('blink', 0)
    if e == 'hurt': return e
    if b >= 1: return 'closed'
    if b >= .5: return 'half'
    return e
SK, SH = np.array(HEX['s']), np.array(HEX['S'])
FEAT = {k: np.array(v) for k, v in COL.items()}

def chart_tex(expr):
    """S-layout feature texture, 1 texel = 1 S-master px; value = char or ''"""
    t = np.full((128, 128), '', object)
    for (ox, oy), side, kind in LAYOUT['S']:
        for r, line in enumerate(eye(expr, side, kind)):
            for c, ch in enumerate(line):
                if ch not in ' .': t[oy + r, ox + c] = ch
    return t

def region(act, v, i):
    rp, ok = rpos(act, v, i); u, w = to_chart(rp)
    mir = v in ('SW', 'W', 'NW')
    ui, wi = np.floor(u).astype(int), np.floor(w).astype(int)
    inb = ok & (ui >= 0) & (ui < 128) & (wi >= 0) & (wi < 128) & (rp[..., 1] > 0.0)
    reg = np.zeros(ok.shape, bool); reg[inb] = FMASK_D[wi[inb], ui[inb]]
    if v in ('E', 'W'):  # profile: the face side wraps past the S chart -> side band (front half y >= .045 m, chart rows 45-58)
        reg |= ok & (rp[..., 1] >= 0.045) & (w >= 45) & (w < 59) & (np.abs(rp[..., 0]) >= 0.09) & (np.abs(rp[..., 0]) <= 0.21)
    return reg, ui, wi, inb

def clear(a, cov):
    out = a.copy(); al = nd.binary_fill_holes(a[..., 3] > 0)  # 66119a7 has transparent holes inside the eyes -> filled
    edge = al & ~nd.binary_erosion(al, structure=np.ones((3, 3)))
    sel = (cov >= .5) & al & ~edge
    holes = al & (a[..., 3] == 0); out[holes, :3] = SK; out[holes, 3] = 255  # enclosed transparent holes (66119a7 eye bug) -> skin
    eo = (cov >= .5) & edge & np.isin([[INV.get(tuple(p[:3]), '?') for p in row] for row in a], ['W', 'g', 'L', 'k', 'm'])
    out[eo, :3] = HEX['K']  # silhouette rule: an edge pixel of the face is outline K, never eye white/iris/blush
    out[sel, :3] = SK; out[sel, 3] = 255  # locked rule: face interior = flat s (no S speckle, no blush, no mouth, no nose)
    return out, sel

BROW_OVER_HAIR = os.environ.get('BROWHAIR', '1') == '1'
def put(img, base, face, X0, Y0, rows, keep=0.6):
    """stamp one eye template; skin/face pixels only (hair, hands, outline occlude it); an eye whose ink is < keep visible is dropped whole
    (no orphan catchlight / lash crumbs on the hair)."""
    pts = [(Y0 + r, X0 + c, ch) for r, line in enumerate(rows) for c, ch in enumerate(line) if ch not in ' .']
    ok = [(y, x, ch) for y, x, ch in pts if 0 <= y < 128 and 0 <= x < 128 and (face[y, x] or INV.get(tuple(base[y, x, :3])) in ('s', 'S'))]
    eyeink = [p for p in pts if p[2] != 'h']; eyeok = [p for p in ok if p[2] != 'h']
    if eyeink and len(eyeok) < keep * len(eyeink): ok = [p for p in ok if p[2] == 'h']
    for y, x, ch in ok: img[y, x, :3] = FEAT[ch]
    if BROW_OVER_HAIR:  # brows show through the bangs: on hair (H/L/g) the brow is drawn K (one step darker than what it sits on)
        for y, x, ch in pts:
            if ch == 'h' and 0 <= y < 128 and 0 <= x < 128 and INV.get(tuple(base[y, x, :3])) in ('H', 'L', 'g'): img[y, x, :3] = FEAT['K']

def proto(act, v, i):
    d, clip = info(act, v); fr = d['frames'][i]; mo = json.load(open(B + f'{act}/{v}/motion.json'))['frames'][i]
    ex = expr_of(mo); a = np.asarray(final(act, v, i)).copy()
    reg, ui, wi, inb = region(act, v, i)
    cov = blocks(reg[..., None].astype(float))[..., 0].mean(-1)
    base, face = clear(a, cov)
    # (b) stamp at anchors
    b = base.copy(); src = v; mir = False
    if v in ('SW', 'W'): src = {'SW': 'SE', 'W': 'E'}[v]; mir = True
    keys = ['eye.R', 'eye.L']; odx, ody = d['out_dxdy']
    for k, ((ox, oy), side, kind) in zip(keys, LAYOUT.get(src, [])):
        A, R0 = fr['face'][k], d['rest_face'][k]
        if not (A['visible'] or (A['occ_m'] is None and A['facing'] > -0.1)): continue
        dx = int(round(A['px'][0] - R0['px'][0])); dy = int(round(A['px'][1] - R0['px'][1]))
        put(b, base, face, ox + odx + dx, oy + ody + dy, eye(ex, side, kind))
    # (b') stamp at SURFACE anchors (rpos-tracked rest point of each drawn eye)
    b2 = base.copy()
    if src in SA.KEYS:
        for c, ((ox, oy), side, kind) in zip(SA.calib(src), LAYOUT[src]):
            loc = SA.locate(act, v, i, c['P'])
            if loc is None: continue
            X0 = int(np.floor(loc[0] + c['off'][0] + .5)); Y0 = int(np.floor(loc[1] + c['off'][1] + .5))
            put(b2, base, face, X0, Y0, eye(ex, side, kind))
    # (a) flat texture on the 3D head, block plurality vote
    t = chart_tex(ex); hi = np.full(reg.shape, '', object)
    hi[inb] = t[wi[inb], ui[inb]]
    hb = blocks(hi[..., None])[..., 0]
    at = base.copy()
    for y, x in zip(*np.where(cov > 0)):
        vals, cnt = np.unique(hb[y, x], return_counts=True)
        j = cnt.argmax(); ch = vals[j]
        if ch != '' and face[y, x]: at[y, x, :3] = FEAT[ch]
    return a, base, at, b, ex, fr['face']['_head']['centre_px'], b2

if __name__ == '__main__':
    F = [('idle', 'SE', 0), ('idle', 'SE', 1), ('walk', 'SE', 2), ('run', 'E', 3), ('jump', 'S', 4), ('jump', 'S', 8)]
    from PIL import ImageDraw
    rows4, rows1 = [], []
    for act, v, i in F:
        a, base, at, b, ex, c, b2 = proto(act, v, i)
        x0, y0 = int(c[0]) - 16, int(c[1]) - 14
        crops = [Image.fromarray(im).crop((x0, y0, x0 + 32, y0 + 30)) for im in (a, base, at, b, b2)]
        r4 = Image.new('RGBA', (5 * 138, 30 * 4), (96, 128, 96, 255))
        for k, cr in enumerate(crops): r4.alpha_composite(cr.resize((128, 120), Image.NEAREST), (k * 138, 0))
        ImageDraw.Draw(r4).text((2, 2), f'{act} {v} f{i:02d} {ex}', fill=(255, 255, 0, 255)); rows4.append(r4)
        r1 = Image.new('RGBA', (5 * 72, 100), (96, 128, 96, 255))
        for k, im in enumerate((a, base, at, b, b2)): r1.alpha_composite(Image.fromarray(im).crop((28, 20, 100, 120)), (k * 72, 0))
        rows1.append(r1)
        for nm, im in (('a_tex', at), ('b_stamp', b), ('b2_surfstamp', b2)): Image.fromarray(im).save(OUT + f'frames/proto_{nm}_{act}_{v}_f{i:02d}.png')
    W = rows4[0].width; s = Image.new('RGBA', (W, len(rows4) * 124 + 16), (30, 30, 30, 255))
    d = ImageDraw.Draw(s)
    for k, t in enumerate(['current 66119a7', 'cleared (rpos)', '(a) texture on 3D', '(b) stamp@face.*', "(b') stamp@surface"]): d.text((k * 138 + 4, 2), t, fill=(255, 255, 255, 255))
    for k, r in enumerate(rows4): s.alpha_composite(r, (0, 16 + k * 124))
    s.save(OUT + 'proto_compare_4x.png')
    s1 = Image.new('RGBA', (rows1[0].width, 100 * len(rows1)), (96, 128, 96, 255))
    for k, r in enumerate(rows1): s1.alpha_composite(r, (0, k * 100))
    s1.save(OUT + 'proto_compare_1x.png'); s1.resize((s1.width * 2, s1.height * 2), Image.NEAREST).save(OUT + 'proto_compare_2x.png')
    print('ok')
