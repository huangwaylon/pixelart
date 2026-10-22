"""Ground shadow + snow-puff FX. Direction independent; exported as separate strips for the engine."""
import math
import numpy as np

from .mathutil import translate, scale
from .render import render_pixels, add_outline, remove_lone_pixels, Camera


def shadow_frame(size, pivot, z_px, palette, z_max=20, ppu=1.0, spec=None):
    """Flat ellipse under the character: 14x5 px grounded -> 10x4 px at apex (AD spec)."""
    W, H = size
    k = min(max(z_px / z_max, 0), 1)
    if spec:   # explicit screen-px shadow (GD: width tied to body width, shrink to apex_scale at the top)
        sc = 1 - (1 - spec.get("apex_scale", 0.65)) * k
        w, h = spec["w"] * sc, max(spec["h"] * sc, 2)
    else:
        w = (14 - 4 * k) * ppu
        h = max((5 - 1 * k) * ppu, 2)
    ys, xs = np.mgrid[0:H, 0:W]
    cx, cy = pivot[0], pivot[1] + 0.5
    inside = ((xs + 0.5 - cx) / (w / 2)) ** 2 + ((ys + 0.5 - cy) / (h / 2)) ** 2 <= 1.0
    idx = np.full((H, W), -1, int)
    idx[inside] = palette.special["ground_shadow"]
    return idx


PUFFS = {
    # count, max spread (units), clump radius, lifetime ms, angle offset
    "takeoff": (6, 9.0, 2.0, 260, 30.0),
    "land":    (8, 13.0, 2.6, 320, 0.0),
}


def puff_prims(event, age_ms):
    n, spread, rad, life, a0 = PUFFS[event]
    if age_ms < 0 or age_ms >= life:
        return []
    u = age_ms / life
    prims = []
    for i in range(n):
        ang = math.radians(a0 + 360.0 * i / n)
        # alternate near/far clumps for a less mechanical ring (deterministic)
        dist = (4.0 + spread * (1 - math.exp(-age_ms / 70.0))) * (1.0 if i % 2 == 0 else 0.8)
        r = rad * (1.0 - u) ** 0.7 * (1.0 if i % 2 == 0 else 0.8)
        if r < 0.6:
            continue
        y = r * 0.7 + 3.0 * math.sin(math.pi * min(u * 1.4, 1.0))
        c = (math.sin(ang) * dist, y, math.cos(ang) * dist)
        prims.append({"name": f"puff_{event}_{i}", "M": translate(*c) @ scale(r * 1.2, r, r * 1.2),
                      "material": "snow", "group": f"puff{i}", "front": c[2] * 0.894 + c[1] * 0 > 0})
    return prims


def fx_frames(event_times, t_ms, size, pivot, palette, ppu=1.0):
    """Returns (back_idx, front_idx) for the snow puffs alive at time t_ms."""
    prims = []
    for ev, te in event_times:
        prims += puff_prims(ev, t_ms - te)
    W, H = size
    out = []
    for front in (False, True):
        sel = [p for p in prims if p["front"] == front]
        if not sel:
            out.append(np.full((H, W), -1, int))
            continue
        pix = render_pixels(sel, palette, size, pivot, cam=Camera(ppu=ppu), cast_shadows=False, inner_line_depth=1e9)
        idx = remove_lone_pixels(pix.idx)
        out.append(add_outline(idx, palette.index[palette.ramps["snow"][0]]))
    return out[0], out[1]
