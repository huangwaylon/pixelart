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
sheet = Image.new("RGBA", (W, 2800), BG + (255,))
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
dr.text((20, y), "pose tests (Actions pose_*): sword_ready (refs/2) iso SE + front/side, walk_contact, jump_apex, run_stride, overhead (SE / NW)", font=F, fill=(240, 240, 240))
y += 32
shots = [("pose_test", "sword_ready SE"), ("pose_test_front", "sword_ready front"), ("pose_test_side", "sword_ready side")]
for pn in ("walk_contact", "jump_apex", "run_stride", "overhead"):
    for d in ("SE", "NW"):
        shots.append((f"pose_{pn}_{d}", f"{pn} {d}"))
for i, (n, lab) in enumerate(shots):
    im = load(n + ".png")
    xx, yy = 20 + (i % 6) * 345, y + (i // 6) * 420
    if im:
        if n.startswith("pose_test_"):
            sheet.alpha_composite(on_bg(im, (330, 330)), (xx, yy))
        else:
            sheet.alpha_composite(on_bg(im.crop((96, 96, 416, 496)), (264, 330)), (xx, yy))
            sp = load(n + "_64.png")
            if sp:
                sheet.alpha_composite(on_bg(sp.crop((24, 24, 104, 128)), (64, 83), nearest=True), (xx + 266, yy))
    dr.text((xx + 4, yy + 334), lab, font=FS, fill=(255, 255, 255))
y += 2 * 420 + 10
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
        dr.rectangle((20 + (i % 22) * 40, y + 20, 56 + (i % 22) * 40, y + 56), fill=rgb)
    dr.text((20, y), "palette v2", font=FS, fill=(255, 255, 255))
except Exception as e:
    print(e)
y += 70
sheet = sheet.crop((0, 0, W, y))
sheet.convert("RGB").save(os.path.join(D, "sheet.png"))
print("[sheet]", os.path.join(D, "sheet.png"))


# ---- 1x readability sheet: 8 sprite cells on grass / dirt / dungeon, ground shadow 20x10 (2:1)
TER = [("grass", (90, 138, 60)), ("dirt", (122, 90, 58)), ("dungeon", (42, 38, 48))]
cells = [load(f"iso_{d}_64.png") for d in DIRS]
if all(cells):
    sc_ = 3
    R = Image.new("RGBA", (40 + 8 * 128 * sc_ // 2 + 8 * 10, 60 + len(TER) * (2 * 104 + 30) + 40), BG + (255,))
    d2 = ImageDraw.Draw(R)
    d2.text((20, 10), "1x + 2x readability on terrain (ground shadow = #1a1220 @35%, 20x10 px ellipse at pivot)", font=FS,
            fill=(240, 240, 240))
    yy = 40
    for tn, col in TER:
        d2.text((20, yy), tn, font=FS, fill=(240, 240, 240))
        yy += 20
        x = 20
        for c in cells:
            t = Image.new("RGBA", (128, 128), col + (255,))
            sh = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse((54, 99, 74, 109), fill=(26, 18, 32, 90))
            t.alpha_composite(sh)
            t.alpha_composite(c)
            t = t.crop((24, 24, 104, 128))
            R.alpha_composite(t, (x, yy))
            R.alpha_composite(t.resize((160, 208), Image.NEAREST), (x, yy + 104 + 4)) if False else None
            x += 84
        x += 20
        for c in cells[:4]:
            t = Image.new("RGBA", (128, 128), col + (255,))
            sh = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse((54, 99, 74, 109), fill=(26, 18, 32, 90))
            t.alpha_composite(sh)
            t.alpha_composite(c)
            t = t.crop((24, 24, 104, 128)).resize((160, 208), Image.NEAREST)
            R.alpha_composite(t, (x, yy))
            x += 164
        yy += 2 * 104 + 10
    R = R.crop((0, 0, x + 20, yy + 10))
    R.convert("RGB").save(os.path.join(D, "sheet_readability.png"))
    print("[sheet]", os.path.join(D, "sheet_readability.png"))
