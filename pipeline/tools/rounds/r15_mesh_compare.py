"""r15: compare our SDF model (meshexport) with an external (Gemini) mesh in the pipeline camera.

    .venv/bin/python -m pipeline.tools.rounds.r15_mesh_compare export            # ours -> 00_REVIEW/r15_model_gemini/ours_idle.obj
    .venv/bin/python -m pipeline.tools.rounds.r15_mesh_compare compare <gemini.obj> [tag]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

from pipeline.build import load_variant, ROOT
from pipeline.chargen import build as gen_character
from pipeline.palette import Palette
from pipeline.frames import Scene
from pipeline import meshrender as mr

OUT = os.path.join(ROOT, "00_REVIEW", "r15_model_gemini")
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]


def palette():
    return Palette(os.path.join(ROOT, "data", "palettes", "cw_oatmeal.json"))


def export_ours(variant="S4_hd"):
    from pipeline.meshexport import mesh_parts, write_obj
    spec = load_variant(variant)
    pal = Palette(os.path.join(ROOT, "data", "palettes", f"{spec['palette']}.json"))
    anim = json.load(open(os.path.join(ROOT, "data", "animations", "idle.json")))
    scene = Scene(gen_character(spec), anim, pal)
    parts, _ = scene.primitives(0, "S", lod="ref")
    meshes = mesh_parts(parts, 2.2, open_clips=True)
    os.makedirs(OUT, exist_ok=True)
    write_obj(os.path.join(OUT, f"ours_idle.obj"), meshes, pal)
    print("ours triangles", sum(len(t) for t, _ in meshes.values()))


def label(img, text):
    im = Image.fromarray(img)
    ImageDraw.Draw(im).text((4, 2), text, fill=(36, 22, 40))
    return np.asarray(im)


def row(imgs, pad=4):
    h = max(i.shape[0] for i in imgs)
    out = [np.pad(i, ((0, h - i.shape[0]), (0, pad), (0, 0)), constant_values=255) for i in imgs]
    return np.concatenate(out, 1)


def col(imgs, pad=4):
    w = max(i.shape[1] for i in imgs)
    out = [np.pad(i, ((0, pad), (0, w - i.shape[1]), (0, 0)), constant_values=255) for i in imgs]
    return np.concatenate(out, 0)


def load_both(gem_path):
    ours = mr.load_obj(os.path.join(OUT, "ours_idle.obj"))
    h = max(T[..., 1].max() for T in ours.values())
    gem = mr.load_obj(gem_path, up="z", height=h)      # same standing height for a fair shape comparison
    return ours, gem


def compare(gem_path, tag="", ref_sheet=None):
    pal = palette()
    ours, gem = load_both(gem_path)
    models = [("ours (S4_hd SDF)", ours), ("gemini", gem)]
    # hi-res turnaround: front / side / back (S, E, N) + 3/4 (SE)
    cells = []
    for name, m in models:
        cells.append(row([label(mr.render_shaded(m, pal, d, (64, 64), (32, 58), 7, elevation=0), f"{name} {d}")
                          for d in ("S", "SE", "E", "N")]))
    Image.fromarray(col(cells)).save(os.path.join(OUT, f"compare_turnaround{tag}.png"))
    # 8 iso directions at the sprite camera (16 deg), 4x
    cells = []
    for name, m in models:
        cells.append(row([label(mr.render_shaded(m, pal, d, (48, 64), (24, 57), 4), f"{name[:6]} {d}") for d in DIRS]))
    Image.fromarray(col(cells)).save(os.path.join(OUT, f"compare_iso8{tag}.png"))
    # 48x64 pixelisation vs the shipped S4_hd idle frame
    cells = []
    for name, m in models:
        sprites = [pal.to_rgba(mr.render_sprite(m, pal, d))[..., :3] for d in DIRS]
        sprites = [np.where(pal.to_rgba(mr.render_sprite(m, pal, d))[..., 3:] > 0, s, 255) for d, s in zip(DIRS, sprites)]
        cells.append(row(sprites, 2))
    sheet = ref_sheet or os.path.join(ROOT, "releases", "S4_hd_actions_v1", "idle", "idle_sheet.png")
    if os.path.exists(sheet):
        S = np.asarray(Image.open(sheet).convert("RGBA"))
        ref = [S[r * 64:(r + 1) * 64, 0:48] for r in range(8)]
        ref = [np.where(f[..., 3:] > 0, f[..., :3], 255).astype(np.uint8) for f in ref]
        cells.insert(0, row(ref, 2))
    g = col(cells, 2)
    g = np.kron(g, np.ones((4, 4, 1), np.uint8))
    Image.fromarray(g).save(os.path.join(OUT, f"compare_sprite48{tag}.png"))
    print("wrote", OUT, tag)


if __name__ == "__main__":
    if sys.argv[1] == "export":
        export_ours(*(sys.argv[2:3] or ["S4_hd"]))
    else:
        compare(sys.argv[2], *(sys.argv[3:4] or [""]))
