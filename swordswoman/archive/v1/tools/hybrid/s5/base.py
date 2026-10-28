"""Stage B: chosen snap -> base sprite with the LOCKED head stamp pasted byte-identical.
base.py NAME SRC_TAG  -> work/base_<name>.png"""
import sys
import numpy as np
from common import *

STEEL = {TRGB[k] for k in ("steel_0", "steel_1", "steel_2")}
def is_steel(px): return tuple(px[:3]) in STEEL

def head_paste(a, name):
    d = dir_of(name)
    st = load(f"{ROOT}/hybrid/lock/pixel/head_{d}.png")
    x, y = head_xy(name); h, w = st.shape[:2]
    m = st[..., 3] > 0
    chin = y + h - 1
    out = a.copy()
    # clear Gemini's own head around the stamp (keep steel = sword, keep pink ribbons outside the hair box)
    for yy in range(max(0, y - 6), chin - 2):
        for xx in range(max(0, x - 4), min(128, x + w + 4)):
            inside = 0 <= yy - y < h and 0 <= xx - x < w and m[yy - y, xx - x]
            if not inside and out[yy, xx, 3] and not is_steel(out[yy, xx]):
                out[yy, xx] = 0
    reg = out[y:y+h, x:x+w]; reg[m] = st[m]
    return out

if __name__ == "__main__":
    name, tag = sys.argv[1], sys.argv[2]
    a = load(f"{OUT}/snap/{name}_1x_{tag}.png")
    save(head_paste(a, name), f"{OUT}/work/base_{name}.png")
