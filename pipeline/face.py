"""Face decals: hand-designed pixel patterns anchored to 3D points on the head.
Keeps eyes crisp (never resampled by rotation) yet placed consistently in every facing."""
import math
import numpy as np

from .mathutil import xform_point

# E = eye, C = catchlight, M = mouth, B = blush. Patterns are listed top row first.
# "large" = GBA/DS-style 2x3 eye with a top-left catchlight (light is upper-left in every facing).
EYES_BY_STYLE = {
    "large": {
        "neutral":    {"L": ["CE", "EE", "EE"], "R": ["CE", "EE", "EE"]},
        "determined": {"L": ["EE", "EE"], "R": ["EE", "EE"]},
        "joyful":     {"L": [".E.", "E.E"], "R": [".E.", "E.E"]},
        "squint":     {"L": ["E.", ".E", "E."], "R": [".E", "E.", ".E"]},
        "smile":      {"L": ["CE", "EE", "EE"], "R": ["CE", "EE", "EE"]},
    },
    # kawaii (Japanese research rule 9): 2x3 iris + 1px upper lash cap extending outward, catchlight top-left
    "kawaii": {
        "neutral":    {"L": ["EEE", ".CE", ".EE"], "R": ["EEE", "CE.", "EE."]},
        "smile":      {"L": ["EEE", ".CE", ".EE"], "R": ["EEE", "CE.", "EE."]},
        "determined": {"L": ["EEE", ".EE"], "R": ["EEE", "EE."]},
        "joyful":     {"L": [".E.", "E.E"], "R": [".E.", "E.E"]},
        "squint":     {"L": ["E.", ".E", "E."], "R": [".E", "E.", ".E"]},
    },
    "small": {
        "neutral":    {"L": ["E", "E"], "R": ["E", "E"]},
        "determined": {"L": ["E"], "R": ["E"]},
        "joyful":     {"L": [".E.", "E.E"], "R": [".E.", "E.E"]},
        # screen-left eye shows '>' and screen-right eye '<' so the squint reads as >< in every facing
        "squint":     {"L": ["E.", ".E", "E."], "R": [".E", "E.", ".E"]},
        "smile":      {"L": ["E", "E"], "R": ["E", "E"]},
    },
}
EYES = EYES_BY_STYLE["small"]
# 3/4 far eye for the kawaii face model: 2px wide, no outward lash (foreshortened), catchlight dropped
FAR_EYES = {"neutral": ["EE", "EE", "EE"], "smile": ["EE", "EE", "EE"], "determined": ["EE", "EE"],
            "joyful": ["EE"], "squint": ["E", "E"]}
# v2 profile eyes (one eye visible): drawn 1px behind the face front so a nose column remains.
# Patterns are written facing RIGHT and mirrored for left-facing views.
PROFILE_EYES = {   # AD locked rule 2: 1x2 eye column, catchlight on the BACK side (left when facing right)
    "neutral": ["CE", ".E"], "smile": ["CE", ".E"], "determined": [".E", ".E"],
    "joyful": ["E.", ".E"], "squint": ["E.", ".E", "E."],
}
MOUTHS = {
    "neutral": None,
    "determined": ["MM"],
    "joyful": ["MM", "MM"],
    "squint": ["M"],
    "smile": ["M"],
}
BLUSH = {"neutral": True, "determined": False, "joyful": True, "squint": True, "smile": True}


def _surface_point(face, yaw, pitch):
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    d = np.array([sy * cp, sp, cy * cp])
    c = np.asarray(face["center"], float)
    r = np.asarray(face["radii"], float)
    return c + r * d, d / r  # point, (unnormalised) ellipsoid normal direction


def _stamp(idx, mask_skin, pattern, cx, cy, colors, extra=None):
    h, w = len(pattern), len(pattern[0])
    x0 = int(math.floor(cx - w / 2 + 0.5))
    y0 = int(math.floor(cy - h / 2 + 0.5))
    H, W = idx.shape
    for j, row in enumerate(pattern):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = x0 + i, y0 + j
            if 0 <= x < W and 0 <= y < H and mask_skin[y, x]:
                idx[y, x] = colors[ch]
    return x0, y0, w, h


