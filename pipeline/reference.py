"""Character reference sheets: pixel turnaround, expression sheet, palette card, smooth 3D turnaround."""
import os

import numpy as np
from PIL import Image, ImageDraw

from .face import EYES_BY_STYLE
from .render import render_smooth

INK = (36, 22, 40)
PAPER = (244, 234, 210)
SUB = (168, 192, 224)


def _label(draw, xy, text, fill=PAPER):
    draw.text(xy, text, fill=fill)


def _pix(palette, idx, scale, bg=(223, 234, 246)):
    rgba = palette.to_rgba(idx)
    im = Image.new("RGBA", (idx.shape[1], idx.shape[0]), bg + (255,))
    im.alpha_composite(Image.fromarray(rgba))
    return im.convert("RGB").resize((idx.shape[1] * scale, idx.shape[0] * scale), Image.NEAREST)


def build_reference(scene, palette, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rest = len(scene.anim.keys) - 1              # "ready" pose == rest pose
    dirs = scene.dirs
    W, H = scene.size

    # 1. pixel turnaround (6x)
    s = 6
    turn = Image.new("RGB", (len(dirs) * W * s, H * s + 30), INK)
    d_ = ImageDraw.Draw(turn)
    for k, d in enumerate(dirs):
        turn.paste(_pix(palette, scene.render_base(rest, d, "neutral"), s), (k * W * s, 30))
        _label(d_, (k * W * s + 8, 8), d)
    turn.save(os.path.join(out_dir, "turnaround_pixel.png"))

    # 2. expression sheet: S and SE head crops (8x)
    s = 8
    exprs = list(EYES_BY_STYLE['small'].keys())
    sk = scene.render_base(rest, "S", "neutral")
    head_rows = np.nonzero((sk >= 0).any(axis=1))[0]
    top = int(head_rows.min())
    crop = (W // 2 - 16, max(top - 2, 0), W // 2 + 16, max(top - 2, 0) + 28)
    cw, chh = (crop[2] - crop[0]) * s, (crop[3] - crop[1]) * s
    ex = Image.new("RGB", (len(exprs) * cw, 2 * chh + 30), INK)
    d_ = ImageDraw.Draw(ex)
    for k, e in enumerate(exprs):
        _label(d_, (k * cw + 8, 8), e)
        for r, d in enumerate(("S", "SE")):
            idx = scene.render_base(rest, d, e)[crop[1]:crop[3], crop[0]:crop[2]]
            ex.paste(_pix(palette, idx, s), (k * cw, 30 + r * chh))
    ex.save(os.path.join(out_dir, "expressions.png"))

    # 3. palette card
    sw = 40
    groups = [("outline", [palette.names[palette.special["outline"]]])] + \
             [(m, r) for m, r in palette.data["ramps"].items()]
    card = Image.new("RGB", (130 + 4 * (sw + 4), len(groups) * (sw + 6) + 10), INK)
    d_ = ImageDraw.Draw(card)
    for r, (name, cols) in enumerate(groups):
        y = 6 + r * (sw + 6)
        _label(d_, (6, y + sw // 2 - 6), name)
        for c, cname in enumerate(cols):
            x = 130 + c * (sw + 4)
            rgb = palette.rgb[palette.index[cname]]
            d_.rectangle([x, y, x + sw, y + sw], fill=rgb)
            d_.text((x + 2, y + sw - 11), palette.hex[palette.index[cname]][1:], fill=INK if sum(rgb) > 380 else PAPER)
    card.save(os.path.join(out_dir, "palette.png"))

    # 4. smooth 3D turnaround (the "3D reference" the pixel pass is derived from)
    ppu = 6
    SW, SH = 300, 330
    t3 = Image.new("RGB", (len(dirs) * SW, SH + 30), (223, 234, 246))
    d_ = ImageDraw.Draw(t3)
    for k, d in enumerate(dirs):
        prims, _ = scene.primitives(rest, d, lod="ref")
        rgba, _, _ = render_smooth(prims, palette, (SW, SH), (SW // 2, SH - 20), ppu, cam=scene.cam,
                                   tracer=getattr(scene, "tracer", None))
        im = Image.new("RGBA", (SW, SH), (223, 234, 246, 255))
        im.alpha_composite(Image.fromarray(rgba))
        t3.paste(im.convert("RGB"), (k * SW, 30))
        _label(d_, (k * SW + 8, 8), d, fill=INK)
    t3.save(os.path.join(out_dir, "turnaround_3d.png"))

    # 5. 3D key poses (S-E 3/4 view) for animation review
    keys = Image.new("RGB", (len(scene.anim.keys) * 200, 300), (223, 234, 246))
    d_ = ImageDraw.Draw(keys)
    for i in range(len(scene.anim.keys)):
        prims, _ = scene.primitives(i, "SE", in_place=False, lod="ref")
        rgba, _, _ = render_smooth(prims, palette, (200, 280), (100, 270), 4, cam=scene.cam,
                                   tracer=getattr(scene, "tracer", None))
        im = Image.new("RGBA", (200, 280), (223, 234, 246, 255))
        im.alpha_composite(Image.fromarray(rgba))
        keys.paste(im.convert("RGB"), (i * 200, 20))
        _label(d_, (i * 200 + 6, 4), f"{i + 1} {scene.anim.anim['frames'][i]['name']}", fill=INK)
    keys.save(os.path.join(out_dir, "keyposes_3d.png"))

    # 6. combined character sheet
    a = Image.open(os.path.join(out_dir, "turnaround_pixel.png"))
    b = Image.open(os.path.join(out_dir, "turnaround_3d.png"))
    b = b.resize((a.width, int(b.height * a.width / b.width)), Image.LANCZOS)
    c = Image.open(os.path.join(out_dir, "expressions.png"))
    p = Image.open(os.path.join(out_dir, "palette.png"))
    sheet = Image.new("RGB", (a.width, 50 + a.height + b.height + max(c.height, p.height) + 20), INK)
    d_ = ImageDraw.Draw(sheet)
    _label(d_, (10, 10), f"{scene.char['name'].upper()} - character reference  |  palette {palette.data['name']}  |  "
                         f"cam {scene.cam.elevation:.1f} deg  |  frame {W}x{H} pivot {scene.pivot}")
    y = 40
    sheet.paste(b, (0, y)); y += b.height
    sheet.paste(a, (0, y)); y += a.height + 10
    sheet.paste(c, (0, y)); sheet.paste(p, (c.width + 20, y))
    sheet.save(os.path.join(out_dir, "character_sheet.png"))


SKELETON = [("pelvis", "spine"), ("spine", "chest"), ("chest", "neck"), ("neck", "head"),
            ("chest", "shoulder_L"), ("shoulder_L", "elbow_L"), ("elbow_L", "hand_L"),
            ("chest", "shoulder_R"), ("shoulder_R", "elbow_R"), ("elbow_R", "hand_R"),
            ("pelvis", "hip_L"), ("hip_L", "knee_L"), ("knee_L", "ankle_L"),
            ("pelvis", "hip_R"), ("hip_R", "knee_R"), ("knee_R", "ankle_R")]


def guide_data(scene):
    """Per direction/frame: projected joint positions (px, cell coords) + camera depth. Feeds part
    placement and editor underlays (3D model = maintained reference)."""
    out = {"frameSize": list(scene.size), "pivot": list(scene.pivot), "cameraElevation": scene.cam.elevation,
           "ppu": scene.cam.ppu, "frames": {}}
    for d in scene.dirs:
        for i in range(len(scene.anim.keys)):
            _, worlds = scene.primitives(i, d)
            j = {}
            for name, m in worlds.items():
                x, y = scene.cam.project(m[:3, 3], scene.pivot)
                j[name] = [round(x, 2), round(y, 2), round(scene.cam.depth(m[:3, 3]), 2)]
            out["frames"][f"{d}_{i + 1:02d}"] = j
    return out


def grounding_sheet(scene, palette, final, out_path, dirs=("S", "SE", "E", "N"), z=4):
    """Rows = directions, cols = frames; each cell = smooth 3D reference | pixel frame with skeleton."""
    W, H = scene.size
    n = len(scene.anim.keys)
    cw, chh = W * z * 2 + 6, H * z + 18
    img = Image.new("RGB", (cw * n, chh * len(dirs) + 4), INK)
    dr = ImageDraw.Draw(img)
    dr.fontmode = "1"
    for r, d in enumerate(dirs):
        for i in range(n):
            ox, oy = i * cw, r * chh
            dr.text((ox + 4, oy + 3), f"{d} f{i + 1} {scene.anim.anim['frames'][i]['name']}", fill=PAPER)
            prims, worlds = scene.primitives(i, d, lod="ref")
            piv = (scene.pivot[0] * z, scene.pivot[1] * z)
            rgba, _, _ = render_smooth(prims, palette, (W * z, H * z), piv, z * scene.cam.ppu, cam=scene.cam,
                                       tracer=getattr(scene, "tracer", None))
            ref = Image.new("RGBA", (W * z, H * z), (223, 234, 246, 255))
            ref.alpha_composite(Image.fromarray(rgba))
            img.paste(ref.convert("RGB"), (ox, oy + 16))
            px = _pix(palette, final[d][i], z)
            pd = ImageDraw.Draw(px)
            pts = {k: scene.cam.project(m[:3, 3], scene.pivot) for k, m in worlds.items()}
            for a, b in SKELETON:
                pd.line([(pts[a][0] * z, pts[a][1] * z), (pts[b][0] * z, pts[b][1] * z)], fill=(0, 200, 120), width=1)
            for k, (x, y) in pts.items():
                pd.rectangle([x * z - 1, y * z - 1, x * z + 1, y * z + 1], fill=(0, 160, 255))
            img.paste(px, (ox + W * z + 6, oy + 16))
            dr.rectangle([ox + W * z, oy + 16, ox + W * z + 5, oy + chh], fill=INK)        # 3D | pixel divider
            dr.rectangle([ox + cw - 3, oy, ox + cw, oy + chh], fill=(232, 184, 58))       # frame separator
            dr.text((ox + 4, oy + chh - 12), "3D ref", fill=INK)
    img.save(out_path)
