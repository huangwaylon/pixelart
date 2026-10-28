#!/usr/bin/env python3
"""S2 holistic contact sheet: every sprite at 3x on slate + the whole set at 1x on slate / dirt / grass,
next to the look target and the Gemini source sheets (thumbnails).
  sheet.py R_DIR --out sheet.png --sources a.png,b.png,...
"""
import argparse, os
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument("r"); ap.add_argument("--out", required=True)
ap.add_argument("--sources", default=""); ap.add_argument("--title", default="")
a = ap.parse_args()
SP = os.path.join(a.r, "sprite")
ROWS = [[f"turn_{d}" for d in "S SE E NE N NW W SW".split()],
        [f"walk_SE_k{i}" for i in range(4)] + [f"slash_SE_k{i}" for i in range(4)],
        ["jump_E_crouch", "jump_E_apex", "jump_E_land"]]
BG = {"slate": (36, 32, 44), "dirt": (110, 84, 60), "grass": (74, 122, 58)}
CROP = (16, 24, 112, 120); z = 3
cw, ch = (CROP[2] - CROP[0]) * z, (CROP[3] - CROP[1]) * z
W = 8 * cw + 40
one_w = 19 * 100
H = 30 + len(ROWS) * (ch + 18) + 3 * 110 + 420
sheet = Image.new("RGB", (max(W, one_w) + 20, H), (24, 22, 30))
d = ImageDraw.Draw(sheet)
d.text((10, 8), a.title, fill=(240, 240, 240))
y = 30
for row in ROWS:
    for i, n in enumerate(row):
        im = Image.open(os.path.join(SP, n + ".png")).convert("RGBA").crop(CROP)
        t = Image.new("RGBA", im.size, BG["slate"] + (255,)); t.alpha_composite(im)
        t = t.resize((cw, ch), Image.NEAREST)
        x = 10 + i * cw
        sheet.paste(t.convert("RGB"), (x, y + 14))
        d.text((x + 3, y + 1), n, fill=(200, 200, 210))
        # baseline tick
        d.line([(x, y + 14 + (104 - CROP[1]) * z + z), (x + 8, y + 14 + (104 - CROP[1]) * z + z)], fill=(0, 200, 220))
    y += ch + 18
allnames = sum(ROWS, [])
for bgn, col in BG.items():
    strip = Image.new("RGB", (len(allnames) * 100, 110), col)
    for i, n in enumerate(allnames):
        im = Image.open(os.path.join(SP, n + ".png")).convert("RGBA").crop((14, 0, 114, 110))
        strip.paste(im, (i * 100, 0), im)
    sheet.paste(strip, (10, y)); d.text((12, y + 2), f"1x {bgn}", fill=(255, 255, 255)); y += 112
# look target + sources
x = 10
for p in ["concept/chibi_iso_v5.png"] + [s for s in a.sources.split(",") if s]:
    im = Image.open(p).convert("RGB"); im.thumbnail((620, 400))
    sheet.paste(im, (x, y + 4)); d.text((x + 2, y + 4), os.path.basename(p), fill=(255, 80, 80)); x += im.width + 10
sheet.save(a.out)
print(a.out, sheet.size)
