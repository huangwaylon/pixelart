"""Deterministic pixel-art rules applied after rendering. Each rule encodes a recurring hand fix from the
per-pixel team reviews (docs/review/pixel/*), so the generator produces it instead of an override.

Rules (all on by default; character["render"]["rules"] can list a subset):
  grounded_soles     lowest pixel of each boot column is boot, never cuff (no "sock" feet)
  cuff_continuity    1-2px skin gaps inside the hat-cuff band become cuff
  backview_skin      when no eye is visible: head skin -> hair (no cheek slivers), neck skin -> shadow tone
  outline_notches    transparent 1px notches enclosed on 3 sides are filled with outline
  thin_highlights    1px-wide highlight-tone runs on coat/hat collapse into the base tone (flicker source)
"""
import numpy as np

def angel_ring(idx, pix, palette, hair_mat, depth=2):
    """天使の輪: a hair highlight arc parallel to the top contour of the hair mass (2-3 rows down),
    across the middle 60% of the hair width. Applied when the crown is visible (no full hat)."""
    out = idx.copy()
    ramp = _ramp_idx(palette, hair_mat)
    if len(ramp) < 3:
        return out
    hi = ramp[-1]
    hair_px = np.isin(out, ramp)
    cols = np.nonzero(hair_px.any(axis=0))[0]
    if len(cols) < 6:
        return out
    x0, x1 = cols.min(), cols.max()
    m0, m1 = int(x0 + 0.2 * (x1 - x0)), int(x1 - 0.3 * (x1 - x0))     # skew left: light from upper-left
    for x in range(m0, m1 + 1):
        ys = np.nonzero(hair_px[:, x])[0]
        if len(ys) < depth + 3:
            continue
        y = ys.min() + depth
        if hair_px[y, x]:
            out[y, x] = hi
    return out


ALL_RULES = ["grounded_soles", "cuff_continuity", "temple_cover", "backview_skin", "chin_shadow", "thin_highlights"]
POST_OUTLINE_RULES = ["outline_notches"]


def _ramp_idx(palette, mat):
    return [palette.index[c] for c in palette.ramps.get(mat, [])]


