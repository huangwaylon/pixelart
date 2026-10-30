"""charlab boards: comparison grid GIF + boards PNG + summary for one character.
  python boards.py SPEC.json TIERS BODIES SIZES
grid_SE_4x.gif : rows = tier x body, cols = size; every sprite shown at the same on-screen height (32 px x6, 48 x4, 64 x3,
                 96 x2) so the columns compare pixel density, not size.  Green corner = a designer-recommended size.
boards.png     : left = SE contact frame (f00) at the same matched scale; right = S | SE | E contact frames at true relative
                 size (all x3), so the real sprite sizes compare too.
summary.json   : per variant/size gate summary (from gates.json)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BG = (122, 128, 140); PANEL = (44, 46, 52); TXT = (235, 235, 235)
DISP = 192   # on-screen figure height for the matched grid


def font(sz=14):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc', '/Library/Fonts/Arial.ttf'):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()


def load(o, S, view, i):
    p = os.path.join(o, str(S), f'{view}_f{i:02d}.png')
    return Image.open(p).convert('RGBA') if os.path.exists(p) else None


def on_bg(im, scale, crop):
    N = im.size[0]
    x0, y0, x1, y1 = [int(round(c * N)) for c in crop]
    im = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.NEAREST)
    bg = Image.new('RGBA', im.size, BG + (255,)); bg.alpha_composite(im); return bg


def main():
    spec = json.load(open(sys.argv[1])); sid = spec['id']
    tiers, bodies = sys.argv[2].split(','), sys.argv[3].split(',')
    sizes = [int(s) for s in sys.argv[4].split(',')]
    od = os.path.join(HERE, 'out', sid)
    rec = spec.get('body', {}).get('test_sprite_heights_px', {})
    # every variant on disk (not only this run's), in canonical order
    T0, B0 = ['simple', 'medium', 'detailed'], ['chibi', 'compact', 'slim']
    rows = [(t, b) for t in T0 for b in B0 if os.path.isdir(os.path.join(od, f'{t}_{b}')) or (t in tiers and b in bodies)]
    sizes = sorted(set(sizes) | {int(x) for t, b in rows for x in (os.listdir(os.path.join(od, f'{t}_{b}')) if os.path.isdir(os.path.join(od, f'{t}_{b}')) else []) if x.isdigit()})
    CROP = (0.12, 0.03, 0.88, 0.99)
    f_big, f_sm = font(16), font(12)
    # ---------- grid GIF (SE walk)
    cellw = int(round((CROP[2] - CROP[0]) * 1.25 * DISP)); cellh = int(round((CROP[3] - CROP[1]) * 1.25 * DISP))
    LW, TH = 120, 30
    W, H = LW + cellw * len(sizes), TH + cellh * len(rows)
    nf = 8; frames = []
    summary = {}
    for i in range(nf):
        G = Image.new('RGB', (W, H), PANEL); d = ImageDraw.Draw(G)
        for c, S in enumerate(sizes):
            d.text((LW + c * cellw + 6, 6), f'{S} px  (x{DISP // S})', fill=TXT, font=f_big)
        for r, (t, b) in enumerate(rows):
            d.text((6, TH + r * cellh + cellh // 2 - 18), f'{t}\n{b}', fill=TXT, font=f_big)
            for c, S in enumerate(sizes):
                im = load(os.path.join(od, f'{t}_{b}'), S, 'SE', i)
                x, y = LW + c * cellw, TH + r * cellh
                if im is None:
                    d.text((x + 10, y + 10), 'missing', fill=(255, 120, 120), font=f_sm); continue
                G.paste(on_bg(im, DISP // S, CROP).convert('RGB'), (x, y))
                if S in rec.get(b, []): d.polygon([(x, y), (x + 16, y), (x, y + 16)], fill=(63, 185, 80))
                d.rectangle([x, y, x + cellw - 1, y + cellh - 1], outline=PANEL)
        frames.append(G.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    frames[0].save(os.path.join(od, 'grid_SE_4x.gif'), save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=1)
    # ---------- boards PNG
    left = frames[0].convert('RGB')
    s3 = 3
    colw = [int(round((CROP[2] - CROP[0]) * 1.25 * S)) * s3 * 3 + 8 for S in sizes]
    rowh = [int(round((CROP[3] - CROP[1]) * 1.25 * max(sizes))) * s3 for _ in rows]
    R = Image.new('RGB', (sum(colw) + 10, TH + sum(rowh)), PANEL); d = ImageDraw.Draw(R)
    xs = np.cumsum([0] + colw)
    for c, S in enumerate(sizes): d.text((xs[c] + 6, 6), f'{S} px  S | SE | E  (x3, true size)', fill=TXT, font=f_sm)
    y = TH
    for r, (t, b) in enumerate(rows):
        for c, S in enumerate(sizes):
            x = xs[c]
            for v in ('S', 'SE', 'E'):
                im = load(os.path.join(od, f'{t}_{b}'), S, v, 0)
                if im is None: continue
                tile = on_bg(im, s3, CROP).convert('RGB')
                R.paste(tile, (x, y + rowh[r] - tile.size[1])); x += tile.size[0]
        y += rowh[r]
    B = Image.new('RGB', (left.size[0] + R.size[0] + 12, max(left.size[1], R.size[1])), PANEL)
    B.paste(left, (0, 0)); B.paste(R, (left.size[0] + 12, 0))
    B.save(os.path.join(od, 'boards.png'))
    # ---------- summary
    for t, b in rows:
        for S in sizes:
            gp = os.path.join(od, f'{t}_{b}', str(S), 'gates.json')
            if os.path.exists(gp):
                g = json.load(open(gp)); summary[f'{t}/{b}/{S}'] = dict(PASS=g['PASS'], **g['summary'])
    json.dump(summary, open(os.path.join(od, 'summary.json'), 'w'), indent=1)
    print(f'BOARDS {sid}: grid {W}x{H}, boards {B.size[0]}x{B.size[1]}, {len(summary)} variant-sizes', flush=True)


if __name__ == '__main__':
    main()
