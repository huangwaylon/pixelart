"""facesheet.py MASTERS HEADS OUT.png [expr,expr,...]: face close-up sheet (face round 2: + measured guide lines from face_measure.json: red = illus lash top, orange = iris centre, blue = mouth, brown = chin). Rows = views S SE E NE; cols = illustration face crop
(warped source, same box) | head stamps at 6x (neutral + key expressions) | the same at 1x. Writes OUT and OUT_thumb (<=800)."""
import sys, os, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z, m96 as M
from PIL import Image, ImageDraw
MD, HD, out = sys.argv[1:4]; EX = (sys.argv[4] if len(sys.argv) > 4 else 'neutral,cheerful,determined,surprised').split(',')
keys, rgb, _ = Z.load_pal(M.PAL); S = 6; anc = json.load(open(os.path.join(HD, 'anchor.json')))
def stamp(v, e):
    p = f'{HD}/{v}_{e}.txt'
    L = [l.rstrip('\n') for l in open(p) if l.strip()]; ox, oy = map(int, [l for l in L if l.startswith('; origin')][0].split()[2:4])
    g = np.array([list(r) for r in L if not r.startswith(';')]); im = Z.render(g, keys, rgb)
    bg = Image.new('RGB', im.size, (205, 205, 205)); bg.paste(im, (0, 0), im); return bg, ox, oy
rows = []; OYS = []
for v in ['S', 'SE', 'E', 'NE']:
    ims = [stamp(v, e) for e in EX]; ox, oy = ims[0][1], ims[0][2]; w, h = ims[0][0].size
    g, meta = Z.read(f'{MD}/EC0_{v}_96'); x, b = M.illus_box(meta, ox, oy, ox + w, oy + h)
    il = Image.fromarray(x.astype(np.uint8)).crop(tuple(int(round(t)) for t in b)).resize((w * S, h * S), Image.LANCZOS)
    rows.append((v, il, [i[0] for i in ims])); OYS.append(oy)
FM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'face_measure.json')))['views']
def guides(v):
    sp = FM.get(v, {}).get('spr')
    if not sp: return []
    f = lambda a: a[0] if isinstance(a, list) else a
    ic = sp['iris_c'][0] if isinstance(sp['iris_c'][0], list) else sp['iris_c']
    ch = sp.get('chin') or sp.get('chin_bottom')
    return [(f(sp['lash_top']), (230, 0, 0)), (ic[1], (255, 140, 0)), ((sp['mouth'][2] + sp['mouth'][3]) / 2, (0, 70, 255)), (ch[1], (120, 70, 20))]
def draw_g(im, v, oy):
    d = ImageDraw.Draw(im)
    for y, c in guides(v):
        Y = int(round((y - oy) * S)); d.line([(0, Y), (im.width // 5, Y)], fill=c, width=2); d.line([(im.width - im.width // 5, Y), (im.width, Y)], fill=c, width=2)
    return im
rows = [(v, draw_g(il, v, _oy), ims, _oy) for (v, il, ims), _oy in zip(rows, OYS)]
cw = max(r[1].width for r in rows) + 10; ch = max(r[1].height for r in rows) + 10
W = 30 + cw * (1 + len(EX)) + 10 + len(EX) * 40; H = 18 + ch * len(rows)
O = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(O)
for i, t in enumerate(['illustration'] + EX): d.text((30 + i * cw + 4, 3), t, fill='black')
for j, (v, il, ims, oy_) in enumerate(rows):
    y = 18 + j * ch; d.text((4, y + 40), v, fill='black'); O.paste(il, (30, y))
    for i, im in enumerate(ims):
        O.paste(draw_g(im.resize((im.width * S, im.height * S), Image.NEAREST), v, oy_), (30 + (i + 1) * cw, y))
        O.paste(im, (30 + (1 + len(EX)) * cw + i * 40, y + 10))
O.save(out); t = O.copy(); t.thumbnail((800, 800)); t.save(out.replace('.png', '_thumb.png')); print(out, O.size, t.size)
