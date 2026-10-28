"""r17: render a Gemini-generated base model (y-up, faces +Z, metres, height ~1) with pipeline/meshrender.py.

    .venv/bin/python -m pipeline.tools.r17_gemini_render <model.obj> <tag> [--refs DIR] [--final]

Writes 00_REVIEW/r17_gemini_model/<tag>_turnaround.png (front, 3/4, side, back hi-res, elevation 0), and with --final
also <tag>_iso8.png, <tag>_sprite48_vs_S4_hd.png and compare_turnaround.png (vs S4_hd). --gemini DIR writes the
renders sent back to Gemini (its own model only). --refs DIR writes a reference side-by-side OUTSIDE the repo
(the user's reference images are not committed).
"""
import argparse
import os

import numpy as np
from PIL import Image

from pipeline import meshrender as mr
from pipeline.tools.r15_mesh_compare import palette, label, row, col, OUT as R15_OUT, DIRS, ROOT

OUT = os.path.join(ROOT, "00_REVIEW", "r17_gemini_model")
# hi-res: keep Gemini's own colour roles (ramps dark -> light in our palette)
HIRES = {"skin": ["skin_1", "skin_2"], "hair_shadow": ["plum_0", "hair_1"], "hair": ["hair_1", "hair_2"],
         "hair_hi": ["hair_2", "hair_2"], "teal_dark": ["teal_0", "teal_0"], "teal": ["teal_0", "teal_1", "teal_2"],
         "teal_light": ["teal_1", "teal_2"], "coat": ["oat_1", "oat_2"], "coat_shadow": ["mauve", "oat_1"],
         "rust": ["hair_1", "hair_2"], "belt": ["plum_0", "hair_1"], "gold": ["gold_0", "gold_1"],
         "tights": ["ink", "char_1"], "boots": ["plum_0", "hair_1"], "fur": ["oat_1", "oat_2"],
         "iris": ["teal_0", "teal_1"], "lash": ["ink", "ink"], "eye_white": ["snow_2", "snow_3"],
         "mouth": ["crn_1", "crn_2"]}
# sprite: merge colour roles into pipeline materials so banding / inner lines behave like our sprites
SPRITE = {"hair_shadow": "hair", "hair": "hair", "hair_hi": "hair", "teal_dark": "scarf", "teal": "scarf",
          "teal_light": "scarf", "coat": "coat", "coat_shadow": "coat", "rust": "coat_trim", "belt": "boots",
          "gold": "gold", "tights": "pants", "boots": "boots", "fur": "boot_cuff", "iris": "iris", "lash": "ink",
          "eye_white": "eye_white", "mouth": "blush", "skin": "skin"}
HIRES_SIZE, HIRES_PIVOT, HIRES_PPU = (56, 64), (28, 60), 8
VIEWS = [("front", "S"), ("three_quarter", "SE"), ("side", "E"), ("back", "N")]


def load(path, height):
    raw = mr.load_obj(path, up="y", height=height, map_names=False)
    hires = {f"g_{m}": T for m, T in raw.items()}
    sprite = {}
    for m, T in raw.items():
        k = SPRITE.get(m, "coat")
        sprite[k] = np.concatenate([sprite[k], T]) if k in sprite else T
    return hires, sprite


def pal_hires():
    pal = palette()
    for m, r in HIRES.items():
        pal.ramps[f"g_{m}"] = r
    return pal


def turnaround(meshes, pal, name, views=VIEWS, ppu=HIRES_PPU):
    return row([label(mr.render_shaded(meshes, pal, d, HIRES_SIZE, HIRES_PIVOT, ppu, elevation=0), f"{name} {v}")
                for v, d in views])


def sprite_row(meshes, pal):
    out = []
    for d in DIRS:
        rgba = pal.to_rgba(mr.render_sprite(meshes, pal, d))
        out.append(np.where(rgba[..., 3:] > 0, rgba[..., :3], 255).astype(np.uint8))
    return row(out, 2)


