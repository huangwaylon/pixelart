"""Seed -> grid template for Gemini. 1x: 80x80 grid window -> 1024 px (pitch 12.8).
2x: the window nearest-upscaled 2x = 160x160 grid -> 1024 px (pitch 6.4), Gemini adds detail at 2x.
Background flat green (#00c000)."""
import sys
import numpy as np
from PIL import Image
from common import *
WIN = (26, 38, 106, 118)   # x0,y0,x1,y1 in the 128 cell (80x80)
BG = (0, 192, 0)
WINS = {"jump_E_apex": (26, 26, 106, 106)}
def win(name):
    import os
    if os.environ.get("S5_OLDWIN"): return WIN
    return WINS.get(name, WIN)
def make(name, mode="1x", grid=False):
    s = Image.open(f"{OUT}/seed/{name}.png").convert("RGBA").crop(win(name))
    bg = Image.new("RGBA", s.size, BG + (255,)); bg.alpha_composite(s)
    n = 80 if mode == "1x" else 160
    if mode == "2x": bg = bg.resize((160, 160), Image.NEAREST)
    big = bg.resize((1024, 1024), Image.NEAREST).convert("RGB")
    if grid:
        a = np.array(big)
        for i in range(n + 1):
            p = min(1023, int(round(i * 1024 / n)))
            a[:, p] = (a[:, p] * 0.8).astype(np.uint8); a[p, :] = (a[p, :] * 0.8).astype(np.uint8)
        big = Image.fromarray(a)
    return big
if __name__ == "__main__":
    mode = sys.argv[1]; names = sys.argv[2:] or NAMES
    for nm in names:
        make(nm, mode).save(f"{OUT}/seed/{nm}_tpl{mode}.png")
