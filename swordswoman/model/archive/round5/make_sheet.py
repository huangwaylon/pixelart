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
sheet = Image.new("RGBA", (W, 6000), BG + (255,))
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
dr.text((20, y), "pose tests (Actions pose_*): sword_ready (refs/2), walk_contact, jump_apex, run_stride, overhead (high guard), attack_slash_mid (SE / NW)", font=F, fill=(240, 240, 240))
y += 32
shots = [("pose_test", "sword_ready SE"), ("pose_sword_ready_NW", "sword_ready NW"),
         ("pose_test_front", "sword_ready front"), ("pose_test_side", "sword_ready side")]
for pn in ("walk_contact", "jump_apex", "run_stride", "overhead", "attack_slash_mid"):
    for d in ("SE", "NW"):
        shots.append((f"pose_{pn}_{d}", f"{pn} {d}"))
for i, (n, lab) in enumerate(shots):
    im = load(n + ".png")
    xx, yy = 20 + (i % 6) * 345, y + (i // 6) * 420
    if im:
        if n in ("pose_test_front", "pose_test_side"):
            sheet.alpha_composite(on_bg(im, (330, 330)), (xx, yy))
        else:
            sheet.alpha_composite(on_bg(im.crop((96, 96, 416, 496)), (264, 330)), (xx, yy))
            sp = load(n + "_64.png")
            if sp:
                sheet.alpha_composite(on_bg(sp.crop((24, 24, 104, 128)), (64, 83), nearest=True), (xx + 266, yy))
    dr.text((xx + 4, yy + 334), lab, font=FS, fill=(255, 255, 255))
y += ((len(shots) + 5) // 6) * 420 + 10
# keyframed cycles (anim_idle / anim_walk, 8 frames each, iso SE)
LABEL = {"anim_idle": "cyclic, 8 f, IK feet planted", "anim_walk": "cyclic, 8 f, IK feet planted",
         "anim_run": "round 5: cyclic, 8 f, flight phase", "anim_jump": "round 5: 8 f, anticipation / air / landing",
         "anim_slash": "round 5: 6 f, windup / cut / follow-through",
         "anim_overhead_slash": "round 5: 8 f, windup over the head / strike / follow-through"}
for an, dd in [("anim_idle", "SE"), ("anim_walk", "SE"), ("anim_run", "SE"), ("anim_jump", "SE"),
               ("anim_slash", "SE"), ("anim_overhead_slash", "SE"), ("anim_overhead_slash", "NW")]:
    fr = []
    while os.path.exists(os.path.join(D, "_masks", f"{an}_{dd}_f{len(fr)}.png")):
        fr.append(os.path.join(D, "_masks", f"{an}_{dd}_f{len(fr)}.png"))
    if not fr:
        continue
    dr.text((20, y), f"{an} ({LABEL.get(an, '')}) - iso {dd}, 256 render + sprite cell",
            font=F, fill=(240, 240, 240))
    y += 32
    strip = Image.new("RGBA", (len(fr) * 200, 250), TILE_BG + (255,))
    strip64 = Image.new("RGBA", (len(fr) * 80, 96), TILE_BG + (255,))
    for i, f in enumerate(fr):
        im = Image.open(f).convert("RGBA").crop((28, 20, 228, 250))
        sheet.alpha_composite(on_bg(im, (200, 230)), (20 + i * 255, y))
        strip.alpha_composite(im, (i * 200, 0))
        sp = load(f"{an}_{dd}_f{i}_64.png")
        if sp:
            c = sp.crop((24, 24, 104, 120))
            sheet.alpha_composite(on_bg(c, (40, 48), nearest=True), (20 + i * 255 + 205, y))
            strip64.alpha_composite(c, (i * 80, 0))
        dr.text((24 + i * 255, y + 2), f"f{i}", font=FS, fill=(255, 255, 255))
    strip.convert("RGB").save(os.path.join(D, f"{an}_{dd}.png"))
    strip64.save(os.path.join(D, f"{an}_{dd}_strip64.png"))
    y += 245
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


# ---- round 4 (GD/TA): both cycles in ALL 8 directions at sprite scale (1x + 3x nearest)
rows8 = []
for an in ("anim_idle", "anim_walk"):
    for d in DIRS:
        fr = [load(f"{an}_{d}_f{i}_64.png") for i in range(8)]
        if all(fr):
            rows8.append((an, d, fr))
if rows8:
    cw, chh, sc3 = 80, 90, 3
    A = Image.new("RGBA", (160 + 8 * (cw * sc3 + 8) + 8 * (cw + 4), 60 + len(rows8) * (chh * sc3 + 10)), BG + (255,))
    da = ImageDraw.Draw(A)
    da.text((20, 14), f"round {RND}: anim_idle / anim_walk, 8 frames x 8 directions (per-direction Actions "
            "anim_<idle|walk>_<DIR>), sprite cells at 3x nearest + 1x strip", font=F, fill=(240, 240, 240))
    yy = 60
    for an, d, fr in rows8:
        da.text((20, yy + 10), f"{an[5:]} {d}", font=F, fill=(240, 240, 240))
        for i, im in enumerate(fr):
            c = im.crop((24, 20, 104, 110))
            A.alpha_composite(on_bg(c, (cw * sc3, chh * sc3), nearest=True), (160 + i * (cw * sc3 + 8), yy))
            A.alpha_composite(on_bg(c, (cw, chh), nearest=True),
                              (160 + 8 * (cw * sc3 + 8) + i * (cw + 4), yy))
        yy += chh * sc3 + 10
    A.convert("RGB").save(os.path.join(D, "sheet_anim8.png"))
    print("[sheet]", os.path.join(D, "sheet_anim8.png"))