def apply_face(frame_idx, pix, head_world, face, expression, palette, pivot, cam, v2=False, info=None):
    """Stamp eyes / mouth / blush on skin pixels where the 3D anchor faces the camera and is unoccluded.
    v2: profile eye search + profile patterns, mouth locked 2 rows under the eyes. `info` (dict) receives
    {"eyes": n_visible}."""
    idx = frame_idx.copy()
    skin = pix.material == "skin"
    if v2:
        # trust final colours, not the render-time material map (cleanup passes may recolour pixels)
        skin = np.isin(idx, [palette.index[c] for c in palette.ramps["skin"]])
    colors = {"E": palette.special["eye"], "M": palette.special["mouth"], "B": palette.special["blush"],
              "C": palette.special.get("catchlight", palette.special["eye"])}
    vis_min = 0.04 if v2 else face.get("visibility_min", 0.2)   # v2: near-profile eyes still count

    def anchor(yaw, pitch):
        p, n = _surface_point(face, yaw, pitch)
        pw = xform_point(head_world, p)
        nw = np.linalg.inv(head_world[:3, :3]).T @ n
        nw /= np.linalg.norm(nw)
        sx, sy = cam.project(pw, pivot)
        depth = cam.depth(pw)
        facing = float(np.dot(nw, cam.to_cam))
        H, W = idx.shape
        xi, yi = int(math.floor(sx)), int(math.floor(sy))
        inside = 0 <= xi < W and 0 <= yi < H
        if v2 and inside and facing > vis_min and not skin[yi, xi]:
            # anchor landed on hair/outline at the face edge: walk toward the head centre to find skin
            hcx = cam.project(xform_point(head_world, face["center"]), pivot)[0]
            step = 1 if hcx > sx else -1
            for _ in range(3):
                xi += step
                if 0 <= xi < W and skin[yi, xi]:
                    sx = xi + 0.5
                    break
        inside = 0 <= xi < W and 0 <= yi < H
        # grazing angles: the pixel's ray hits the curving surface in front of the anchor; widen tolerance
        tol = 1.5 + (4.0 * (1.0 - facing) if v2 else 0.0)
        visible = facing > vis_min and inside and skin[yi, xi] and depth <= pix.depth[yi, xi] + tol
        return sx, sy, visible, facing

    eyes = []
    facings = []
    for side, sgn in (("L", 1), ("R", -1)):
        sx, sy, vis, fc = anchor(sgn * face["eye_yaw"], face["eye_pitch"])
        eyes.append((sx, sy, vis))
        facings.append((sx, fc))
    visible = [e for e in eyes if e[2]]
    far_x = None
    if v2 and len(visible) == 2 and abs(facings[0][1] - facings[1][1]) > 0.2:
        far_x = min(facings, key=lambda t: t[1])[0]     # AD rule 1: far eye gets no catchlight
    if info is not None:
        info["eyes"] = len(visible)
    if not visible:
        return idx
    if v2 and len(visible) == 1:
        cuffm = pix.material == "hatcuff"

        def cuff_rows(x):
            xs = [xx for xx in range(x - 2, x + 3) if 0 <= xx < cuffm.shape[1]]
            ys = [int(np.nonzero(cuffm[:, xx])[0].max()) for xx in xs if cuffm[:, xx].any()]
            return max(ys) if ys else None
        return _profile_eye(idx, skin, visible[0], head_world, face, expression, colors, pivot, cam, cuff_rows)
    visible.sort(key=lambda e: e[0])
    if v2 and len(visible) == 2:
        # eyes share one pixel row (a 1px offset reads as a crooked face) unless the head is deliberately rolled
        ey = head_world[:3, 1] / np.linalg.norm(head_world[:3, 1])
        a = cam.project(np.zeros(3), (0, 0)); b = cam.project(ey, (0, 0))
        # screen-space roll = how far the head's up-axis leans from vertical (independent of facing yaw)
        roll = abs(math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1]) + 1e-9)))
        if roll < 12.0:
            row = math.floor((visible[0][1] + visible[1][1]) / 2.0) + 0.5
            visible = [(visible[0][0], row, visible[0][2]), (visible[1][0], row, visible[1][2])]
    style = EYES_BY_STYLE[face.get("eyes", "small")]
    if expression not in style:
        expression = "neutral"           # HD-only expressions (sad, surprised, ...) fall back for sprite faces
    pats = style[expression]
    eye_boxes = []
    for k, (sx, sy, _) in enumerate(visible):
        # screen-left eye uses the "L" pattern unless only one eye is visible
        key = "L" if (k == 0 and len(visible) == 2) else ("R" if len(visible) == 2 else
                                                           ("L" if sx > idx.shape[1] / 2 else "R"))
        pat = pats[key]
        is_far = far_x is not None and abs(sx - far_x) < 1e-6
        if is_far:
            pat = [row.replace("C", "E") for row in pat]
            if v2 and face.get("eyes") == "kawaii":
                # 3/4 far eye (face model): narrower, no outward lash, same row as the near eye
                pat = FAR_EYES.get(expression, pat)
            if v2:
                # keep >= 1 skin pixel between the far eye and the face edge (hair/outline) on its outer side
                outer_dir = -1 if k == 0 else 1
                wpat = len(pat[0])
                for _ in range(3):
                    x0_ = int(math.floor(sx - wpat / 2 + 0.5))
                    edge_x = x0_ - 1 if outer_dir < 0 else x0_ + wpat
                    rows_ = range(int(math.floor(sy - 0.5)), int(math.floor(sy - 0.5)) + len(pat))
                    ok = all(0 <= edge_x < idx.shape[1] and 0 <= yy < idx.shape[0] and skin[yy, edge_x] for yy in rows_)
                    if ok:
                        break
                    sx -= outer_dir          # nudge toward the face centre
        top = sy - 0.5  # anchor marks the upper eye pixel for 2-tall eyes
        mask = skin
        if v2 and is_far:
            # AD: far eye never doubles the cheek outline -> no pixel 4-adjacent to the outer outline
            ol = colors["E"]
            H_, W_ = idx.shape
            outer = np.zeros_like(skin)
            for yy in range(H_):
                for xx in range(W_):
                    if idx[yy, xx] == ol and any(0 <= yy + a < H_ and 0 <= xx + b < W_ and idx[yy + a, xx + b] < 0
                                                 for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        outer[yy, xx] = True
            near_outer = np.zeros_like(skin)
            near_outer[1:, :] |= outer[:-1, :]; near_outer[:-1, :] |= outer[1:, :]
            near_outer[:, 1:] |= outer[:, :-1]; near_outer[:, :-1] |= outer[:, 1:]
            mask = skin & ~near_outer
        x0, y0, w, h = _stamp(idx, mask, pat, sx, top + len(pat) / 2, colors)
        eye_boxes.append((x0, y0, w, h))
        if BLUSH[expression] and not (v2 and is_far):
            outward = -1 if (k == 0 and len(visible) == 2) else 1
            if len(visible) == 1:
                outward = 0
            # blush sits under the eye's outer column, mirrored for the two eyes
            bx = x0 if outward < 0 else (x0 + w - 1 if outward > 0 else x0 + w // 2)
            by = y0 + h + 1
            bxs = [bx]
            if face.get("eyes") == "kawaii" and outward != 0:
                # 2px blush directly under the eye's outer half
                bxs = [x0, x0 + 1] if outward < 0 else [x0 + w - 2, x0 + w - 1]
                by = y0 + h
            for bx_ in bxs:
                if 0 <= by < idx.shape[0] and 0 <= bx_ < idx.shape[1] and skin[by, bx_] and idx[by, bx_] not in (colors["E"], colors["C"]):
                    idx[by, bx_] = colors["B"]
    mouth = MOUTHS[expression]
    if mouth:
        mx, my, mvis, _ = anchor(0.0, face["mouth_pitch"])
        if v2 and len(visible) == 2 and eye_boxes:
            # lock the mouth 2 rows under the eyes, centred between them (never on the scarf)
            bottom = max(b[1] + b[3] for b in eye_boxes)
            mx = (eye_boxes[0][0] + eye_boxes[1][0] + eye_boxes[1][2]) / 2.0
            my = bottom + len(mouth) / 2.0        # first row under the eyes, centred between them
            mvis = True
        if mvis and v2:
            # AD rule 3: the mouth touches only skin (no eye, scarf or outline). Try the first row under the
            # eyes, then one row lower (as hand-fixed in v1.1), otherwise omit it.
            h_, w_ = len(mouth), len(mouth[0])
            H, W = idx.shape

            def clear(mx_, my_):
                x0 = int(math.floor(mx_ - w_ / 2 + 0.5)); y0 = int(math.floor(my_ - h_ / 2 + 0.5))
                ring = [(x, y) for y in range(y0 - 1, y0 + h_ + 1) for x in range(x0 - 1, x0 + w_ + 1)
                        if not (y0 <= y < y0 + h_ and x0 <= x < x0 + w_)]
                inside = [(x, y) for y in range(y0, y0 + h_) for x in range(x0, x0 + w_)]
                return all(0 <= x < W and 0 <= y < H and skin[y, x] and idx[y, x] not in (colors["E"], colors["C"])
                           for x, y in ring + inside)
            mvis = False
            two_row = h_ >= 2

            def contacts(mx_, my_):
                x0 = int(math.floor(mx_ - w_ / 2 + 0.5)); y0 = int(math.floor(my_ - h_ / 2 + 0.5))
                inside = [(x, y) for y in range(y0, y0 + h_) for x in range(x0, x0 + w_)]
                if not all(0 <= x < W and 0 <= y < H and skin[y, x] and idx[y, x] not in (colors["E"], colors["C"])
                           for x, y in inside):
                    return None                                   # would be clipped -> never a partial mouth
                ring = [(x, y) for y in range(y0 - 1, y0 + h_ + 1) for x in range(x0 - 1, x0 + w_ + 1)
                        if (x, y) not in inside]
                return sum(1 for x, y in ring if not (0 <= x < W and 0 <= y < H and skin[y, x]
                                                       and idx[y, x] not in (colors["E"], colors["C"])))
            if len(visible) == 2 and eye_boxes:
                # AD round 3: preferred row = one clear row under the eyes (2-row mouths) / first row (1-row);
                # if that touches the chin row or scarf, move UP one row, never down. Pick the cleanest spot.
                rows = (1, 0) if two_row else (0,)
                best = None
                for pri, dy in enumerate(rows):
                    for dx in (0, -1, 1):
                        c = contacts(mx + dx, my + dy)
                        if c is not None and (best is None or (c, pri, abs(dx)) < best[0]):
                            best = ((c, pri, abs(dx)), dx, dy)
                if best is not None and (best[0][0] == 0 or two_row):
                    mx, my, mvis = mx + best[1], my + best[2], True
        if mvis:
            _stamp(idx, skin, mouth, mx, my, colors)
    return idx


def _profile_eye(idx, skin, eye, head_world, face, expression, colors, pivot, cam, cuff_rows=None):
    sx, sy, _ = eye
    hcx = cam.project(xform_point(head_world, face["center"]), pivot)[0]
    facing_right = sx > hcx
    pat = PROFILE_EYES[expression]
    if not facing_right:
        pat = [row[::-1] for row in pat]
    H, W = idx.shape
    yi = int(math.floor(sy))
    xi = int(math.floor(sx))
    front = 1 if facing_right else -1
    if cuff_rows is not None:
        # AD rule 2: eye top = cuff bottom + 2 in this column; keep >= 1 skin row below (clear of the jaw)
        cb = cuff_rows(xi)
        if cb is not None:
            yi = cb + 2
    while yi + len(pat) < H and not skin[min(yi + len(pat), H - 1), xi] and yi > 0:
        yi -= 1
    # AD round 2: eye column sits exactly 2px behind the front outline (1 nose pixel between)
    # the nose gap must hold on every eye row (the face front can slope): use the tightest row
    cols = []
    for yy in range(yi, min(yi + len(pat), H)):
        xs = xi
        while 0 <= xs + front < W and skin[yy, xs + front]:
            xs += front
        cols.append(xs + front - 2 * front)       # first non-skin pixel in front, minus 2
    eye_col = min(cols) if facing_right else max(cols)
    w_ = len(pat[0])
    # the eye column is the pattern's front-most 'E' column
    x0 = eye_col - (w_ - 1) if facing_right else eye_col
    for j, row in enumerate(pat):
        for i, ch in enumerate(row):
            x, y = x0 + i, yi + j
            if ch != "." and 0 <= x < W and 0 <= y < H and skin[y, x]:
                idx[y, x] = colors[ch]
    return idx


# ----------------------------------------------------------------------------------------------------------
# Face cels (v3): hand-designed faces per view class, pinned to the projected 3D eye line -> identical design in
# every frame/direction. File: data/faces/<name>.json
#   {"views": {"front": {"<expr>": {"rows": [...], "origin": [ox, oy]}}, "three_quarter": {...}, "profile": {...}}}
# rows are drawn for a head facing the viewer (front) or facing SCREEN-RIGHT (three_quarter/profile; mirrored for
# left-facing views). Chars: E eye/lash (outline colour), C catchlight, B blush, M mouth, S skin shadow,
# s skin base (to clear), '.' untouched. origin = cel pixel placed on the anchor (face centre on the eye line).
FACE_CLASSES = (("front", 22.5), ("three_quarter", 67.5), ("profile", 112.5))


def face_view(head_world, cam):
    """(class, facing_right) from the head's forward axis relative to the camera."""
    fwd = head_world[:3, 2] / np.linalg.norm(head_world[:3, 2])
    ang = math.degrees(math.atan2(float(np.dot(fwd, cam.right)), float(np.dot(fwd, cam.to_cam))))
    for name, lim in FACE_CLASSES:
        if abs(ang) <= lim:
            return name, ang > 0
    return "back", ang > 0


def apply_face_cels(idx, palette, head_world, face, cels, expression, pivot, cam):
    view, right = face_view(head_world, cam)
    if view == "back":
        return idx, view
    spec = cels["views"].get(view, {})
    cel = spec.get(expression) or spec.get("neutral")
    if not cel:
        return idx, view
    rows = cel["rows"] if (right or view == "front") else [r[::-1] for r in cel["rows"]]
    ox, oy = cel["origin"]
    if not (right or view == "front"):
        ox = len(cel["rows"][0]) - 1 - ox
    # anchor: front surface of the head on the eye line (centre of the face), projected
    pitch = math.radians(face.get("eye_pitch", -8))
    c = np.asarray(face["center"], float)
    r = np.asarray(face["radii"], float)
    p = c + r * np.array([0.0, math.sin(pitch), math.cos(pitch)])
    ax, ay = cam.project(xform_point(head_world, p), pivot)
    skin_ids = [palette.index[n] for n in palette.ramps["skin"]]
    if view == "profile":
        # pin the profile cel to the face's actual front edge on the eye row -> nose is always exactly 1px
        xi, yi = int(math.floor(ax)), int(math.floor(ay))
        step = 1 if right else -1
        H_, W_ = idx.shape
        if 0 <= yi < H_:
            x = min(max(xi, 0), W_ - 1)
            while 0 <= x - step < W_ and idx[yi, x] not in skin_ids:
                x -= step                     # walk back onto the face if the anchor fell outside
            while 0 <= x + step < W_ and idx[yi, x + step] in skin_ids:
                x += step                     # then forward to the last skin pixel (the nose tip)
            ax = x + 0.5
    x0, y0 = int(math.floor(ax)) - ox, int(math.floor(ay)) - oy
    colors = {"E": palette.special["eye"], "C": palette.special.get("catchlight", palette.special["eye"]),
              "B": palette.special["blush"], "M": palette.special["mouth"],
              "S": skin_ids[0], "s": skin_ids[min(1, len(skin_ids) - 1)]}
    out = idx.copy()
    H, W = out.shape
    stamped = set()
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = x0 + i, y0 + j
            if 0 <= x < W and 0 <= y < H and out[y, x] in skin_ids:      # only ever paint on visible skin
                out[y, x] = colors[ch]
                stamped.add((y, x))
    apply_face_cels.last_stamped = stamped        # designed pixels -> QA treats them as deliberate
    return out, view
