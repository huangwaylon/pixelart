"""Compose turntable strips and comparison boards.

strip:  venv/bin/python -I board.py strip RENDER_DIR OUT_DIR NAME [NAME...]   -> OUT_DIR/NAME.png (front|q34|side|back [+ colour row])
board:  venv/bin/python -I board.py board OUT.png TITLE REF.png METRICS.jsonl NAME[=label] ...
        rows = experiments (front|q34|side|back clay), left column = reference, right = metric text.
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VIEWS = ['front', 'q34', 'side', 'back']
try:
    FONT = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 15)
    FONTB = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 22)
except Exception:
    FONT = FONTB = ImageFont.load_default()


def on_bg(path, size, bg=(236, 236, 240)):
    im = Image.open(path).convert('RGBA')
    if im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    b = Image.new('RGBA', im.size, bg + (255,)); b.alpha_composite(im); return b


def strip(rdir, odir, name, size=384):
    rows = [[f'{rdir}/{name}_{v}.png' for v in VIEWS]]
    if os.path.exists(f'{rdir}/{name}_col_front.png'):
        rows.append([f'{rdir}/{name}_col_{v}.png' for v in VIEWS])
    S = Image.new('RGBA', (size * 4, size * len(rows) + 28), (255, 255, 255, 255))
    d = ImageDraw.Draw(S); d.text((6, 4), name, fill=(0, 0, 0), font=FONTB)
    for r, row in enumerate(rows):
        for c, p in enumerate(row):
            S.paste(on_bg(p, size), (c * size, 28 + r * size))
    os.makedirs(odir, exist_ok=True); S.convert('RGB').save(f'{odir}/{name}.png')


def board(out, title, ref, mfile, items, rdir, size=256):
    M = {}
    if os.path.exists(mfile):
        for l in open(mfile):
            r = json.loads(l); M[r['name']] = {**M.get(r['name'], {}), **r}
    W = size * 5 + 330; H = 50 + size * len(items)
    S = Image.new('RGB', (W, H), (255, 255, 255)); d = ImageDraw.Draw(S)
    d.text((8, 10), title, fill=(0, 0, 0), font=FONTB)
    refim = Image.open(ref).convert('RGBA'); refim.thumbnail((size, size))
    for i, it in enumerate(items):
        name, label = (it.split('=', 1) + [None])[:2]
        label = label or name
        y = 50 + i * size
        rb = Image.new('RGBA', (size, size), (255, 255, 255, 255)); rb.alpha_composite(refim, ((size - refim.width) // 2, (size - refim.height) // 2))
        S.paste(rb.convert('RGB'), (0, y))
        col = os.path.exists(f'{rdir}/{name}_col_front.png')
        for c, v in enumerate(VIEWS):
            p = f'{rdir}/{name}_col_{v}.png' if (col and v in ('front', 'q34')) else f'{rdir}/{name}_{v}.png'
            if os.path.exists(p):
                S.paste(on_bg(p, size).convert('RGB'), (size * (c + 1), y))
        m = M.get(name, {})
        lines = [label[:30]]
        for k, fmt in [('sec', 'gen %ss'), ('mlx_peak_gb', 'mem %sGB'), ('tris', 'tris %s'), ('iou_front', 'IoU F %.3f'),
                       ('iou_side', 'IoU S %.3f'), ('sym_err_pct', 'sym %.2f%%'), ('floater_frac', 'float %.3f'),
                       ('sig_components', 'parts %s'), ('main_watertight', 'wt %s')]:
            if k in m and m[k] is not None:
                lines.append(fmt % m[k])
        for j, t in enumerate(lines):
            d.text((size * 5 + 10, y + 8 + j * 20), t, fill=(0, 0, 0) if j else (20, 60, 160), font=FONT)
        d.line([(0, y), (W, y)], fill=(200, 200, 200))
    S.save(out)


if __name__ == '__main__':
    if sys.argv[1] == 'strip':
        for n in sys.argv[4:]:
            strip(sys.argv[2], sys.argv[3], n)
    else:
        out, title, ref, mfile, rdir = sys.argv[2:7]
        board(out, title, ref, mfile, sys.argv[7:], rdir)
