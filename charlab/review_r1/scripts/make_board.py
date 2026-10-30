"""charlab review r1: top_picks.png (ranked best variant per character, 1x + 4x) and top3_walk_4x.gif."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'lab', 'out'); DST = os.path.join(ROOT, 'review_r1')
PICKS = [  # rank, id, name, tier, body, size
    (1, 'mechanic', 'Rio', 'medium', 'compact', 64),
    (2, 'schoolgirl', 'Hana', 'medium', 'compact', 64),
    (3, 'astronaut', 'Nova', 'medium', 'chibi', 48),
    (4, 'courier', 'Zip', 'medium', 'compact', 64),
    (5, 'shorthair', 'Mika', 'medium', 'chibi', 48),
    (6, 'runner', 'Kai', 'medium', 'compact', 64),
    (7, 'ranger', 'Fern', 'medium', 'compact', 64),
    (8, 'diver', 'Marin', 'medium', 'compact', 64),
]
BG = (122, 128, 140)
try: FONT = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 15)
except Exception: FONT = ImageFont.load_default()


def frame(cid, t, b, s, view, i):
    return Image.open(os.path.join(OUT, cid, f'{t}_{b}', str(s), f'{view}_f{i:02d}.png')).convert('RGBA')


def tight(ims):
    """common bbox over a list of frames so every crop keeps the same ground line."""
    al = np.zeros(ims[0].size[::-1], bool)
    for im in ims: al |= np.array(im)[..., 3] > 0
    ys, xs = np.nonzero(al); return (xs.min() - 1, ys.min() - 1, xs.max() + 2, ys.max() + 2)


def on_bg(im, k):
    im = im.resize((im.width * k, im.height * k), Image.NEAREST)
    o = Image.new('RGBA', im.size, BG + (255,)); o.alpha_composite(im); return o.convert('RGB')


def board():
    cols = []
    for r, cid, nm, t, b, s in PICKS:
        fr = [frame(cid, t, b, s, v, i) for v, i in (('S', 0), ('SE', 2), ('E', 2))]
        bb = tight(fr); fr = [f.crop(bb) for f in fr]
        x1 = [on_bg(f, 1) for f in fr]; x4 = [on_bg(f, 4) for f in fr]
        w = max(sum(i.width for i in x4) + 8, 220); h4 = x4[0].height
        col = Image.new('RGB', (w, 40 + 30 + h4 + 120 + 20), (40, 42, 48)); d = ImageDraw.Draw(col)
        d.text((4, 4), f'#{r} {nm} ({cid})', fill=(240, 240, 240), font=FONT)
        d.text((4, 22), f'{t} / {b} / {s}px', fill=(180, 200, 255), font=FONT)
        x = 4
        for im in x1: col.paste(im, (x, 46)); x += im.width + 6
        d.text((x + 4, 46), '1x  S|SE|E', fill=(170, 170, 170), font=FONT)
        y = 46 + x1[0].height + 10; x = 4
        for im in x4: col.paste(im, (x, y)); x += im.width
        d.text((4, y + h4 + 4), '4x  S | SE | E', fill=(170, 170, 170), font=FONT)
        cols.append(col.crop((0, 0, w, y + h4 + 26)))
    rows = [cols[:4], cols[4:]]
    W = max(sum(c.width for c in r) + 6 * (len(r) + 1) for r in rows)
    hs = [max(c.height for c in r) for r in rows]
    o = Image.new('RGB', (W, sum(hs) + 40 + 6), (30, 31, 36)); d = ImageDraw.Draw(o)
    d.text((8, 8), 'charlab review r1 - best variant per character, ranked (frames S f00, SE f02, E f02)', fill=(255, 255, 255), font=FONT)
    y = 34
    for r, h in zip(rows, hs):
        x = 6
        for c in r: o.paste(c, (x, y)); x += c.width + 6
        y += h + 6
    o.save(os.path.join(DST, 'top_picks.png'))


def gif():
    rows = []
    sel = PICKS[:3]
    seqs = []
    for r, cid, nm, t, b, s in sel:
        fr = {v: [frame(cid, t, b, s, v, i) for i in range(8)] for v in ('S', 'SE', 'E')}
        bbs = {v: tight(fr[v]) for v in fr}
        seqs.append((nm, fr, bbs))
    frames = []
    for i in range(8):
        tiles = []
        for nm, fr, bbs in seqs:
            ims = [on_bg(fr[v][i].crop(bbs[v]), 4) for v in ('S', 'SE', 'E')]
            h = max(im.height for im in ims); w = sum(im.width for im in ims) + 8 * 2
            t = Image.new('RGB', (w, h), BG); x = 0
            for im in ims: t.paste(im, (x, h - im.height)); x += im.width + 8
            tiles.append(t)
        H = max(t.height for t in tiles) + 28; W = sum(t.width for t in tiles) + 24 * (len(tiles) + 1)
        o = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(o); x = 24
        for (nm, _, _), t in zip(seqs, tiles):
            o.paste(t, (x, H - t.height)); d.text((x, 4), nm, fill=(255, 255, 255), font=FONT); x += t.width + 24
        frames.append(o.convert('P', palette=Image.ADAPTIVE, colors=64))
    frames[0].save(os.path.join(DST, 'top3_walk_4x.gif'), save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=2)


if __name__ == '__main__':
    board(); gif()
