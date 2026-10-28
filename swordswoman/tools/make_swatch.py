"""Render docs/palette_swatch.png from docs/palette.json, incl. luminance and a dark-terrain strip."""
import json, sys
from PIL import Image, ImageDraw, ImageFont
pal = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "docs/palette.json"))
out = sys.argv[2] if len(sys.argv) > 2 else "docs/palette_swatch.png"
def lum(h):
    c = [int(h[i:i+2], 16)/255 for i in (1, 3, 5)]
    c = [x/12.92 if x <= 0.04045 else ((x+0.055)/1.055)**2.4 for x in c]
    return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 11)
rows = list(pal["ramps"].items())
S = 46; W = 90 + 4*S + 10; H = 30 + len(rows)*(S+6) + 110
im = Image.new("RGB", (W, H), "#ffffff"); d = ImageDraw.Draw(im)
d.text((8, 8), pal["name"] + f"  ({pal['notes']['unique_colors']} colors)", fill="#000", font=f)
y = 30
for name, ramp in rows:
    d.text((8, y+16), name, fill="#000", font=f)
    for i, h in enumerate(ramp):
        x = 90 + i*S
        d.rectangle([x, y, x+S-4, y+S-4], fill=h)
        L = lum(h); tc = "#000" if L > 0.25 else "#fff"
        d.text((x+3, y+3), h[1:], fill=tc, font=f); d.text((x+3, y+28), f"{L:.3f}", fill=tc, font=f)
    y += S+6
# dark-terrain strip: key darks on dungeon / dirt / grass
d.text((8, y+4), "darks on dungeon / dirt / grass", fill="#000", font=f); y += 20
keys = ["#1a1220", "#42282a", "#74483a", "#4a2e20", "#504462", "#92203f", "#f49ab0"]
for j, bg in enumerate(["#2a2830", "#6b5440", "#4f7a3a"]):
    yy = y + j*28
    d.rectangle([0, yy, W, yy+26], fill=bg)
    for i, h in enumerate(keys):
        d.rectangle([10+i*34, yy+4, 10+i*34+28, yy+22], fill=h)
im.save(out); print(out, im.size)
