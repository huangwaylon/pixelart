"""lock3 RIBBON lag stamps (pink scarf ribbons, rooted at the collar). Paths are relative to the root, drawn for a
ribbon on the viewer-LEFT side (dir=-1); dir=+1 mirrors x. Rendered by kit.ribbon (2 -> 3 -> 2 -> 1 px taper,
pink_1 over a pink_0 underside, 1 px dark root). Always drawn over=0 (behind the arm / body: never across the chest).
  neutral      hangs with one S-curve (out, back in, tip flicks out)
  trail_out    flung outward / back (lag when the body moves toward the other side, or fast travel)
  trail_in     swung in behind the body (lag when the body moves toward this side); the tip peeks below the cuff
  float        apex / hang time: lifted, S-curve opening upward
"""
PRESETS = {
    'neutral':   [(0, 0), (-3, 1), (-6, 3), (-8, 5), (-9, 8), (-8, 11), (-8, 14), (-10, 16), (-12, 17)],
    'trail_out': [(0, 0), (-4, 1), (-7, 2), (-10, 4), (-12, 6), (-14, 7), (-16, 8), (-18, 8), (-20, 7)],
    'trail_in':  [(0, 0), (-2, 2), (-4, 4), (-5, 7), (-5, 10), (-4, 13), (-4, 16), (-6, 18), (-7, 19)],
    'float':     [(0, 0), (-4, 0), (-7, -1), (-10, 0), (-12, 1), (-14, 0), (-16, -2), (-17, -3), (-18, -3)],
    'swing_mid': [(0, 0), (-3, 1), (-6, 3), (-9, 5), (-11, 7), (-12, 10), (-14, 12), (-16, 13), (-17, 13)],
}


def path(root, preset='neutral', d=-1, sx=1.0, sy=1.0, blend=None):
    """root (x,y); preset name or list; d = -1 viewer-left side, +1 right. blend=(other, t) mixes two presets."""
    P = PRESETS[preset] if isinstance(preset, str) else preset
    if blend:
        Q = PRESETS[blend[0]] if isinstance(blend[0], str) else blend[0]; t = blend[1]
        P = [(a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t) for a, b in zip(P, Q)]
    x0, y0 = root
    return [(round(x0 - d * x * sx), round(y0 + y * sy)) for x, y in P]


def spec(root, preset='neutral', d=-1, **kw):
    pts = path(root, preset, d, **kw)
    return f"@ribbon {' '.join(f'{x},{y}' for x, y in pts)} side={d} over=0"
