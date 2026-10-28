"""Derive S4 head stamps from the lock stamps: darker iso_v5 hair (shadow side H->h, lower-right),
key light upper-left kept.  Shapes, faces and bows are untouched (lock byte-identical except hair_1 -> hair_0).
  .venv/bin/python tools/hybrid/s4/relight_heads.py OUT_DIR
"""
import os, sys
import numpy as np
from PIL import Image
ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
H1 = np.array([0x74, 0x48, 0x3a]); H0 = np.array([0x42, 0x28, 0x2a])
for d in ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]:
    a = np.array(Image.open(f"{ROOT}/hybrid/lock/pixel/head_{d}.png").convert("RGBA"))
    h, w = a.shape[:2]
    for y in range(h):
        for x in range(w):
            if a[y, x, 3] and (a[y, x, :3] == H1).all():
                s = (x - 4) / 26 + (y - 9) / 22
                if s > 0.62:
                    a[y, x, :3] = H0
    Image.fromarray(a).save(f"{out}/head_{d}.png")
    print(d)
