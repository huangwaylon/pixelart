"""r19 experiment: pixelise the Blender bake (pipeline/blender_bake.py) into S4_hd-style 48x64 sprites.

The bake's hi-res passes stand in for the SDF raycaster. A fake tracer module gives render_pixels() the baked hits and
normals, so the S4_hd variant's pixel pass runs unchanged on the Blender character:
  * majority vote per pixel over ss x ss samples (role, then the chosen role's mean light and nearest depth)
  * palette ramps and S4_hd band thresholds from N.L with the pipeline key light, plus Blender cast shadows
  * inner lines at part/depth breaks, despeckle, closed outline + sel-out, ring trim, skin edge, bow shine, orphans
  * kawaii_hd face cels placed per eye at the projected Blender eye centres (modelled eyes and face lines hidden)
Nothing in S4_hd, face.py or the clips changes: Scene.render_base runs with render_pixels swapped for this bake.

    .venv/bin/python -m pipeline.blender_sprites --bake work/r19/true_idle --clip idle --out out/r19_blender/true_idle
"""
import argparse
import json
import math
import os
import types

import numpy as np
from PIL import Image

from . import build, frames
from .chargen import build as gen_character
from .palette import Palette
from .render import RAY_START, render_pixels as _render_pixels

FACE_EYE_DIST = 7.1          # S4_hd face_eyes markers are +-3.55 head units apart
FACE_EYE_MID = np.array([0.0, 5.55, 7.127])


def load_s4(clip):
    """S4_hd character, palette and clip exactly as build.main assembles them (read-only)."""
    spec = build.load_variant("S4_hd")
    pal = Palette(os.path.join(build.ROOT, "data", "palettes", f"{spec['palette']}.json"))
    pal.data.setdefault("material_bands", {}).update(spec.get("material_bands", {}))
    for mat, names in spec.get("ramp_overrides", {}).items():
        pal.ramps[mat] = names
    with open(os.path.join(build.ROOT, "data", "animations", f"{clip}.json")) as f:
        anim = json.load(f)
    ch = gen_character(spec)
    anim["frame_size"], anim["pivot"] = spec["frame"]["size"], spec["frame"]["pivot"]
    for k, v in spec.get("anim", {}).items():
        anim[k] = v
    return ch, anim, pal


def b2p(v):
    """Blender (x, y, z) -> pipeline (x, z, -y)."""
    v = np.asarray(v, float)
    return np.stack([v[..., 0], v[..., 2], -v[..., 1]], axis=-1)


class Bake:
    def __init__(self, path):
        self.path = path
        with open(os.path.join(path, "meta.json")) as f:
            self.meta = json.load(f)
        self.ss = self.meta["ss"]
        self.roles = [tuple(r) for r in self.meta["roles"]]
        self.parts = self.meta["parts"]

    def load(self, d, i):
        return np.load(os.path.join(self.path, f"{d}_{i}.npz"))

    def head_matrix(self, d, i, cam):
        """Head-bone matrix in pipeline units whose S4_hd eye markers land on the Blender eye centres; plus the Blender
        mouth centre in that head space (the cel mouth goes where the modelled mouth is)."""
        f = self.meta["frames"][f"{d}_{i}"]
        k = self.meta["ppu_m"] / cam.ppu                     # pipeline units per metre (pixel-equivalent)
        eL, eR, mo = (b2p(f[n]) * k for n in ("eye_L", "eye_R", "mouth"))
        x = eL - eR
        s = np.linalg.norm(x) / FACE_EYE_DIST
        x /= np.linalg.norm(x)
        y = b2p(f["head_y"])
        y = y - x * np.dot(x, y)
        y /= np.linalg.norm(y)
        z = np.cross(x, y)
        R = np.stack([x, y, z], axis=1) * s
        M = np.eye(4)
        M[:3, :3] = R
        M[:3, 3] = (eL + eR) / 2 - R @ FACE_EYE_MID
        mouth_local = np.linalg.solve(R, mo - M[:3, 3])
        return M, mouth_local, s


