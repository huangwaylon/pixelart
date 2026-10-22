"""HD face (portraits / cut-scene concept art): anime-style eyes, brows, mouth and blush drawn as crisp pixel shapes,
positioned from the 3D head (eye anchors on the head ellipsoid) so the face stays on-model in any pose or angle.
Spec: data/faces/<name>.json  {"palette": {...colour roles...}, "eye": {...}, "expressions": {name: {...}}}"""
import math

import numpy as np

from .mathutil import xform_point


def _eye_anchor(face, head_world, cam, pivot, sgn):
    yaw, pitch = math.radians(sgn * face["eye_yaw"]), math.radians(face["eye_pitch"])
    c, r = np.asarray(face["center"], float), np.asarray(face["radii"], float)
    d = np.array([math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch)])
    p = xform_point(head_world, c + r * d)
    n = np.linalg.inv(head_world[:3, :3]).T @ (d / r)
    n /= np.linalg.norm(n)
    return cam.project(p, pivot), float(np.dot(n, cam.to_cam))


def apply_face_hd(idx, palette, head_world, face, spec, expression, pivot, cam):
    ex = spec["expressions"].get(expression) or spec["expressions"]["neutral"]
    P = {k: palette.index[v] for k, v in spec["palette"].items()}
    iris = [palette.index[c] for c in spec["iris_ramp"]]
    skin_ids = set(palette.index[n] for n in palette.ramps["skin"])
    out = idx.copy()
    H, W = out.shape
    R = face["radii"][0] * cam.ppu                     # head radius in pixels
    E = spec["eye"]
    eyes = []
    for sgn in (1, -1):
        (sx, sy), facing = _eye_anchor(face, head_world, cam, pivot, sgn)
        if facing > 0.05:
            eyes.append((sx, sy, facing, sgn))
    if not eyes:
        return out
    skin_mask = np.isin(out, list(skin_ids))
    ys, xs = np.mgrid[0:H, 0:W]
    pxc, pyc = xs + 0.5, ys + 0.5

    def paint(mask, col):
        m = mask & skin_mask
        out[m] = col

    row = sum(e[1] for e in eyes) / len(eyes)          # eyes share one row (alignment rule)
    for sx, sy, facing, sgn in eyes:
        a = E["w"] * R * max(0.45, facing) * 0.5        # half width, foreshortened on the far side
        b = E["h"] * R * 0.5 * ex.get("open", 1.0)
        cx, cy = sx, row
        u, v = (pxc - cx) / max(a, 0.5), (pyc - cy) / max(b, 0.5)
        outward = 1 if sx > (eyes[0][0] + eyes[-1][0]) / 2 or len(eyes) == 1 and sgn > 0 else -1
        if ex.get("closed"):                            # ^ (happy) or ‿ (calm) closed-eye arc, 2px thick
            curve = -0.55 * (1 - u ** 2) if ex["closed"] == "happy" else 0.45 * (1 - u ** 2)
            m = (np.abs(u) <= 1.05) & (np.abs((pyc - cy) - curve * b) <= max(1.0, 0.18 * b))
            paint(m, P["lash"])
        else:
            sock = u ** 2 + v ** 2 <= 1.0
            paint(sock, P["white"])
            iu, iv = (pxc - cx) / (a * E["iris_w"]), (pyc - (cy + 0.08 * b)) / (b * E["iris_h"])
            ir = (iu ** 2 + iv ** 2 <= 1.0) & sock
            # iris gradient: dark top -> light bottom (3 bands)
            t = np.clip((iv + 1) / 2, 0, 1)
            for k, col in enumerate(iris):
                lo, hi = k / len(iris), (k + 1) / len(iris)
                paint(ir & (t >= lo) & (t < hi + (k == len(iris) - 1)), col)
            pu, pv = (pxc - cx) / (a * 0.32 * ex.get("pupil", 1.0)), (pyc - (cy + 0.15 * b)) / (b * 0.42 * ex.get("pupil", 1.0))
            paint((pu ** 2 + pv ** 2 <= 1.0) & sock, P["pupil"])
            # highlights fixed to screen top-left (light direction), not mirrored
            hu, hv = (pxc - (cx - 0.32 * a)) / (0.3 * a), (pyc - (cy - 0.38 * b)) / (0.26 * b)
            paint((hu ** 2 + hv ** 2 <= 1.0) & sock, P["shine"])
            h2u, h2v = (pxc - (cx + 0.3 * a)) / (0.14 * a + 0.4), (pyc - (cy + 0.45 * b)) / (0.12 * b + 0.4)
            paint((h2u ** 2 + h2v ** 2 <= 1.0) & sock, P["shine"])
            # upper lash: thick dark arc over the top edge, flicking outward at the outer corner
            top = (u ** 2 + v ** 2 <= 1.0 + E["lash_px"] / b * 2) & (v < -0.45) & ~((u ** 2 + v ** 2 <= 0.72) & (v > -0.8))
            flick = (np.abs((pyc - (cy - 0.7 * b)) + (pxc - cx - outward * a) * 0.6 * outward) <= 0.8) & \
                    ((pxc - cx) * outward > 0.7 * a) & ((pxc - cx) * outward < a + E["flick_px"])
            paint(top | flick, P["lash"])
            lower = (np.abs(u ** 2 + v ** 2 - 1.0) <= 0.18) & (v > 0.55) & ((pxc - cx) * outward > -0.1 * a)
            paint(lower, P["lash_light"])
        # brow: arc above the eye, angle per expression (+ = inner end lower -> angry, - = worried)
        by = cy - b - E["brow_gap"] * R + ex.get("brow_y", 0.0) * R
        tilt = ex.get("brow_tilt", 0.0) * (-outward)
        bu = (pxc - cx) / (a * 1.05)
        m = (np.abs(bu) <= 1.0) & (np.abs(pyc - (by + 0.18 * b * bu ** 2 * -1 + tilt * bu * b * 0.5)) <= 0.6)
        # anime convention: brows read through the bangs (drawn over hair as well as skin)
        hair_ids = [palette.index[c] for m_, r_ in palette.ramps.items() if m_.startswith("hair") for c in r_]
        mb = m & (skin_mask | np.isin(out, hair_ids))
        out[mb] = P["brow"]
        # blush: anime hatch lines under the outer half of the eye
        if ex.get("blush", 1):
            for k in range(int(ex.get("blush_lines", 3))):
                x0 = cx + outward * (0.1 * a + k * 0.32 * a)
                m = (np.abs((pxc - x0) + (pyc - (cy + b + 0.18 * R))) <= 0.6) & (np.abs(pyc - (cy + b + 0.18 * R)) <= 0.12 * R + 0.6)
                paint(m, P["blush"])
    # nose + mouth on the face centre line between the eyes
    mx = sum(e[0] for e in eyes) / len(eyes) + (0.12 * R if len(eyes) == 1 else 0.0)
    if len(eyes) == 2 and abs(eyes[0][2] - eyes[1][2]) > 0.2:
        far = min(eyes, key=lambda e: e[2])
        mx = mx * 0.65 + far[0] * 0.35
    ny = row + E["nose_y"] * R
    paint((np.abs(pxc - mx) <= 0.5) & (np.abs(pyc - ny) <= 0.5), P["nose"])
    my = row + E["mouth_y"] * R
    mw = E["mouth_w"] * R * ex.get("mouth_w", 1.0)
    shape = ex.get("mouth", "smile")
    mu = (pxc - mx) / max(mw * 0.5, 0.6)
    if shape in ("smile", "frown", "flat"):
        k = {"smile": 0.35, "frown": -0.35, "flat": 0.0}[shape]
        m = (np.abs(mu) <= 1.0) & (np.abs((pyc - my) - k * mw * 0.5 * (1 - mu ** 2)) <= 0.55)
        paint(m, P["mouth_line"])
    elif shape in ("open", "o", "grin"):
        hh = mw * (0.55 if shape == "open" else 0.45 if shape == "o" else 0.32)
        ww = mw * (0.5 if shape != "o" else 0.3)
        mv = (pyc - my) / max(hh * 0.5, 0.6)
        mu2 = (pxc - mx) / max(ww, 0.6)
        inside = mu2 ** 2 + mv ** 2 <= 1.0
        if shape == "open":
            inside &= mv > -0.35                         # flat top: a "D" laugh
        paint(inside, P["mouth_in"])
        paint(inside & (mv > 0.35), P["tongue"])
        edge = (np.abs(mu2 ** 2 + mv ** 2 - 1.0) <= 0.35) & ~inside | (inside & (mv <= -0.2) & (shape == "open"))
        paint(edge & ~inside, P["mouth_line"])
    return out