def apply_rules(idx, pix, palette, rules, face_visible):
    """Pre-outline rules. idx: palette-index image; pix: PixelFrame with material/group maps."""
    H, W = idx.shape
    out = idx.copy()
    mat = pix.material
    if "grounded_soles" in rules and "boots" in palette.ramps:
        boot = _ramp_idx(palette, "boots")
        cuff = set(_ramp_idx(palette, "boot_cuff"))
        for x in range(W):
            col = np.nonzero(out[:, x] >= 0)[0]
            if len(col) == 0:
                continue
            y = col[-1]
            if out[y, x] in cuff and mat[y, x] == "boot_cuff":
                out[y, x] = boot[0]
                if y - 1 >= 0 and out[y - 1, x] in cuff and y - 2 >= 0 and out[y - 2, x] in cuff:
                    out[y - 1, x] = boot[min(1, len(boot) - 1)]
    if "cuff_continuity" in rules and "hatcuff" in palette.ramps:
        cuff = set(_ramp_idx(palette, "hatcuff"))
        base = _ramp_idx(palette, "hatcuff")[-1]
        for y in range(H):
            row = out[y]
            x = 0
            while x < W:
                if mat[y, x] == "skin":
                    x1 = x
                    while x1 < W and mat[y, x1] == "skin":
                        x1 += 1
                    left_ok = x > 0 and (row[x - 1] in cuff)
                    right_ok = x1 < W and (row[x1] in cuff)
                    edge_l = x == 0 or row[x - 1] < 0 or mat[y, x - 1] is None
                    edge_r = x1 >= W or row[x1] < 0 or mat[y, x1] is None
                    n_cuff = int(np.isin(row, list(cuff)).sum())
                    # close gaps inside the band, and run the band out to the silhouette at its ends
                    if x1 - x <= 2 and ((left_ok and right_ok) or (n_cuff >= 3 and ((left_ok and edge_r) or (right_ok and edge_l)))):
                        out[y, x:x1] = base
                    x = x1
                else:
                    x += 1
    if "temple_cover" in rules and "hatcuff" in palette.ramps:
        # skin never shows above the hat cuff (temples beside the cuff read as a too-narrow hat)
        hair_mats = [m for m in set(mat[mat != None].tolist()) if str(m).startswith("hair")]  # noqa: E711
        hair = _ramp_idx(palette, hair_mats[0]) if hair_mats else None
        for x in range(W):
            rows = np.nonzero(mat[:, x] == "hatcuff")[0]
            if len(rows) and hair:
                for y in range(0, rows.max()):
                    if mat[y, x] == "skin":
                        out[y, x] = hair[1 if len(hair) > 1 else 0]
    if "chin_shadow" in rules and face_visible:
        # AD rule 7: the skin row directly above the scarf/collar is the shadow tone
        skin = _ramp_idx(palette, "skin")
        names = pix.group_names
        head_id = names.index("head") if "head" in names else -2
        for y in range(H - 1):
            for x in range(W):
                if mat[y, x] == "skin" and pix.group[y, x] == head_id and mat[y + 1, x] not in ("skin", None):
                    out[y, x] = skin[0]
    if "backview_skin" in rules and not face_visible:
        hair_mats = [m for m in set(mat[mat != None].tolist()) if str(m).startswith("hair")]  # noqa: E711
        hair = _ramp_idx(palette, hair_mats[0]) if hair_mats else None
        skin = _ramp_idx(palette, "skin")
        names = pix.group_names
        head_id = names.index("head") if "head" in names else -2
        for y in range(H):
            for x in range(W):
                if mat[y, x] != "skin":
                    continue
                below = mat[y + 1, x] if y + 1 < H else None
                nape = below is not None and below != "skin" and not str(below).startswith("hair")
                if nape:
                    out[y, x] = skin[0]          # AD rule 7: a 1-row skin_0 nape stays visible above the collar
                elif pix.group[y, x] == head_id and hair:
                    out[y, x] = hair[min(1, len(hair) - 1)]
                else:
                    out[y, x] = skin[0]
    if "thin_highlights" in rules:
        for m in ("coat", "hat"):
            r = _ramp_idx(palette, m)
            if len(r) < 3:
                continue
            hi, base = r[-1], r[1]
            for y in range(H):
                for x in range(W):
                    if out[y, x] != hi:
                        continue
                    horiz = (x > 0 and out[y, x - 1] == hi) or (x < W - 1 and out[y, x + 1] == hi)
                    vert = (y > 0 and out[y - 1, x] == hi) or (y < H - 1 and out[y + 1, x] == hi)
                    wide = horiz and vert
                    if not wide:
                        # part of a 1px-thin run: keep only if it has a 2x2 block somewhere next to it
                        blk = any(0 <= y + dy < H - 1 and 0 <= x + dx < W - 1 and
                                  (out[y + dy:y + dy + 2, x + dx:x + dx + 2] == hi).all()
                                  for dy in (-1, 0) for dx in (-1, 0))
                        if not blk:
                            out[y, x] = base
    return out


