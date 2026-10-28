"""stampsheet.py HEADS_DIR OUT.png [EYES_OUT.png]: stamp sheet (rows = views S SE E NE N, cols = expressions; head at 3x + 1x)
and eye-consistency sheet (eyes cropped at 8x: rows = views S/SE/E, cols = key expressions)"""
import sys, os, json
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z, m96 as M, numpy as np
from PIL import Image, ImageDraw
D, out = sys.argv[1], sys.argv[2]; eo = sys.argv[3] if len(sys.argv) > 3 else None
keys, rgb, _ = Z.load_pal(M.PAL); anc = json.load(open(os.path.join(D, 'anchor.json')))
EX = ['neutral', 'cheerful', 'determined', 'effort', 'shout', 'joy', 'surprised', 'pain', 'blink_half', 'blink_closed', 'embarrassed']
def load(v, e):
    p = f'{D}/{v}_{e}.txt'
    if not os.path.exists(p): p = f'{D}/{v}_neutral.txt'
    L = [l.rstrip('\n') for l in open(p) if l.strip()]; rows = [l for l in L if not l.startswith(';')]
    g = np.array([list(r) for r in rows]); return Z.render(g, keys, rgb)
cells = {(v, e): load(v, e) for v in ['S', 'SE', 'E', 'NE', 'N'] for e in EX}
cw = max(im.width for im in cells.values()) * 3 + 8; ch = max(im.height for im in cells.values()) * 3 + 8 + 40
S = Image.new('RGB', (40 + cw * len(EX), 16 + ch * 5), 'white'); d = ImageDraw.Draw(S)
for i, e in enumerate(EX): d.text((40 + i * cw + 2, 2), e[:11], fill='black')
for j, v in enumerate(['S', 'SE', 'E', 'NE', 'N']):
    d.text((4, 16 + j * ch + 20), v, fill='black')
    for i, e in enumerate(EX):
        im = cells[(v, e)]; x, y = 40 + i * cw, 16 + j * ch
        bg = Image.new('RGB', im.size, (235, 235, 235)); bg.paste(im, (0, 0), im)
        S.paste(bg.resize((im.width * 3, im.height * 3), Image.NEAREST), (x, y)); S.paste(bg, (x, y + im.height * 3 + 4))
S.save(out); t = S.copy(); t.thumbnail((800, 800)); t.save(out[:-4] + '_thumb.png'); print(out, S.size)
if eo:
    KEY = ['neutral', 'cheerful', 'determined', 'shout', 'surprised', 'blink_half', 'joy', 'embarrassed']
    tiles = []
    for v in ['S', 'SE', 'E']:
        a = anc['views'][v]; st = a['stamp']; ex0 = min(e['x0'] for e in a['eyes']) - 1; ex1 = max(e['x0'] + 6 for e in a['eyes']) + 1; ey0 = a['eyes'][0]['y0']; ey1 = ey0 + 7
        row = []
        for e in KEY:
            im = load(v, e).crop((ex0 - st[0], ey0 - st[1], ex1 - st[0], ey1 - st[1])); bg = Image.new('RGB', im.size, (235, 235, 235)); bg.paste(im, (0, 0), im)
            row.append(bg.resize((im.width * 8, im.height * 8), Image.NEAREST))
        tiles.append((v, row))
    cw = max(r.width for _, row in tiles for r in row) + 10; ch = max(r.height for _, row in tiles for r in row) + 10
    E = Image.new('RGB', (40 + cw * len(KEY), 16 + ch * 3), 'white'); d = ImageDraw.Draw(E)
    for i, e in enumerate(KEY): d.text((40 + i * cw, 2), e, fill='black')
    for j, (v, row) in enumerate(tiles):
        d.text((4, 16 + j * ch + 20), v, fill='black')
        for i, im in enumerate(row): E.paste(im, (40 + i * cw, 16 + j * ch))
    E.save(eo); t = E.copy(); t.thumbnail((800, 800)); t.save(eo[:-4] + '_thumb.png'); print(eo, E.size)
