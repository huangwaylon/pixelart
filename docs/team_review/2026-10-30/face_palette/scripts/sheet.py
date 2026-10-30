"""Expression sheet: eyes+brows on the face-cleared master heads (rig/tex/tex_<V>.png = master with eyes/brows/mouth/blush cleared;
nose pixels cleared here). 1x + 6x. Mirrored views (SW, W) = flipped base + mirrored layout, catchlight kept screen-left."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from facesys import *
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
TEX = REL.replace('release/', '') + 'rig/tex/'
NOSE = {'S': [(63, 54), (63, 55)], 'SE': [(71, 55), (71, 56)]}
SKIN = HEX['s']

def base(v):
    src = {'SW': 'SE', 'W': 'E'}.get(v, v)
    t = np.asarray(Image.open(TEX + f'tex_{src}.png').convert('RGBA')).copy()
    m = np.asarray(Image.open(ROOT + f'swordswoman/v2/m96/masters/EC0_{src}_96.png').convert('RGBA'))
    t[..., 3] = m[..., 3]; t[m[..., 3] == 0] = 0
    for x, y in NOSE.get(src, []): t[y, x, :3] = SKIN
    return t

def compose(v, expr):
    mir = v in ('SW', 'W'); src = {'SW': 'SE', 'W': 'E'}.get(v, v)
    a = base(v)
    if src in LAYOUT:
        for (ox, oy), side, kind in LAYOUT[src]:
            rows = eye(expr, side, kind)
            if mir:
                w = len(rows[0]); rows = eye(expr, 'right' if side == 'left' else 'left', kind); ox = 127 - ox - (w - 1)
            stamp(a, ox, oy, rows)
    elif src == 'NE':
        for x, y in NE_LASH.get(expr, []): a[y, x, :3] = COL['K']
    if mir: a = a[:, ::-1].copy() if False else a
    return a

def flipbase(a): return a[:, ::-1].copy()

def compose_view(v, expr):
    if v in ('SW', 'W'):
        src = {'SW': 'SE', 'W': 'E'}[v]
        a = flipbase(base(src))
        for (ox, oy), side, kind in LAYOUT[src]:
            rows = eye(expr, 'right' if side == 'left' else 'left', kind); w = len(rows[0])
            stamp(a, 127 - ox - (w - 1), oy, rows)
        return a
    return compose(v, expr)

if __name__ == '__main__':
    views = ['S', 'SE', 'E', 'SW', 'W', 'NE', 'N']
    X0, Y0, W, H = 42, 24, 44, 44
    bg = (96, 128, 96, 255)
    sh = Image.new('RGBA', (W * len(EXPR), H * len(views)), bg)
    for r, v in enumerate(views):
        for c, e in enumerate(EXPR):
            a = compose_view(v, e)
            sh.alpha_composite(Image.fromarray(a).crop((X0, Y0, X0 + W, Y0 + H)), (c * W, r * H))
    sh.save(OUT + 'expr_sheet_1x.png')
    big = sh.resize((sh.width * 6, sh.height * 6), Image.NEAREST)
    from PIL import ImageDraw
    d = ImageDraw.Draw(big)
    for c, e in enumerate(EXPR): d.text((c * W * 6 + 4, 2), e, fill=(255, 255, 255, 255))
    for r, v in enumerate(views): d.text((4, r * H * 6 + 14), v, fill=(255, 255, 0, 255))
    big.save(OUT + 'expr_sheet_6x.png')
    # face-only zoom for S/SE/E (the part that matters), 10x
    crops = {'S': (52, 43, 76, 57), 'SE': (57, 44, 79, 58), 'E': (66, 43, 82, 57)}
    rows = []
    for v, (x0, y0, x1, y1) in crops.items():
        rowim = Image.new('RGBA', ((x1 - x0) * len(EXPR) + len(EXPR), y1 - y0), (40, 40, 40, 255))
        for c, e in enumerate(EXPR):
            rowim.alpha_composite(Image.fromarray(compose_view(v, e)).crop((x0, y0, x1, y1)), (c * (x1 - x0 + 1), 0))
        rows.append(rowim)
    Wd = max(r.width for r in rows); z = Image.new('RGBA', (Wd, sum(r.height + 1 for r in rows)), (40, 40, 40, 255)); y = 0
    for r in rows: z.alpha_composite(r, (0, y)); y += r.height + 1
    z.resize((z.width * 10, z.height * 10), Image.NEAREST).save(OUT + 'expr_face_zoom10x.png')
    print('ok')
