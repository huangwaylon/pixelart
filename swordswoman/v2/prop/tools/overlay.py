import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/tools')
from landmarks import *
from PIL import Image, ImageDraw, ImageFont
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/'
T = json.load(open(R + 'prop/template.json')); Fn = ImageFont.load_default()
COL = dict(crown=(255,255,0), eye=(0,255,255), chin=(255,140,0), shoulder=(255,0,255), armpit=(180,120,255), waist=(0,255,0),
           hip=(0,140,255), crotch=(255,60,60), hem=(255,180,180), knee=(160,255,160), ankle=(255,255,160), sole=(255,255,255))
def load(path, crop):
    im = Image.open(R + path)
    if im.mode in ('P', 'RGBA', 'LA'):
        im = im.convert('RGBA'); a = np.array(im)[..., 3] > 0
    else:
        im = im.convert('RGB'); x = np.array(im).astype(int); a = np.abs(x - x[2, 2]).sum(-1) > 40
        im = im.convert('RGBA'); arr = np.array(im); arr[..., 3] = a * 255; im = Image.fromarray(arr)
    if crop == 'bbox':
        ys, xs = np.where(a); im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    return im
def fig(name, src, rows, scale_h, design=False):
    """return image scaled so H (crown..sole) = scale_h px, and y-offset of crown"""
    im = load(src, 'bbox' if (src.startswith('style') or design) else None)
    if design:  # rows were read on a 70-row resample of the bbox
        im = im.resize((round(im.width * 70 / im.height), 70), Image.BOX)
    H = rows['sole'] - rows['crown']; s = scale_h / H
    big = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.NEAREST)
    return big, rows['crown'] * s, s
def panel(items, scale_h, title=None, tmpl=True, pad=6):
    figs = []
    for name, src, rows, wids in items:
        big, cy, s = fig(name, src, rows, scale_h, design=name.startswith('design'))
        if src.startswith('masters'):  # trim empty cell margins
            a = np.array(big)[..., 3] > 0; xs = np.where(a.any(0))[0]; big = big.crop((xs.min(), 0, xs.max() + 1, big.height))
        figs.append((name, big, cy, s, rows))
    top = max(f[2] for f in figs) + 4; bot = max(f[1].height - f[2] for f in figs)
    W = sum(f[1].width + 2 * pad for f in figs) + 34; Hh = int(top + bot + 30)
    P = Image.new('RGB', (W, Hh), (96, 96, 104)); d = ImageDraw.Draw(P); x = 30
    for k in ROWS:  # template mean lines across the whole panel
        if tmpl:
            y = top + T['rows'][k]['mean'] * scale_h; d.line([(0, y), (W, y)], fill=tuple(c // 2 for c in COL[k]))
            d.text((1, y - 6), k[:4], fill=COL[k], font=Fn)
    for name, big, cy, s, rows in figs:
        ox = x + pad; oy = top - cy; P.paste(big, (int(ox), int(oy)), big)
        for k in ROWS:  # this figure's own measured lines (bright ticks)
            if rows[k] is None: continue
            y = top + (rows[k] - rows['crown']) * s; d.line([(ox - 4, y), (ox + big.width + 4, y)], fill=COL[k])
        d.text((ox, Hh - 14), name[:14], fill=(255, 255, 255), font=Fn); x += big.width + 2 * pad
    return P
def stack(ps, out, maxw=1000):
    W = max(p.width for p in ps); H = sum(p.height for p in ps); B = Image.new('RGB', (W, H), (96, 96, 104)); y = 0
    for p in ps: B.paste(p, (0, y)); y += p.height
    if B.width > maxw: B = B.resize((maxw, round(B.height * maxw / B.width)), Image.NEAREST)
    B.save(out); print(out, B.size)
if __name__ == '__main__':
    refs = [(n,) + REFS[n] for n in REFS]
    stack([panel(refs, 260)], R + 'prop/refs_sections.png')
