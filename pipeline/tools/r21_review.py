"""r21: S4_hd (old) vs S4_hd2 (refined) review boards -> 00_REVIEW/r21_s4_hd2/<round>/.

    .venv/bin/python -m pipeline.tools.r21_review quick [out.png]     # fast new-model turnaround + heads (iteration)
    .venv/bin/python -m pipeline.tools.r21_review round r1            # full round boards (needs idle + walk builds)

Hi-res views use render.render_smooth (the same lambert-on-palette-ramp shading with lavender shadow tones as the
r12 S4_hd_turnaround_3d.png / build reference turnaround), LOD ref, idle frame 0.
"""
import json
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

from pipeline.build import load_variant, ROOT
from pipeline.chargen import build as gen_character
from pipeline.palette import Palette
from pipeline.frames import Scene
from pipeline.render import render_smooth
from pipeline import sdf

# hi-res boards only: more sphere-tracing steps so grazing silhouettes don't drop rays (both models alike; the sprite
# builds keep sdf.STEPS = 48)
sdf.STEPS = 128

OUT = os.path.join(ROOT, "00_REVIEW", "r21_s4_hd2")
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
VIEWS = [("front", "S"), ("3/4", "SE"), ("side", "E"), ("back", "N")]
BG = (223, 234, 246)
INK = (36, 22, 40)
OLD, NEW = "S4_hd", "S4_hd2"
_CACHE = {}


def scene(variant, clip="idle"):
    key = (variant, clip)
    if key in _CACHE:
        return _CACHE[key]
    spec = load_variant(variant)
    pal = Palette(os.path.join(ROOT, "data", "palettes", f"{spec['palette']}.json"))
    if spec.get("material_bands"):
        pal.data.setdefault("material_bands", {}).update(spec["material_bands"])
    for m, names in spec.get("ramp_overrides", {}).items():
        pal.ramps[m] = names
    anim = json.load(open(os.path.join(ROOT, "data", "animations", f"{clip}.json")))
    if "frame" in spec:
        anim["frame_size"], anim["pivot"] = spec["frame"]["size"], spec["frame"]["pivot"]
    sc = Scene(gen_character(spec), anim, pal)
    _CACHE[key] = (sc, pal)
    return sc, pal


def view(variant, d, ppu, size, focus="body", frame=0):
    """Smooth render of one direction, centred on a focus point (bone-local) -> RGB uint8."""
    sc, pal = scene(variant)
    prims, worlds = sc.primitives(frame, d, lod="ref")
    bone, off = {"head": ("head", [0, 8.6, -1.5]), "body": ("spine", [0, -1.5, 0]), "full": ("spine", [0, 3.0, 0]),
                 "legs": ("pelvis", [0, -6, 0])}[focus]
    p = worlds[bone][:3, :3] @ np.asarray(off, float) + worlds[bone][:3, 3]
    W, H = size
    piv = (W / 2 - ppu * float(p @ sc.cam.right), H / 2 + ppu * float(p @ sc.cam.up))
    rgba, _, _ = render_smooth(prims, pal, (W, H), piv, ppu, cam=sc.cam, tracer=sc.tracer)
    im = Image.new("RGBA", (W, H), BG + (255,))
    im.alpha_composite(Image.fromarray(rgba))
    return im.convert("RGB")


def grid(rows, title, col_labels=None):
    """rows: [(label, [PIL images])] -> one labelled board."""
    pad, lh = 6, 16
    cw = max(im.width for _, ims in rows for im in ims)
    ch = max(im.height for _, ims in rows for im in ims)
    nc = max(len(ims) for _, ims in rows)
    W = nc * (cw + pad) + pad
    H = lh + (lh if col_labels else 0) + len(rows) * (ch + lh + pad) + pad
    board = Image.new("RGB", (W, H), INK)
    dr = ImageDraw.Draw(board)
    dr.text((pad, 3), title, fill=(244, 234, 210))
    y = lh
    if col_labels:
        for k, c in enumerate(col_labels):
            dr.text((pad + k * (cw + pad), y + 2), c, fill=(244, 234, 210))
        y += lh
    for label, ims in rows:
        dr.text((pad, y + 2), label, fill=(244, 234, 210))
        y += lh
        for k, im in enumerate(ims):
            board.paste(im, (pad + k * (cw + pad), y))
        y += ch + pad
    return board


