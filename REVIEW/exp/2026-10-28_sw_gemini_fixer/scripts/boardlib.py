"""board helpers: tiles on mid-grey, nearest upscales, labelled rows. Run with any venv that has PIL+numpy."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

GREY = (110, 110, 110)


def font(sz=14):
    try:
        return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', sz)
    except Exception:
        return ImageFont.load_default()


def on_grey(im):
    im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, GREY + (255,)); bg.alpha_composite(im)
    return bg.convert('RGB')


def fit(im, H, nearest=True):
    """scale to height H (integer factor if pixel art and it fits, else resample)"""
    im = on_grey(im)
    if nearest:
        k = max(1, H // im.height)
        return im.resize((im.width * k, im.height * k), Image.NEAREST)
    r = H / im.height
    return im.resize((max(1, round(im.width * r)), H), Image.LANCZOS)


def trim(im, pad=2):
    a = np.array(im.convert('RGBA'))[..., 3]
    ys, xs = np.where(a > 0)
    if not len(ys): return im
    return im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + 1 + pad), min(im.height, ys.max() + 1 + pad)))


def row(tiles, labels, H, gap=8, lab_h=34, title=None):
    """tiles: list of PIL images already sized to <=H tall"""
    f = font(13)
    W = sum(t.width for t in tiles) + gap * (len(tiles) + 1)
    top = 22 if title else 0
    out = Image.new('RGB', (W, H + lab_h + top), GREY)
    d = ImageDraw.Draw(out)
    if title: d.text((gap, 3), title, fill=(255, 255, 220), font=font(15))
    x = gap
    for t, l in zip(tiles, labels):
        out.paste(t, (x, top + H - t.height))
        for i, ln in enumerate(str(l).split('\n')[:2]):
            d.text((x, top + H + 3 + 15 * i), ln, fill=(240, 240, 240), font=f)
        x += t.width + gap
    return out


def stack(rows, gap=6):
    W = max(r.width for r in rows); H = sum(r.height for r in rows) + gap * (len(rows) - 1)
    out = Image.new('RGB', (W, H), GREY); y = 0
    for r in rows:
        out.paste(r, (0, y)); y += r.height + gap
    return out
