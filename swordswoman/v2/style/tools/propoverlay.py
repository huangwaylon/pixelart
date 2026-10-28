# measured landmark overlay -> prop/proportions_overlay.png
import sys, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/tools')
from PIL import Image, ImageDraw, ImageFont
from pk import read, to_img
D = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/'
F = ImageFont.load_default()
def load(spec):
    half = spec.endswith('/2'); spec = spec[:-2] if half else spec
    crop = None
    if '@' in spec: spec, c = spec.split('@'); crop = tuple(map(int, c.split(',')))
    if spec.endswith('.txt'): im = to_img(read(D + spec))
    else: im = Image.open(D + spec).convert('RGBA')
    if crop: x, y, w, h = crop; im = im.crop((x, y, x + w, y + h))
    if half: im = im.resize((im.width // 2, im.height // 2), Image.NEAREST)
    a = np.array(im)[..., 3] > 0; ys, xs = np.where(a); return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
# name, spec, scale, crown, eye_top, eye_bot, chin, shoulder, waist, crotch, sole, headW, shoulderW, waistW
S = [('Lyra HGSS battle', 'refs/battle/lyra.png', 4, 3, 13, 15, 19, 23, 29, 37, 64, 18, 14, 9),
     ('Dawn DPPt battle', 'refs/battle/dawn.png', 4, 3, 12, 15, 20, 22, 28, 40, 64, 20, 13, 9),
     ('Hilda BW battle', 'refs/battle/hilda-bw.png', 4, 7, 18, 21, 25, 28, 38, 45, 73, 18, 14, 11),
     ('Rosa B2W2 battle', 'refs/battle/rosa-bw.png', 4, 3, 14, 17, 22, 24, 33, 40, 66, 22, 16, 11),
     ('BW-style OW NPC f', 'refs/gen5/NPC_08.png@0,0,64,64/2', 9, 0, 12, 15, 17, 19, 23, 25, 28, 18, 11, 9),
     ('OURS C_r4 48px', 'tests/C_r4.txt', 6, 5, 14, 17, 23, 24, 29, 38, 47, 23, 22, 22),
     ('OURS A_r4 32px', 'tests/A_r4.txt', 8, 4, 10, 12, 16, 17, 19, 26, 31, 18, 17, 17)]
cols = {'crown': (255, 255, 0), 'eyes': (0, 255, 255), 'chin': (255, 128, 0), 'shoulder': (255, 0, 255), 'waist': (0, 255, 0), 'crotch': (255, 64, 64), 'sole': (255, 255, 255)}
tiles = []
for n, sp, s, cr, et, eb, ch, sh, wa, cro, so, hw, sw, ww in S:
    im = load(sp); W, H = im.size; big = im.resize((W * s, H * s), Image.NEAREST)
    t = Image.new('RGB', (max(W * s, 150) + 20, 300 + 110), (110, 110, 118)); ox = 10; oy = 300 - H * s + 5
    t.paste(big, (ox, oy), big); d = ImageDraw.Draw(t)
    for k, r in [('crown', cr), ('eyes', (et + eb + 1) / 2), ('chin', ch + 1), ('shoulder', sh), ('waist', wa), ('crotch', cro), ('sole', so + 1)]:
        y = oy + r * s; d.line([(0, y), (t.width, y)], fill=cols[k], width=1)
    Ht = so + 1 - cr; hh = ch + 1 - cr
    txt = [n, f"heads tall {Ht / hh:.1f}", f"head {hh / Ht:.0%} of height", f"legs {(so + 1 - cro) / Ht:.0%}", f"shoulder/headW {sw / hw:.2f}", f"waist/headW {ww / hw:.2f}", f"eye ctr {((et + eb + 1) / 2 - cr) / hh:.2f} down head", f"eye h {(eb - et + 1) / hh:.2f} of head"]
    for i, l in enumerate(txt): d.text((4, 308 + i * 12), l, fill=(255, 255, 255) if i else (255, 255, 0), font=F)
    tiles.append(t)
B = Image.new('RGB', (sum(t.width for t in tiles), tiles[0].height + 14), (110, 110, 118)); x = 0
for t in tiles: B.paste(t, (x, 14)); x += t.width
d = ImageDraw.Draw(B); x = 4
for k, c in cols.items(): d.text((x, 1), k, fill=c, font=F); x += 60
B.save(D + 'prop/proportions_overlay.png')
s = min(1.0, 1000 / B.width); B.resize((int(B.width * s), int(B.height * s)), Image.LANCZOS).save(D + 'prop/proportions_overlay_thumb.png'); print(B.size)