def turnaround(variants, ppu=7.0, size=(330, 420)):
    rows = [(v, [view(v, d, ppu, size, "full") for _, d in VIEWS]) for v in variants]
    return grid(rows, "turnaround (render_smooth, LOD ref, idle f0): " + " vs ".join(variants), [n for n, _ in VIEWS])


def heads(variants, ppu=17.0, size=(460, 460)):
    rows = [(v, [view(v, d, ppu, size, "head") for _, d in VIEWS]) for v in variants]
    return grid(rows, "head close-ups: " + " vs ".join(variants), [n for n, _ in VIEWS])


def bodies(variants, ppu=16.0, size=(400, 470)):
    rows = [(v, [view(v, d, ppu, size, "body") for _, d in VIEWS]) for v in variants]
    return grid(rows, "body close-ups: " + " vs ".join(variants), [n for n, _ in VIEWS])


# ------------------------------------------------------------------ sprites (from the builds in out/variants)
def sheet(variant, clip):
    p = os.path.join(ROOT, "out", "variants", f"{variant}__{clip}", f"{clip}_sheet.png")
    return Image.open(p).convert("RGBA"), json.load(open(p.replace(".png", ".json")))


def cell(sh, d, i, W=48, H=64):
    r = DIRS.index(d)
    return sh.crop((i * W, r * H, i * W + W, r * H + H))


def sprite_row(variant, clip="idle", i=0, scale=1, bg=(200, 205, 212, 255)):
    sh, _ = sheet(variant, clip)
    im = Image.new("RGBA", (48 * 8, 64), bg)
    for k, d in enumerate(DIRS):
        im.alpha_composite(cell(sh, d, i), (k * 48, 0))
    return im.convert("RGB").resize((48 * 8 * scale, 64 * scale), Image.NEAREST)


def idle_board(variants):
    out = {}
    for s in (1, 2, 8):
        out[s] = grid([(v, [sprite_row(v, "idle", 0, s)]) for v in variants],
                      f"idle f0, 8 dirs (S SE E NE N NW W SW) at {s}x: " + " vs ".join(variants))
    return out


def walk_gif(variants, path, scale=3):
    sheets = [sheet(v, "walk") for v in variants]
    n = len(sheets[0][1]["frames"]) if isinstance(sheets[0][1]["frames"], list) else 8
    durs = [f.get("duration_ms", 100) for f in sheets[0][1]["frames"]]
    frames = []
    for i in range(n):
        rows = []
        for v, (sh, _) in zip(variants, sheets):
            im = Image.new("RGBA", (48 * 8, 64), (200, 205, 212, 255))
            for k, d in enumerate(DIRS):
                im.alpha_composite(cell(sh, d, i), (k * 48, 0))
            rows.append(im.convert("RGB"))
        board = Image.new("RGB", (48 * 8, 64 * len(rows) + 10 * len(rows)), INK)
        dr = ImageDraw.Draw(board)
        for k, (v, r) in enumerate(zip(variants, rows)):
            board.paste(r, (0, k * 74 + 10))
            dr.text((2, k * 74), v, fill=(244, 234, 210))
        frames.append(board.resize((board.width * scale, board.height * scale), Image.NEAREST))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, optimize=False)


