"""r_tex_head.py (R, round 2) -- helper for the pixel step: paste the rig's projected master head.
The `tex` pass (render_motion.py, 8x, EEVEE 1 sample, no AA) shows the camera-projected m96 master pixels on the rig's own hull head +
side locks (exact palette colours; alpha = head-group faces visible from this view at rest). It deforms with the head / hair / bow / bun
bones, so head turns and hair swings carry the master look. Usage: g = tex_head(T, g) with T = the 128-cell crop of <stem>_fNN_tex.png
(float RGBA 0..1, 1024x1024, already shifted like the other passes) and g = the sprite char grid (hx palette keys)."""
import numpy as np
import sys
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx  # noqa: E402
P, N = 8, 128


def tex_head(T, g, cover=0.5):
    """each sprite cell whose 8x8 block is > cover tex-covered takes the block's majority tex colour, snapped to the palette"""
    al = T[..., 3] > 0.5; cov = hx.cells(al.astype(float)).mean((2, 3)) > cover
    rgb = np.round(T[..., :3] * 255).astype(int); key = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]; key[~al] = -1
    Kc = hx.cells(key).reshape(N, N, P * P); out = g.copy(); pal = np.array(hx.RGB, float)
    for y, x in zip(*np.nonzero(cov)):
        v = Kc[y, x][Kc[y, x] >= 0]; u, c = np.unique(v, return_counts=True); k = int(u[c.argmax()])
        col = np.array([k >> 16, (k >> 8) & 255, k & 255], float); out[y, x] = hx.KEYS[int(((pal - col) ** 2).sum(1).argmin())]
    return out
