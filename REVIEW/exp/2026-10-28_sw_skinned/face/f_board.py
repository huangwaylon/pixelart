"""f_board.py (F) -- review boards + GIFs for the face layer.
  python f_board.py clip <act> <view>      -> face/out/<act>/board_face_<act>_<view>.png (rows: P2 head 6x | F head 6x + anchors | F body 4x)
                                              + face/out/<act>/<act>_<view>_face_4x.gif (full frame, loop=0, >= 20 ms) + cmp gif (P2 | F)
  python f_board.py sheet <view>           -> face/out/sheet_expr_<view>.png (every expression on the rest head, 8x, + 1x)
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import face_layer as FLY  # noqa: E402
import face_lib as FL  # noqa: E402
hx = FLY.hx
BG = (110, 110, 110)


def gif(ims, durs, path):
    durs = [max(20, int(d)) for d in durs]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=1, optimize=False)


def head_box(fs, V, act):
    """common crop box around the head over all frames (from the face json anchors)"""
    d = json.load(open(f'{EXP}/face/out/{act}/{act}_{V}_face.json'))
    xs = [f['anchors']['eye.0']['xy'][0] for f in d['frames']]; ys = [f['anchors']['eye.0']['xy'][1] for f in d['frames']]
    cx = int(round(sum(xs) / len(xs))) + {'SE': 6, 'S': 8, 'E': 0}.get(V, 4); cy = int(round(sum(ys) / len(ys)))
    return cx - 22, cy - 26, cx + 22, cy + 16


def clip(act, V):
    PS = os.environ.get('PSRC', f'{EXP}/face/out/p2cur'); pd = f'{PS}/{act}/{act}_{V}_px'; fd = f'{EXP}/face/out/{act}/{act}_{V}_fpx'
    os.makedirs(fd, exist_ok=True)
    fs = sorted(f for f in os.listdir(pd) if f.endswith('.txt'))
    info = json.load(open(f'{PS}/{act}/{act}_{V}.json')); ms = {f['i']: f['ms'] for f in info['frames']}
    x0, y0, x1, y1 = head_box(fs, V, act); S = 6
    rows = [[], [], [], []]; full, cmp_, durs = [], [], []
    for f in fs:
        i = int(f[1:3]); g0 = hx.read_grid(f'{pd}/{f}')
        fi = {'action': act, 'view': V, 'i': i}
        g1 = FLY.face_layer(fi, g0, {}); hx.save(g1, f'{fd}/{f[:-4]}', V)
        C, pl, fr = FLY.frame_meta(fi)
        a = hx.render(g0[y0:y1, x0:x1], S, BG); cl = hx.render(g1[y0:y1, x0:x1], S, BG); b = hx.render(g1[y0:y1, x0:x1], S, BG).convert('RGB'); dr = ImageDraw.Draw(b)
        for k, an in fr['anchors'].items():
            ax, ay = (an['xy'][0] - x0) * S, (an['xy'][1] - y0) * S
            col = {'e': (0, 255, 255), 'b': (255, 0, 255), 'm': (255, 255, 0), 'c': (255, 120, 0), 'n': (0, 255, 0)}[k[0]]
            dr.rectangle([ax - 1, ay - 1, ax + 1, ay + 1], fill=col)
        h = pl['head']
        dr.text((3, 2), f"f{i:02d} {pl['expr']}{'/' + str(pl['blink']) if pl['blink'] else ''}", fill=(255, 255, 160))
        dr.text((3, (y1 - y0) * S - 24), f"yaw{h['dyaw']:+.0f} roll{h['roll']:+.0f} pit{h['pitch']:+.0f}", fill=(255, 255, 160))
        dr.text((3, (y1 - y0) * S - 12), ' '.join(f"{k[0]}{k[-1]}:{v}" for k, v in pl['kinds'].items()), fill=(200, 255, 200))
        rows[0].append(a); rows[1].append(cl); rows[2].append(b)
        fb = hx.render(g1, 4, BG); full.append(fb); rows[3].append(fb.crop((16 * 4, 16 * 4, 112 * 4, 128 * 4)).resize((96 * 2, 112 * 2), Image.NEAREST))
        c = Image.new('RGB', (128 * 8, 128 * 4), BG); c.paste(hx.render(g0, 4, BG), (0, 0)); c.paste(fb, (128 * 4, 0)); cmp_.append(c)
        durs.append(ms.get(i, 100))
    W = max(sum(im.width for im in r) for r in rows); H = sum(max(im.height for im in r) for r in rows) + 3 * 16
    B = Image.new('RGB', (W, H), (40, 40, 44)); d = ImageDraw.Draw(B); y = 0
    for lab, r in zip(['P2 (baked master face, smears)', 'F face layer', 'F + projected 3D anchors (eye cyan: eye cyan, brow magenta, mouth yellow, cheek orange, nose green)', 'F 1x->2x body'], rows):
        d.text((4, y + 2), f'{act} {V}: {lab}', fill=(230, 230, 120)); y += 16; x = 0
        for im in r: B.paste(im, (x, y)); x += im.width
        y += max(im.height for im in r)
    B.save(f'{EXP}/face/out/{act}/board_face_{act}_{V}.png')
    gif(full, durs, f'{EXP}/face/out/{act}/{act}_{V}_face_4x.gif')
    gif(cmp_, durs, f'{EXP}/face/out/{act}/cmp_face_{act}_{V}_4x.gif')
    # 1x strip
    st = Image.new('RGB', (96 * len(fs), 112), BG)
    for k, f in enumerate(sorted(os.listdir(fd))):
        pass
    print('board', act, V)


def sheet(V):
    """every expression on the rest pose (walk f-less: the rest render of the faceless head)"""
    rest = f'{EXP}/face/out/rest/rest_{V}_f00_tex.png'
    d = json.load(open(f'{EXP}/face/out/rest/rest_{V}_face.json'))
    T, gn = FLY.tex_cells(FLY.load_ftex(rest, d['align']['dx'], d['align']['dy']))
    m = hx.read_grid(f'{FL.M96}masters/EC0_{V}_96.txt')
    parts = json.load(open(f'{HERE}/parts.json'))[V]
    off = d.get('tex_off', [0, 0]); G = (int(off[0]), int(off[1])); R = {k: (0, 0) for k in parts}
    m = np.roll(np.roll(m, G[1], 0), G[0], 1); kinds = {k: a['kind'] for k, a in parts.items() if k.startswith('eye.')}
    a = FL.ANC[V]; bx0, by0, bx1, by1 = a['stamp']; bx0 += G[0]; bx1 += G[0]; by0 += G[1]; by1 += G[1]
    names = list(FL.EXPR); S = 6; tiles = []
    base = np.where(T, gn, m)
    for e in names:
        pl = {'G': G, 'R': R, 'kinds': kinds, 'expr': e, 'blink': None}
        g = FLY.draw(base, gn, T, V, parts, pl)
        t = hx.render(g[by0 + 10:by1 + 1, bx0:bx1], S, BG).convert('RGB'); ImageDraw.Draw(t).text((3, 2), e, fill=(255, 255, 160))
        t1 = hx.render(g[by0:by1 + 1, bx0:bx1], 1, BG); t.paste(t1, (t.width - t1.width - 2, t.height - t1.height - 2)); tiles.append(t)
    # far-eye foreshortening variants (SE/S)
    extra = []
    if V == 'SE':
        for kk in ('far3', 'hidden'):
            pl = {'G': G, 'R': R, 'kinds': {**kinds, 'eye.1': kk}, 'expr': 'neutral', 'blink': None}; extra.append((f'turn away: {kk}', pl))
    if V == 'S':
        extra.append(('turn: far', {'G': G, 'R': {**R, 'eye.1': (-1, 0), 'brow.1': (-1, 0), 'cheek.1': (-1, 0)}, 'kinds': {**kinds, 'eye.1': 'far'}, 'expr': 'neutral', 'blink': None}))
    for lab, pl in extra:
        g = FLY.draw(base, gn, T, V, parts, pl)
        t = hx.render(g[by0 + 10:by1 + 1, bx0:bx1], S, BG).convert('RGB'); ImageDraw.Draw(t).text((3, 2), lab, fill=(160, 255, 160)); tiles.append(t)
    mt = hx.render(m[by0 + 10:by1 + 1, bx0:bx1], S, BG).convert('RGB'); ImageDraw.Draw(mt).text((3, 2), 'm96 master', fill=(160, 220, 255))
    tiles = [mt] + tiles
    cols = 7; w, h = tiles[0].size; rows_ = (len(tiles) + cols - 1) // cols
    B = Image.new('RGB', (cols * (w + 4), rows_ * (h + 4)), (40, 40, 44))
    for k, t in enumerate(tiles): B.paste(t, ((k % cols) * (w + 4), (k // cols) * (h + 4)))
    B.save(f'{EXP}/face/out/sheet_expr_{V}.png'); print('sheet', V)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'clip': clip(a[1], a[2])
    elif a[0] == 'sheet': sheet(a[1])
