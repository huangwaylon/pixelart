"""f_focus_sheet.py (F, round 4): neutral | determined | focused | effort on the rest head in SE/S/E/SW (8x + 1x) -> face/crit/focused_r4.png"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE); sys.path.insert(0, HERE)
import face_layer as F, face_lib as FL
from PIL import Image, ImageDraw
hx = F.hx; rows = []
for V in ['SE', 'S', 'E', 'SW']:
    d = json.load(open(f'{HERE}/out/rest/rest_{V}_face.json')); T, gn = F.tex_cells(F.load_ftex(f'{HERE}/out/rest/rest_{V}_f00_tex.png', d['align']['dx'], d['align']['dy']))
    parts = json.load(open(f'{HERE}/parts.json'))[V]; G = tuple(int(v) for v in d['tex_off']); R = {k: (0, 0) for k in parts}
    kinds = {k: a['kind'] for k, a in parts.items() if k.startswith('eye.')}
    src = FL.MIRROR.get(V); a = FL.ANC[src or V]; x0, y0, x1, y1 = a['stamp']
    if src: x0, x1 = 128 - x1, 128 - x0
    x0 += G[0]; x1 += G[0]; y0 += G[1] + 12; y1 += G[1] + 1; ts = []
    for e in ['neutral', 'determined', 'focused', 'effort']:
        g = F.draw(gn, gn, T, V, parts, {'G': G, 'R': R, 'kinds': kinds, 'expr': e, 'blink': None})
        t = hx.render(g[y0:y1, x0:x1], 8, (110, 110, 110)).convert('RGB'); ImageDraw.Draw(t).text((3, 2), f'{V} {e}', fill=(255, 255, 150))
        t1 = hx.render(g[y0 - 12:y1, x0:x1], 1, (110, 110, 110)); t.paste(t1, (t.width - t1.width - 2, t.height - t1.height - 2)); ts.append(t)
    rows.append(ts)
B = Image.new('RGB', (max(sum(t.width + 4 for t in r) for r in rows), sum(r[0].height + 4 for r in rows)), (36, 36, 40)); y = 0
for r in rows:
    x = 0
    for t in r: B.paste(t, (x, y)); x += t.width + 4
    y += r[0].height + 4
B.save(f'{HERE}/crit/focused_r4.png'); print('focused sheet', B.size)
