"""r17b: render the Gemini-generated SDF base model (track B) with pipeline/meshrender.py.

    .venv/bin/python -m pipeline.tools.r17b_sdf_render <model.obj> <tag> [--gemini DIR] [--refs DIR] [--final]

Writes 00_REVIEW/r17b_gemini_sdf_model/<tag>_turnaround.png (front, 3/4, side, back; elevation 0) and <tag>_head.png.
--final also writes <tag>_iso8.png (sprite camera, 16 deg) and <tag>_sprite48.png (48x64 pixelisation, our palette +
outline, 8 directions, x4). --gemini DIR: copies of the renders sent back to Gemini (its own model only).
--refs DIR: side-by-side with ref5/ref4 (front/side), written OUTSIDE the repo (the refs are not committed).
"""
import argparse
import os

import numpy as np
from PIL import Image

from pipeline import meshrender as mr
from pipeline.tools.r15_mesh_compare import palette, label, row, col, DIRS, ROOT
from pipeline.tools.r17_gemini_render import load, pal_hires, turnaround, sprite_row

OUT = os.path.join(ROOT, "00_REVIEW", "r17b_gemini_sdf_model")
SPRITE_H = 50.0          # standing height in sprite units for the 48x64 read (about the S4_hd height)


def heads(meshes, pal):
    top = max(T[..., 1].max() for T in meshes.values())
    return row([label(mr.render_shaded(meshes, pal, d, (18, 16), (9, 64 - (top - 52) - 47), 22, elevation=0), v)
                for v, d in (("front", "S"), ("3/4", "SE"), ("side", "E"), ("back 3/4", "NE"))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obj")
    ap.add_argument("tag")
    ap.add_argument("--refs")
    ap.add_argument("--gemini")
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    pal = pal_hires()
    hires, _ = load(a.obj, 52.0)
    tt = turnaround(hires, pal, a.tag)
    hd = heads(hires, pal)
    Image.fromarray(tt).save(os.path.join(OUT, f"{a.tag}_turnaround.png"))
    Image.fromarray(hd).save(os.path.join(OUT, f"{a.tag}_head.png"))
    _, sp = load(a.obj, SPRITE_H)
    spr = np.kron(sprite_row(sp, palette()), np.ones((4, 4, 1), np.uint8))
    if a.gemini:
        os.makedirs(a.gemini, exist_ok=True)
        Image.fromarray(tt).save(os.path.join(a.gemini, f"{a.tag}_turnaround.png"))
        Image.fromarray(hd).save(os.path.join(a.gemini, f"{a.tag}_head.png"))
        Image.fromarray(spr).save(os.path.join(a.gemini, f"{a.tag}_sprite48.png"))
    if a.refs:
        os.makedirs(a.refs, exist_ok=True)
        fs = turnaround(hires, pal, a.tag, views=[("front", "S"), ("side", "E")])
        refs = []
        for n in ("ref5", "ref4"):
            im = Image.open(f"/tmp/r17_refs/{n}.png").convert("RGB")
            im = im.resize((int(im.width * fs.shape[0] / im.height), fs.shape[0]))
            refs.append(np.asarray(im))
        Image.fromarray(row([fs] + refs)).save(os.path.join(a.refs, f"{a.tag}_vs_refs.png"))
    if a.final:
        iso = row([label(mr.render_shaded(hires, pal, d, (48, 64), (24, 57), 4, elevation=16), d) for d in DIRS])
        Image.fromarray(iso).save(os.path.join(OUT, f"{a.tag}_iso8.png"))
        Image.fromarray(spr).save(os.path.join(OUT, f"{a.tag}_sprite48.png"))
    print("wrote", a.tag)


if __name__ == "__main__":
    main()