def mesh_board(od, write_files=False):
    """Exported meshes (meshexport, as the build writes them: S4_hd default grid vs S4_hd2 polished) rendered
    flat-shaded per triangle (meshrender.render_shaded) - shows marching-grid facets / terracing directly."""
    from pipeline import meshexport as mx, meshrender as mr
    rows = []
    for v in (OLD, NEW):
        sc, pal = scene(v)
        parts, _ = sc.primitives(0, "S", lod="ref")
        cfg = sc.char.get("render", {}).get("mesh_export") or {}
        pol = bool(cfg.get("polish"))
        budget = int(cfg.get("max_tris", 420000)) if pol else mx.MAX_TRIS
        s = 0.9 if pol else 1.8
        for _ in range(4):
            meshes = mx.mesh_parts(parts, s, open_clips=pol)
            tri = sum(len(t) for t, _ in meshes.values())
            if tri <= budget:
                break
            s *= max(1.05, (tri / (0.97 * budget)) ** 0.5)
        if pol:
            meshes = mx.polish(meshes, int(cfg.get("smooth_iters", 12)))
        if write_files and v == NEW:
            mx.write_obj(os.path.join(od, "S4_hd2_idle.obj"), meshes, pal, normals=True)
            mx.write_stl(os.path.join(od, "S4_hd2_idle.stl"), meshes)
        tri = sum(len(t) for t, _ in meshes.values())
        M = {m: T for m, (T, _) in meshes.items()}
        ims = []
        for d, (sz, piv, ppu) in (("S", ((44, 34), (22, 55), 14)), ("SE", ((44, 34), (22, 55), 14))):
            ims.append(Image.fromarray(mr.render_shaded(M, pal, d, sz, piv, ppu, elevation=sc.cam.elevation, ss=2)))
        rows.append((f"{v}: {tri} triangles ({'welded + Taubin-smoothed, open face clip' if pol else 'default export'})", ims))
    return grid(rows, "exported mesh (head + bust), flat-shaded per triangle")


def full_round(tag):
    od = os.path.join(OUT, tag)
    os.makedirs(od, exist_ok=True)
    vs = [OLD, NEW]
    t0 = time.time()
    turnaround(vs).save(os.path.join(od, "a_turnaround_old_vs_new.png"))
    heads(vs).save(os.path.join(od, "b_head_closeups_old_vs_new.png"))
    bodies(vs).save(os.path.join(od, "c_body_closeups_old_vs_new.png"))
    for s, im in idle_board(vs).items():
        im.save(os.path.join(od, f"d_idle_8dir_{s}x_old_vs_new.png"))
    walk_gif(vs, os.path.join(od, "e_walk_8dir_old_vs_new.gif"))
    mesh_board(od, write_files=tag == "latest").save(os.path.join(od, "f_mesh_export_old_vs_new.png"))
    print("round boards ->", od, f"{time.time() - t0:.0f}s")


def quick(path):
    t0 = time.time()
    a = turnaround([NEW], ppu=5.0, size=(240, 300))
    b = heads([NEW], ppu=14.0, size=(300, 300))
    W = max(a.width, b.width)
    im = Image.new("RGB", (W, a.height + b.height), INK)
    im.paste(a, (0, 0))
    im.paste(b, (0, a.height))
    im.save(path)
    print("quick ->", path, f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    if sys.argv[1] == "quick":
        quick(sys.argv[2] if len(sys.argv) > 2 else "/tmp/r21_quick.png")
    elif sys.argv[1] == "round":
        full_round(sys.argv[2])
    elif sys.argv[1] == "mesh":
        mesh_board("/tmp").save("/tmp/r21_mesh.png")
    elif sys.argv[1] == "old":
        heads([OLD], ppu=14.0, size=(300, 300)).save("/tmp/r21_old_heads.png")


def zoom(variant, d, ppu, focus, off, size=(500, 500), path="/tmp/r21_zoom.png", frame=0):
    """Ad-hoc close-up: focus bone + bone-local offset."""
    sc, pal = scene(variant)
    prims, worlds = sc.primitives(frame, d, lod="ref")
    p = worlds[focus][:3, :3] @ np.asarray(off, float) + worlds[focus][:3, 3]
    W, H = size
    piv = (W / 2 - ppu * float(p @ sc.cam.right), H / 2 + ppu * float(p @ sc.cam.up))
    rgba, _, _ = render_smooth(prims, pal, (W, H), piv, ppu, cam=sc.cam, tracer=sc.tracer)
    im = Image.new("RGBA", (W, H), BG + (255,))
    im.alpha_composite(Image.fromarray(rgba))
    im.convert("RGB").save(path)
