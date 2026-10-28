"""f_critstrip.py (F): critique strips: m96 master head | round-2 P2 head (baked projected face) per frame | F face layer per frame (6x head
crops, same box) + a 2x full-body F row.  -> face/crit/strip_<act>_<V>.png"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE); sys.path.insert(0, HERE)
import face_layer as FLY
hx = FLY.hx; BG = (110, 110, 110)


def strip(act, V, S=6):
    fd = f'{EXP}/face/out/{act}/{act}_{V}_fpx'; od = f'{EXP}/render/out/p2/{act}/{act}_{V}_px'
    fs = sorted(f for f in os.listdir(fd) if f.endswith('.txt'))
    d = json.load(open(f'{EXP}/face/out/{act}/{act}_{V}_face.json'))
    G = [hx.read_grid(f'{fd}/{f}') for f in fs]
    C = FLY.plan_clip(f'{EXP}/face/out/{act}/{act}_{V}_face.json', act, act != 'jump')
    rows = []
    for gs, lab in ((G, 'F'),):
        pass
    def box(g):
        ys, xs = np.nonzero(g[:70] != '.'); return xs.min(), ys.min()
    tiles = [[], [], []]
    for k, f in enumerate(fs):
        g = G[k]; fr = d['frames'][k]; ex = fr['anchors']['eye.0']['xy']
        x0, y0 = int(ex[0]) - 18, int(ex[1]) - 24; x1, y1 = x0 + 36, y0 + 34
        t = hx.render(g[max(0, y0):y1, max(0, x0):x1], S, BG).convert('RGB'); pl = C['plan'][k]
        ImageDraw.Draw(t).text((3, 2), f"f{fr['i']:02d} {pl['expr']}" + (f" b{pl['blink']}" if pl['blink'] else '') + (f" {pl['mouth']}" if pl.get('mouth') else ''), fill=(255, 255, 150))
        tiles[1].append(t)
        if os.path.exists(f'{od}/{f}'):
            go = hx.read_grid(f'{od}/{f}'); ys, xs = np.nonzero(go[:66] != '.')
            # same-size crop around the old head (old motion differs a little)
            cx, cy = int(np.median(xs)), int(ys.min())
            tiles[0].append(hx.render(go[max(0, cy - 2):max(0, cy - 2) + 34, cx - 16:cx + 20], S, BG).convert('RGB'))
        tiles[2].append(hx.render(g[16:120, 16:112], 2, BG).convert('RGB'))
    m = hx.read_grid(f'{FLY.FL.M96}masters/EC0_{V}_96.txt'); a = FLY.FL.ANC[V]
    mt = hx.render(m[a['stamp'][1]:a['stamp'][1] + 34, a['stamp'][0]:a['stamp'][0] + 36], S, BG).convert('RGB')
    labs = ['round 2 (P2, projected master face baked in the head texture)', 'round 3 F face layer (parts on 3D head anchors)', 'F 2x']
    W = mt.width + max(sum(t.width for t in r) for r in tiles if r) + 8; H = sum(max([t.height for t in r] or [0]) + 14 for r in tiles)
    B = Image.new('RGB', (W, H), (36, 36, 40)); dr = ImageDraw.Draw(B); y = 0
    B.paste(mt, (0, 14)); dr.text((2, 2), f'm96 master {V}', fill=(150, 220, 255))
    for lab, r in zip(labs, tiles):
        if not r: continue
        dr.text((mt.width + 8, y + 1), f'{act} {V}: {lab}', fill=(230, 230, 120)); y += 14; x = mt.width + 8
        for t in r: B.paste(t, (x, y)); x += t.width
        y += max(t.height for t in r)
    p = f'{EXP}/face/crit/strip_{act}_{V}.png'; B.save(p); print(p)


if __name__ == '__main__':
    for av in sys.argv[1:]:
        a, v = av.split(':'); strip(a, v)