def fake_pixels(bake, d, i):
    """render_pixels() replacement fed by the bake (same signature; ignores prims / hair_style)."""
    z = bake.load(d, i)
    role, part, alpha = z["role"], z["part"], z["alpha"]
    np_ = len(bake.parts)
    hit = (alpha > 0.5) & (role > 0)
    prim_id = np.where(hit, (role.astype(int) - 1) * np_ + np.maximum(part.astype(int) - 1, 0), -1)
    prims = []
    for r, (mat, force) in enumerate(bake.roles):
        for p, g in enumerate(bake.parts):
            prims.append({"name": f"{mat}_{g}", "material": mat, "group": g, "M": np.eye(4), "force": force})

    def fn(prims_in, palette, size, pivot, cam=None, **kw):
        light = cam.light
        nrm = b2p(z["normal"]).reshape(-1, 3)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-6)
        pid = prim_id.reshape(-1)
        lam = nrm @ light
        force = np.array([p["force"] or "" for p in prims] + [""], dtype=object)[np.where(pid >= 0, pid, len(prims))]
        nrm[force == "hi"] = light
        nrm[force == "lo"] = -light
        units = bake.meta["ppu_m"] / cam.ppu
        t = RAY_START + (z["depth"].reshape(-1) - bake.meta["cam_dist"]) * units
        # Blender cast shadow: lit by N.L but the hard sun reached it at < half strength
        shade = z["shade"].reshape(-1) * math.pi
        shadow = (lam > 0.03) & (shade < 0.5 * lam) & (force == "")
        tracer = types.SimpleNamespace(
            raycast=lambda pr, origins, direction: (np.where(pid >= 0, t, np.inf), pid, nrm),
            occluded=lambda pr, hp, dirn, groups: shadow[pid >= 0])
        kw.pop("hair_style", None)
        kw.pop("tracer", None)
        kw.pop("ss", None)
        return _render_pixels(prims, palette, size, pivot, cam=cam, ss=bake.ss, tracer=tracer, cast_shadows=True,
                              **kw)
    return fn


class BakeScene(frames.Scene):
    """S4_hd Scene whose geometry comes from the Blender bake."""

    def __init__(self, character, anim, palette, bake):
        super().__init__(character, anim, palette)
        self.bake = bake
        self.face_scale = {}

    def primitives(self, i, direction, in_place=True, lod="all"):
        M, mouth, s = self.bake.head_matrix(direction, i % self.bake_frames, self.cam)
        self.char["render"]["face_eyes"]["mouth"] = [float(v) for v in mouth]
        self.face_scale[(direction, i)] = s
        return [], {"head": M}

    def render_base(self, i, direction, expression=None):
        fi = i % self.bake_frames
        orig = frames.render_pixels
        frames.render_pixels = fake_pixels(self.bake, direction, fi)
        try:
            return super().render_base(i, direction, expression)
        finally:
            frames.render_pixels = orig

    @property
    def bake_frames(self):
        return 8 if self.bake.meta["clip"] == "walk" else 1


def render_clip(bake_dir, clip, nframes=None):
    ch, anim, pal = load_s4(clip)
    bake = Bake(bake_dir)
    sc = BakeScene(ch, anim, pal, bake)
    n = nframes or sc.bake_frames
    out = {d: [sc.render_base(i, d) for i in range(n)] for d in sc.dirs}
    return out, sc, pal


def save_sheet(frames_by_dir, dirs, pal, path):
    n = len(frames_by_dir[dirs[0]])
    sheet = np.zeros((64 * len(dirs), 48 * n, 4), np.uint8)
    for r, d in enumerate(dirs):
        for c, f in enumerate(frames_by_dir[d]):
            sheet[r * 64:(r + 1) * 64, c * 48:(c + 1) * 48] = pal.to_rgba(f)
    Image.fromarray(sheet).save(path)
    return sheet


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bake", required=True)
    ap.add_argument("--clip", default="idle")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    fr, sc, pal = render_clip(a.bake, a.clip)
    name = os.path.basename(os.path.normpath(a.out))
    save_sheet(fr, sc.dirs, pal, os.path.join(a.out, f"{name}_sheet.png"))
    for d in sc.dirs:
        for i, f in enumerate(fr[d]):
            Image.fromarray(pal.to_rgba(f)).save(os.path.join(a.out, f"{d}_{i:02d}.png"))
    with open(os.path.join(a.out, f"{name}_sheet.json"), "w") as f:
        json.dump({"frameSize": [48, 64], "pivot": list(sc.pivot), "directions": sc.dirs,
                   "layout": "rows=directions, cols=frames, no padding", "source": "Blender model B r2 bake",
                   "ppu_m": sc.bake.meta["ppu_m"], "face_scale": {f"{d}_{i}": s for (d, i), s in sc.face_scale.items()}},
                  f, indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
