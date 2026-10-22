"""Concept art / cut-scene sheets: the same 3D character rendered at high resolution with the HD face.

    python -m pipeline.portrait --variant S4_halfup_bow --out 00_REVIEW/r10/concept
Produces:
  fullbody_poses.png      every pose of data/animations/poses_concept.json, front 3/4 (SE) + front (S)
  fullbody_turnaround.png idle pose in 8 directions
  portraits.png           bust portraits, one per HD expression, front + 3/4
  *_x2.png                nearest-neighbour 2x copies for viewing
  sprite sheets (transparent) for the engine: portraits_sheet.png + .json, fullbody_sheet.png + .json
"""
import argparse
import copy
import json
import os

import numpy as np
from PIL import Image, ImageDraw

from .build import load_variant, ROOT
from .chargen import build as gen_character
from .palette import Palette
from .frames import Scene

INK = (36, 22, 40)
PAPER = (244, 234, 210)
BG = (223, 234, 246)


def scene_for(variant, ppu, frame, pivot, elevation=None, face_hd="hd_v1", anim_name="poses_concept"):
    spec = load_variant(variant)
    spec = copy.deepcopy(spec)
    spec.setdefault("render", {})
    spec["render"]["ppu"] = ppu
    spec["render"]["face_hd"] = face_hd
    spec["render"].pop("face_cels", None)
    if elevation is not None:
        spec["render"]["camera_elevation"] = elevation
    la = spec["render"].setdefault("lineart", {})
    la["smooth"] = la.get("smooth", 0.7) * 1.0
    hs = spec["render"].get("hair_style")
    if hs:
        hs = dict(hs)
        hs["line_px"] = hs.get("line_px", 0.5) * max(1.0, ppu / 1.5)   # clump lines ~1-2px at high res
        spec["render"]["hair_style"] = hs
    character = gen_character(spec)
    anim = json.load(open(os.path.join(ROOT, "data", "animations", f"{anim_name}.json")))
    anim["frame_size"], anim["pivot"] = list(frame), list(pivot)
    palette = Palette(os.path.join(ROOT, "data", "palettes", f"{spec['palette']}.json"))
    for mat, names in spec.get("ramp_overrides", {}).items():
        palette.ramps[mat] = names
    if spec.get("material_bands"):
        palette.data.setdefault("material_bands", {}).update(spec["material_bands"])
    return Scene(character, anim, palette), anim


def rgba(scene, idx):
    return Image.fromarray(scene.palette.to_rgba(idx))


def labelled_grid(cells, labels, cols, bg=BG, pad=8, top=16):
    w = max(c.width for c in cells)
    h = max(c.height for c in cells)
    rows = (len(cells) + cols - 1) // cols
    img = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + top) + pad), INK)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    for k, (c, lab) in enumerate(zip(cells, labels)):
        x = pad + (k % cols) * (w + pad)
        y = pad + (k // cols) * (h + pad + top)
        d.text((x + 2, y + 2), lab, fill=PAPER)
        cell = Image.new("RGB", (w, h), bg)
        cell.paste(c, ((w - c.width) // 2, (h - c.height) // 2), c)
        img.paste(cell, (x, y + top))
    return img


def save_sheet(cells, names, path, meta_extra):
    w = max(c.width for c in cells)
    h = max(c.height for c in cells)
    sheet = Image.new("RGBA", (w * len(cells), h), (0, 0, 0, 0))
    for k, c in enumerate(cells):
        sheet.alpha_composite(c, (k * w + (w - c.width) // 2, h - c.height))
    sheet.save(path)
    meta = dict(meta_extra, image=os.path.basename(path), frameSize=[w, h], frames=names)
    json.dump(meta, open(path.replace(".png", ".json"), "w"), indent=1)


def x2(path):
    im = Image.open(path)
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(path.replace(".png", "_x2.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ppu", type=float, default=3.0, help="full-body resolution (game sprite is 0.75)")
    ap.add_argument("--portrait-ppu", type=float, default=6.0)
    a = ap.parse_args()
    out = os.path.join(ROOT, a.out)
    os.makedirs(out, exist_ok=True)

    # ---- full body poses
    W, H = int(64 * a.ppu / 0.75 * 0.75 * 1.4), int(64 * a.ppu / 0.75 * 0.62)
    sc, anim = scene_for(a.variant, a.ppu, (W, H), (W // 2, H - int(6 * a.ppu)), elevation=12)
    names = [f["name"] for f in anim["frames"]]
    cells, labs = [], []
    for i, n in enumerate(names):
        for d in ("SE", "S"):
            cells.append(rgba(sc, sc.render_base(i, d)))
            labs.append(f"{n} ({d})")
    labelled_grid(cells, labs, cols=4).save(os.path.join(out, "fullbody_poses.png"))
    x2(os.path.join(out, "fullbody_poses.png"))
    turn = [rgba(sc, sc.render_base(0, d)) for d in sc.dirs]
    labelled_grid(turn, sc.dirs, cols=8).save(os.path.join(out, "fullbody_turnaround.png"))
    x2(os.path.join(out, "fullbody_turnaround.png"))
    save_sheet([rgba(sc, sc.render_base(i, "SE")) for i in range(len(names))], names,
               os.path.join(out, "fullbody_sheet.png"), {"variant": a.variant, "ppu": a.ppu, "direction": "SE"})

    # ---- bust portraits: crop head + shoulders at high resolution, one per expression
    P = a.portrait_ppu
    PW, PH = int(56 * P), int(70 * P)
    ps, _ = scene_for(a.variant, P, (PW, PH), (PW // 2, PH + int(14 * P)), elevation=8)
    spec = ps._face_cels("hd_v1")
    exprs = list(spec["expressions"].keys())
    pcells, plabs, sheet_cells = [], [], []
    for e in exprs:
        for d in ("S", "SE"):
            im = rgba(ps, ps.render_base(0, d, expression=e))
            bb = im.getbbox()
            if bb:
                top = bb[1]
                im = im.crop((0, max(top - 4, 0), PW, min(top - 4 + int(PH * 0.62), PH)))
            pcells.append(im)
            plabs.append(f"{e} ({d})")
            if d == "SE":
                sheet_cells.append(im)
    labelled_grid(pcells, plabs, cols=6).save(os.path.join(out, "portraits.png"))
    x2(os.path.join(out, "portraits.png"))
    save_sheet(sheet_cells, exprs, os.path.join(out, "portraits_sheet.png"),
               {"variant": a.variant, "ppu": P, "direction": "SE", "use": "dialogue portraits"})
    print("wrote", out)


if __name__ == "__main__":
    main()