def apply_post_outline(idx, palette, rules, deliberate=None, part_mask=None):
    """part_mask (bool HxW): pixels that belong to the rig's boot/boot_cuff parts. Sole rules only ever
    touch these (sleeve cuffs share the cuff ramp, so colour alone is never enough)."""
    out = idx.copy()
    if "grounded_soles" in rules and "boots" in palette.ramps and "boot_cuff" in palette.ramps:
        # AD rule 6: the lowest non-outline pixel of every foot column is boot (lit/shadow), never cuff
        H, W = out.shape
        ol = palette.special["outline"]
        boot = _ramp_idx(palette, "boots")
        cuff_r = _ramp_idx(palette, "boot_cuff")
        rows = np.nonzero((out >= 0).any(axis=1))[0]
        top_y, floor_y = (rows.min(), rows.max()) if len(rows) else (0, H)
        low_y = top_y + 0.6 * (floor_y - top_y)          # feet live in the lower 40% of the sprite
        hits = []                                     # (y, x, was_lit)
        for x in range(W):
            ys = [y for y in range(H - 1, -1, -1) if out[y, x] >= 0 and out[y, x] != ol]
            if not ys:
                continue
            y = ys[0]
            if out[y, x] in cuff_r and y >= low_y and (part_mask is None or part_mask[y, x]):
                hits.append((y, x, out[y, x] == cuff_r[-1]))
        # one colour per contiguous sole run (a split lit/shadow pair would read as two specks)
        hits.sort()
        k = 0
        while k < len(hits):
            j = k
            while j + 1 < len(hits) and hits[j + 1][0] == hits[k][0] and hits[j + 1][1] == hits[j][1] + 1:
                j += 1
            run = hits[k:j + 1]
            col = boot[min(1, len(boot) - 1)] if any(h[2] for h in run) else boot[0]
            for y, x, _ in run:
                out[y, x] = col
                if deliberate is not None:
                    deliberate.add((y, x))
            k = j + 1
        # an isolated cuff pixel left directly above a sole joins the boot (no 1px cuff remnant)
        for y, x, _ in hits:
            yy = y - 1
            if yy >= 0 and out[yy, x] in cuff_r and (part_mask is None or part_mask[yy, x]):
                blk = out[max(yy - 1, 0):yy + 2, max(x - 1, 0):x + 2]
                if (blk == out[yy, x]).sum() == 1:
                    out[yy, x] = out[y, x]
                    if deliberate is not None:
                        deliberate.add((yy, x))
    if "outline_notches" in rules:
        H, W = out.shape
        ol = palette.special["outline"]
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if out[y, x] >= 0:
                    continue
                nb = [out[y - 1, x], out[y + 1, x], out[y, x - 1], out[y, x + 1]]
                if sum(v >= 0 for v in nb) >= 3:
                    out[y, x] = ol
    return out


def pom_cel(r_px, palette, mat="pom", lit=True):
    """Hand-style pom-pom part: a filled disc with a fixed top-left highlight and bottom-right shadow.
    Same integer radius -> identical cel every frame (no highlight blinking)."""
    ramp = _ramp_idx(palette, mat)
    lo, mid, hi = ramp[0], ramp[min(1, len(ramp) - 1)], ramp[-1]
    d = max(3, int(round(2 * r_px)))
    c = (d - 1) / 2.0
    cel = np.full((d, d), -1, int)
    for y in range(d):
        for x in range(d):
            dx, dy = x - c, y - c
            if dx * dx + dy * dy <= (d / 2.0) ** 2 - 0.25:
                t = (-dx - dy) / max(c, 1)          # +1 toward upper-left
                cel[y, x] = hi if t > 0.9 else (lo if t < -0.9 else mid)
    # AD rule 5: oat_1 body + exactly 3px top-left highlight when lit, no shadow tone
    cel[cel >= 0] = mid
    if lit:
        filled = [(y, x) for y in range(d) for x in range(d) if cel[y, x] >= 0]
        filled.sort(key=lambda t: (t[0] + t[1], t[0]))
        top = filled[0]
        # deterministic 3px L: inner-top-left pixel + its right and lower neighbour (inside the disc)
        oy, ox = top[0] + 1, top[1] + 1 if cel[top[0] + 1, top[1] + 1] >= 0 else top[1]
        for y, x in ((oy, ox), (oy, ox + 1), (oy + 1, ox)):
            if 0 <= y < d and 0 <= x < d and cel[y, x] >= 0:
                cel[y, x] = hi
    return cel
