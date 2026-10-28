"""Shared helpers for the pixel hand-cleanup toolchain (tools/pixel/*).

Paths (relative to the project root):
  pixel/base/<anim>/<DIR>/fNN.png        snapshot of renders/model_round_N (never edited by hand)
  pixel/base/<anim>/_id/<DIR>/fNN.png    object-ID pass for the frame (region-aware lint), if rendered
  pixel/base/<anim>/SNAPSHOT.json        which round, hashes, provenance
  pixel/source/<anim>/<DIR>/fNN.png      512 px toon render, same camera / framing (x4)
  pixel/overrides/<anim>/<DIR>/fNN.json  sparse hand edits (list of {x,y,color,reason,author,...})
  pixel/clean/<anim>/<DIR>/fNN.png       base + overrides (px.py apply)
Frame numbers NN are 0-based everywhere (f00 == renders' _f0_).
"""
import hashlib
import json
import os
import re

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
PIXEL = os.path.join(ROOT, "pixel")
CELL = 128
PIVOT = (64, 104)


def rel(p):
    return os.path.relpath(p, ROOT)


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb[:3])


class Palette:
    """docs/palette.json (LOCKED).  Canonical names: 'outline', then <ramp>_<i> for every ramp tone
    that is not already named (leather_0 / dark_0 == outline are accepted as aliases)."""

    def __init__(self, path=None):
        path = path or os.path.join(ROOT, "docs", "palette.json")
        self.raw = json.load(open(path))
        self.names, self.rgb, self.alias = [], [], {}
        self.by_rgb = {}
        self.ramp_of = {}          # name -> (ramp, index)
        self._add("outline", hx(self.raw["outline"]))
        for rn, cols in self.raw["ramps"].items():
            for i, c in enumerate(cols):
                nm = f"{rn}_{i}"
                rgb = hx(c)
                if rgb in self.by_rgb:
                    self.alias[nm] = self.by_rgb[rgb]
                else:
                    self._add(nm, rgb)
                self.ramp_of.setdefault(nm, (rn, i))
        self.index = {n: i for i, n in enumerate(self.names)}

    def _add(self, name, rgb):
        self.by_rgb[rgb] = name
        self.names.append(name)
        self.rgb.append(rgb)

    def resolve(self, name):
        """palette name / alias / '#hex' (must be in the palette) -> canonical name, or 'clear'."""
        n = name.strip()
        if n.lower() in ("clear", "erase", "transparent"):
            return "clear"
        if n.startswith("#"):
            rgb = hx(n)
            if rgb in self.by_rgb:
                return self.by_rgb[rgb]
            raise ValueError(f"{n} is not in the locked palette")
        n = self.alias.get(n, n)
        if n not in self.index:
            raise ValueError(f"unknown colour '{name}'. valid: clear, {', '.join(self.names)}"
                             f" (aliases: {', '.join(sorted(self.alias))})")
        return n

    def rgba(self, name):
        if name == "clear":
            return (0, 0, 0, 0)
        return tuple(self.rgb[self.index[name]]) + (255,)

    def name_of(self, rgba):
        if rgba[3] == 0:
            return "clear"
        return self.by_rgb.get(tuple(int(v) for v in rgba[:3]))

    def ramp(self, rn):
        return [hx(c) for c in self.raw["ramps"][rn]]

    def json(self):
        return [{"name": n, "hex": to_hex(c)} for n, c in zip(self.names, self.rgb)]


def load_rgba(path):
    return np.array(Image.open(path).convert("RGBA"))


def save_rgba(a, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(a.astype(np.uint8), "RGBA").save(path)


def file_hash(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def pixel_hash(a):
    """hash of the decoded RGBA pixels (robust to PNG re-encoding)."""
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:16]


def frame_dir(kind, anim, d):
    return os.path.join(PIXEL, kind, anim, d)


def frame_path(kind, anim, d, k, ext="png"):
    return os.path.join(PIXEL, kind, anim, d, f"f{k:02d}.{ext}")


FRAME_RE = re.compile(r"^f(\d+)\.png$")


def frames_of(anim, d, kind="base"):
    p = frame_dir(kind, anim, d)
    if not os.path.isdir(p):
        return []
    return sorted(int(FRAME_RE.match(f).group(1)) for f in os.listdir(p) if FRAME_RE.match(f))


def dirs_of(anim, kind="base"):
    return [d for d in DIRS if frames_of(anim, d, kind)]


def snapshot_info(anim):
    p = os.path.join(PIXEL, "base", anim, "SNAPSHOT.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def base_hash(anim, d, k):
    info = snapshot_info(anim)
    h = info.get("frames", {}).get(d, {}).get(f"f{k:02d}")
    if h:
        return h
    p = frame_path("base", anim, d, k)
    return pixel_hash(load_rgba(p)) if os.path.exists(p) else None


def load_overrides(anim, d, k):
    p = frame_path("overrides", anim, d, k, "json")
    return json.load(open(p)) if os.path.exists(p) else []


def save_overrides(anim, d, k, edits):
    p = frame_path("overrides", anim, d, k, "json")
    if not edits:
        if os.path.exists(p):
            os.remove(p)
        return p
    os.makedirs(os.path.dirname(p), exist_ok=True)
    edits = sorted(edits, key=lambda e: (e["y"], e["x"]))
    with open(p, "w") as f:
        f.write("[\n" + ",\n".join(json.dumps(e) for e in edits) + "\n]\n")
    return p


def compose(base, edits, pal):
    out = base.copy()
    for e in edits:
        out[e["y"], e["x"]] = pal.rgba(e["color"])
    # hygiene: fully transparent pixels carry no colour (base renders can leave RGB under alpha 0,
    # which px.py cannot erase because the pixel already reads as 'clear'). Invisible change only.
    out[out[..., 3] == 0] = 0
    return out


def anim_ms(anim, n):
    """per-frame durations from docs/anim_spec.json; if the spec frame count differs from the
    rendered frame count, every frame gets the spec's mean duration (and a warning is returned)."""
    spec = json.load(open(os.path.join(ROOT, "docs", "anim_spec.json")))
    a = spec["anims"].get(anim)
    if not a:
        return [100] * n, f"anim '{anim}' not in anim_spec.json; using 100 ms"
    ms = a["ms"]
    if len(ms) == n:
        return list(ms), None
    m = int(round(sum(ms) / len(ms)))
    return [m] * n, f"anim_spec '{anim}' has {len(ms)} frames, renders have {n}: using {m} ms/frame"


def anim_loops(anim):
    spec = json.load(open(os.path.join(ROOT, "docs", "anim_spec.json")))
    return spec["anims"].get(anim, {}).get("loop", True)
