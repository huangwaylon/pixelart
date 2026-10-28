"""Contact sheet for a model render round.  .venv/bin/python model/make_sheet.py <render_dir> [round]"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

D = sys.argv[1]
RND = sys.argv[2] if len(sys.argv) > 2 else "?"
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
BG = (58, 54, 64)
TILE_BG = (92, 88, 98)


def font(sz):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


F, FS = font(22), font(16)


def load(name):
    p = os.path.join(D, name)
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None


def on_bg(im, size, bg=TILE_BG, nearest=False):
    im = im.resize(size, Image.NEAREST if nearest else Image.LANCZOS)
    t = Image.new("RGBA", size, bg + (255,))
    t.alpha_composite(im)
    return t


W = 8 * 260 + 40
rows = []
# row 1: ortho 4 x 400
orth = [("ortho_front", "front"), ("ortho_side", "side (her left)"), ("ortho_back", "back"), ("ortho_34", "3/4")]
sheet = Image.new("RGBA", (W, 2200), BG + (255,))
dr = ImageDraw.Draw(sheet)
dr.text((20, 10), f"Akane chibi model - round {RND}   (H = head height; palette-only cel shading)", font=F,
        fill=(240, 240, 240))
y = 50
for i, (n, lab) in enumerate(orth):
    im = load(n + ".png")
    if im:
        sheet.alpha_composite(on_bg(im, (500, 500)), (20 + i * 520, y))
    dr.text((24 + i * 520, y + 4), lab, font=FS, fill=(255, 255, 255))
y += 520
dr.text((20, y), "iso game camera (ortho, 30 deg elev) - 512 renders", font=F, fill=(240, 240, 240))
y += 32
for i, d in enumerate(DIRS):
    im = load(f"iso_{d}.png")
    if im:
        sheet.alpha_composite(on_bg(im.crop((96, 96, 416, 496)), (240, 300)), (20 + i * 260, y))
    dr.text((24 + i * 260, y + 4), d, font=F, fill=(255, 255, 255))
y += 340
dr.text((20, y), "sprite scale (128 cell, pivot 64,104, ~56 px tall), shown 1x and 3x nearest", font=F,
        fill=(240, 240, 240))
y += 32
for i, d in enumerate(DIRS):
    im = load(f"iso_{d}_64.png")
    if im:
        sheet.alpha_composite(on_bg(im, (128, 128), nearest=True), (20 + i * 260, y))
        c = im.crop((24, 24, 104, 128))
        sheet.alpha_composite(on_bg(c, (240, 312), nearest=True), (20 + i * 260, y + 140))
    dr.text((24 + i * 260, y + 2), d, font=FS, fill=(255, 255, 255))
y += 470
dr.text((20, y), "pose_test: rig posed in sword-ready stance (refs/2.png), iso SE", font=F, fill=(240, 240, 240))
y += 32
im = load("pose_test.png")
if im:
    sheet.alpha_composite(on_bg(im, (500, 500)), (20, y))
im = load("pose_test_64.png")
if im:
    sheet.alpha_composite(on_bg(im, (128, 128), nearest=True), (540, y))
    sheet.alpha_composite(on_bg(im, (384, 384), nearest=True), (690, y))
# palette strip
try:
    pal = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs",
                                      "palette.json")))
    cols = [pal["outline"]] + [c for r in pal["ramps"].values() for c in r]
    seen = []
    for c in cols:
        if c not in seen:
            seen.append(c)
    for i, c in enumerate(seen):
        h = c.lstrip("#")
        rgb = tuple(int(h[k:k + 2], 16) for k in (0, 2, 4))
        dr.rectangle((1100 + (i % 11) * 40, y + 20 + (i // 11) * 40, 1136 + (i % 11) * 40, y + 56 + (i // 11) * 40),
                     fill=rgb)
    dr.text((1100, y), "palette v2", font=FS, fill=(255, 255, 255))
except Exception as e:
    print(e)
y += 520
sheet = sheet.crop((0, 0, W, y))
sheet.convert("RGB").save(os.path.join(D, "sheet.png"))
print("[sheet]", os.path.join(D, "sheet.png"))