def s4_hd_idle_row():
    S = np.asarray(Image.open(os.path.join(ROOT, "releases", "S4_hd_actions_v1", "idle", "idle_sheet.png")).convert("RGBA"))
    return row([np.where(f[..., 3:] > 0, f[..., :3], 255).astype(np.uint8)
                for f in (S[r * 64:(r + 1) * 64, 0:48] for r in range(8))], 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obj")
    ap.add_argument("tag")
    ap.add_argument("--refs")
    ap.add_argument("--gemini")
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    ours = mr.load_obj(os.path.join(R15_OUT, "ours_idle.obj"))
    h_ours = max(T[..., 1].max() for T in ours.values())
    pal = pal_hires()
    hires, sprite = load(a.obj, 52.0)              # hi-res: ~52 units tall fills the 64-unit frame
    tt = turnaround(hires, pal, a.tag)
    Image.fromarray(tt).save(os.path.join(OUT, f"{a.tag}_turnaround.png"))
    face = row([label(mr.render_shaded(hires, pal, d, (16, 14), (8, 13.5 - 0), 28, elevation=0)[::1], f"{a.tag} {v} head")
                for v, d in VIEWS[:3]]) if False else None
    if a.gemini:                                   # Gemini sees only its own model
        os.makedirs(a.gemini, exist_ok=True)
        Image.fromarray(tt).save(os.path.join(a.gemini, f"{a.tag}_turnaround.png"))
        _, sp_g = load(a.obj, h_ours)
        sp = sprite_row(sp_g, palette())
        Image.fromarray(np.kron(sp, np.ones((4, 4, 1), np.uint8))).save(os.path.join(a.gemini, f"{a.tag}_sprite48.png"))
        heads = row([mr.render_shaded(hires, pal, d, (16, 16), (8, 64 - 49), 24, elevation=0) for d in ("S", "SE", "E", "N")])
        Image.fromarray(heads).save(os.path.join(a.gemini, f"{a.tag}_head.png"))
    if a.refs:                                     # outside the repo only
        os.makedirs(a.refs, exist_ok=True)
        fs = turnaround(hires, pal, a.tag, views=[("front", "S"), ("side", "E")])
        refs = []
        for n in ("ref5", "ref4", "ref2", "ref6"):
            p = os.path.join("/tmp/gemini_mesh/refs", f"{n}.jpg")
            if os.path.exists(p):
                im = Image.open(p).convert("RGB")
                im = im.resize((int(im.width * fs.shape[0] / im.height), fs.shape[0]))
                refs.append(np.asarray(im))
        Image.fromarray(row([fs] + refs)).save(os.path.join(a.refs, f"{a.tag}_vs_refs.png"))
    if a.final:
        pal_s = palette()
        iso = []
        iso.append(row([label(mr.render_shaded(hires, pal, d, (48, 64), (24, 57), 4, elevation=16), d) for d in DIRS]))
        Image.fromarray(col(iso)).save(os.path.join(OUT, f"{a.tag}_iso8.png"))
        _, sp_g = load(a.obj, h_ours)              # same standing height as S4_hd for the 48x64 read
        ours_pal = palette()
        g = col([s4_hd_idle_row(), sprite_row(ours, ours_pal), sprite_row(sp_g, pal_s)], 2)
        Image.fromarray(np.kron(g, np.ones((4, 4, 1), np.uint8))).save(os.path.join(OUT, f"{a.tag}_sprite48_vs_S4_hd.png"))
        pal_o = palette()
        ours_hi = mr.load_obj(os.path.join(R15_OUT, "ours_idle.obj"), height=52.0)
        Image.fromarray(col([turnaround(ours_hi, pal_o, "S4_hd"), tt])).save(os.path.join(OUT, "compare_turnaround.png"))
    print("wrote", a.tag)


if __name__ == "__main__":
    main()
