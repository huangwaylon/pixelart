"""Palette loading. Images inside the pipeline are int arrays of palette indices; -1 = transparent."""
import json
import numpy as np


MATERIAL_FALLBACK = {"skirt": "coat_trim", "hatcuff": "hat", "pom": "hat", "coat_trim": "coat",
                     "boot_cuff": "coat_trim", "mitten": "scarf", "knit": "hatcuff", "scarf": "mustard",
                     "ribbon": "scarf"}


class Palette:
    def __init__(self, path):
        with open(path) as f:
            self.data = json.load(f)
        self.names = [c["name"] for c in self.data["colors"]]
        self.hex = [c["hex"] for c in self.data["colors"]]
        self.rgb = [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in self.hex]
        self.index = {n: i for i, n in enumerate(self.names)}
        self.ramps = dict(self.data["ramps"])
        # Optional materials fall back to related ramps so every colourway works with every outfit.
        for mat, fb in MATERIAL_FALLBACK.items():
            if mat not in self.ramps and fb in self.ramps:
                self.ramps[mat] = self.ramps[fb]
        self.bands = self.data["bands"]
        self.special = {k: self.index[v] for k, v in self.data["special"].items() if isinstance(v, str)}

    def to_rgba(self, idx):
        lut = np.zeros((len(self.rgb) + 1, 4), np.uint8)
        for i, c in enumerate(self.rgb):
            lut[i] = (*c, 255)
        return lut[np.where(idx >= 0, idx, len(self.rgb))]

    def from_rgba(self, rgba):
        """RGBA array -> index array. Raises on off-palette colours."""
        h, w = rgba.shape[:2]
        out = np.full((h, w), -1, int)
        lookup = {c: i for i, c in enumerate(self.rgb)}
        for y in range(h):
            for x in range(w):
                r, g, b, a = (int(v) for v in rgba[y, x])
                if a == 0:
                    continue
                if (r, g, b) not in lookup:
                    raise ValueError(f"off-palette colour #{r:02X}{g:02X}{b:02X} at {x},{y}")
                out[y, x] = lookup[(r, g, b)]
        return out
