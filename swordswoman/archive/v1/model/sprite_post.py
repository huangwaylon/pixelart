"""Sprite post pass for the model preview cells (stand-in for the pixel pipeline), round 4.

  .venv/bin/python model/sprite_post.py <render_dir>

For every _masks/raw_*_64.png (+ its object-ID pass _masks/<name>_id.png):
  1. clean-up on the raw palette render (round 3, AD/TA):
     a. hair: deepest-recess outline specks -> hair[0]; angel ring (hair[2]) thinned to ONE
        continuous 1 px band, fragments < 3 px removed
     b. pink rim (pink[0]) drawn on the hair + bow silhouette edge facing the rim light (right
        contour + the right half of the top contour), 1 px, components < 3 px deleted
     c. stray violet: purple outside the arm ornament, and single red[0] specks on the sleeves
        -> neighbour colour
     d. corset: solid leather[1] band, 1 px leather[2] top line, <= 2 steel[1] buckle pixels;
        rivet / recess / buckle speckle dropped; pouch + belt flat leather[1]
     e. skirt hems: single-pixel teeth removed and single-pixel notches filled (no sawtooth)
     f. cloth orphans: a pixel whose 4 neighbours all share one other colour takes that colour
  2. closed 1 px exterior outline (selective: shadow side #1a1220, lit top/left side = darkest
     tone of the neighbouring ramp)
Writes <render_dir>/<name>, then checks.json for every cell (iso, pose, anim).
"""
import os, sys, json, glob
import numpy as np
from PIL import Image

D = sys.argv[1]
M = os.path.join(D, "_masks")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAL = json.load(open(os.path.join(ROOT, "docs", "palette.json")))
RP = PAL["ramps"]


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


OUTL = hx(PAL["outline"])
ALLC = {OUTL}
RAMP_OF = {}
for rn, cols in RP.items():
    for c in cols:
        ALLC.add(hx(c))
        RAMP_OF.setdefault(hx(c), rn)
LIT = {"skin": hx(RP["skin"][0]), "red": hx(RP["red"][1]), "steel": hx(RP["steel"][0]),
       "hair": hx(RP["hair"][0]), "pink": hx(RP["pink"][0])}
C = {k: [np.array(hx(c), np.uint8) for c in v] for k, v in RP.items()}
OUT_A = np.array(OUTL, np.uint8)
idinfo = json.load(open(os.path.join(M, "id_groups.json")))
GID = idinfo["groups"]


def eq(a, col):
    return np.all(a[..., :3] == np.asarray(col, np.uint8), axis=-1)


def shift(m, dy, dx, fill=False):
    """m shifted so that out[y, x] = m[y + dy, x + dx]."""
    H, W = m.shape[:2]
    out = np.full_like(m, fill)
    ys0, ys1 = max(0, -dy), min(H, H - dy)
    xs0, xs1 = max(0, -dx), min(W, W - dx)
    out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def components(mask):
    """4/8-connected components (8-connectivity) -> label array, sizes."""
    H, W = mask.shape
    lab = np.zeros((H, W), int)
    sizes = [0]
    n = 0
    for y in range(H):
        for x in range(W):
            if mask[y, x] and lab[y, x] == 0:
                n += 1
                st = [(y, x)]
                lab[y, x] = n
                cnt = 0
                while st:
                    cy, cx = st.pop()
                    cnt += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = cy + dy, cx + dx
                            if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and lab[yy, xx] == 0:
                                lab[yy, xx] = n
                                st.append((yy, xx))
                sizes.append(cnt)
    return lab, np.array(sizes)


def drop_small(mask, minsize=3):
    lab, sz = components(mask)
    return mask & (sz[lab] >= minsize)


def neighbour_mode(a, ys, xs, exclude):
    """Most common 8-neighbour colour (opaque, not in `exclude`) for each pixel."""
    H, W = a.shape[:2]
    res = []
    for y, x in zip(ys, xs):
        cnt = {}
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if (dy or dx) and 0 <= yy < H and 0 <= xx < W and a[yy, xx, 3] == 255:
                    c = tuple(a[yy, xx, :3])
                    if c not in exclude:
                        cnt[c] = cnt.get(c, 0) + 1
        res.append(max(cnt, key=cnt.get) if cnt else None)
    return res


def load_id(name):
    p = os.path.join(M, name[:-4] + "_id.png")
    if not os.path.exists(p):
        return None
    a = np.array(Image.open(p).convert("RGBA"))
    ids = np.rint(a[..., 0] / 10.0).astype(int)
    ids[a[..., 3] < 128] = 0
    return ids


import re
DIR_RE = re.compile(r"_(SE|SW|NE|NW|S|E|N|W)(?:_f\d+)?_64\.png$")


def cell_dir(name):
    m = DIR_RE.search(name)
    return m.group(1) if m else None


def put(a, y, x, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = np.append(np.asarray(col, np.uint8), 255)


EYE_NEAR, EYE_FAR, EYE_PROFILE = (3, 5), (2, 5), (2, 4)     # (w, h) round 7 (r5-r6: 3x4 / 2x3 / 2x3)
# round 9 (AD 'SW iris runs one row below the eye box'): the 3/4 eyes are clamped to a 4-row box
# (lash row, eye[0] row with the steel[2] glint, 2 eye[1] rows); both bottoms on the same row
EYE_NEAR_34, EYE_FAR_34 = (3, 4), (2, 4)


def stamp_eyes(a, ids, d, stats):
    """Round 5 (AD 'sprite eyes'): hand-pixel eye templates on the rendered eye positions.
    Near eye 3 wide x 4 tall: 1 px ink lash row, eye[0] upper half (+ 1 steel[2] glint on the
    key-light side), eye[1] lower half.  Far eye (SE/SW) and profile eye (E/W) 2 x 3.
    Only face pixels are overwritten (lash row may also cover a bang tip)."""
    stats["eye_px"] = 0
    if d in (None, "N", "NE", "NW"):
        return a
    op = a[..., 3] == 255
    face = (ids == GID["face"]) & op
    hairm = ((ids == GID["hair"]) | (ids == GID["sheen"])) & op
    blue = face & (eq(a, C["eye"][0]) | eq(a, C["eye"][1]))
    lab, sz = components(blue)
    comps = []
    for k in range(1, len(sz)):
        ys, xs = np.where(lab == k)
        comps.append((len(ys), ys.mean(), xs.mean()))
    if not comps:
        return a
    comps.sort(key=lambda c: -c[0])
    # merge blobs that belong to the same eye (glint/pupil split)
    eyes = []
    for n, cy, cx in comps:
        for e in eyes:
            if abs(e[2] - cx) <= 2.0 and abs(e[1] - cy) <= 2.5:
                e[0] += n
                break
        else:
            eyes.append([n, cy, cx])
    eyes = sorted(eyes, key=lambda e: -e[0])[:2]
    # round 7 (AD must-fix 'face at the game camera'): eyes 5 px tall (bible: 4-5 px with lash,
    # 2 iris tones and a glint).  Near eyes 3 x 5, far eye (SE / SW) 2 x 5, profile eye 2 x 4.
    if d == "S":
        sizes = [EYE_NEAR] * len(eyes)
    elif d in ("SE", "SW"):
        sizes = [EYE_NEAR_34, EYE_FAR_34][:len(eyes)]
    else:   # E / W profile: one eye
        eyes = eyes[:1]
        sizes = [EYE_PROFILE]
    # left-to-right, keep >= 1 px skin between the two eyes
    order = sorted(range(len(eyes)), key=lambda i: eyes[i][2])
    boxes = []
    for i in order:
        n, cy, cx = eyes[i]
        w, h = sizes[i]
        x0 = int(round(cx - (w - 1) / 2.0))
        y0 = int(round(cy)) - (h - 3 if h >= 5 else h - 2)    # lash row; blue rows below it
        # round 7: the bottom (eye[1]) row must land on face skin -- lift the box (the lash may
        # cover a bang tip) by up to 2 px when the collar / chin edge is right below
        for _ in range(2):
            yb = y0 + h - 1
            row = [0 <= yb < a.shape[0] and 0 <= x0 + c < a.shape[1] and face[yb, x0 + c] for c in range(w)]
            if sum(row) * 2 >= w:
                break
            y0 -= 1
        if boxes and x0 <= boxes[-1][0] + boxes[-1][2]:
            x0 = boxes[-1][0] + boxes[-1][2] + 1
        if d in ("E", "W"):
            # round 6 (AD/GD 'E/W facing tell'): keep >= 1 px of face/hair in FRONT of the
            # profile eye (E faces screen-right, W screen-left), so the eye is never the last
            # pixel of the head: shift the box back up to 2 px if needed
            fwd = 1 if d == "E" else -1
            for _ in range(2):
                fx = x0 + w if fwd > 0 else x0 - 1
                okc = [0 <= y0 + r < a.shape[0] and 0 <= fx < a.shape[1] and (face[y0 + r, fx] or hairm[y0 + r, fx])
                       for r in range(1, h)]
                if all(okc):
                    break
                x0 -= fwd
        boxes.append((x0, y0, w, h))
    if d in ("SE", "SW") and len(boxes) == 2:
        # round 7: the far eye's blob centre sits 2-3 px higher than the near one (head turn +
        # chin-up); the pair is levelled to within 1 px so the face does not read as tilted
        ni = max(range(2), key=lambda i: boxes[i][2])
        fi = 1 - ni
        # round 9: levelled exactly to the HIGHER of the two lash rows, so neither iris hangs
        # below the other (SW: the near iris ran a row low onto the collar edge)
        ytop = boxes[ni][1] - (1 if boxes[fi][1] < boxes[ni][1] else 0)
        boxes = [(b[0], ytop, b[2], b[3]) for b in boxes]
        # the far eye sits on the face edge (3D decal wraps round the cheek): slide it toward
        # the near eye (>= 1 px skin between them) until its iris rows lie fully on the face
        x0, y0, w, h = boxes[fi]
        nx0, _, nw, _ = boxes[ni]
        step = 1 if nx0 > x0 else -1

        def fits(xx):
            return all(0 <= y0 + r < a.shape[0] and 0 <= xx + c < a.shape[1] and face[y0 + r, xx + c]
                       for r in range(1, h) for c in range(w))
        xx = x0
        for _ in range(3):
            if fits(xx):
                break
            nxt = xx + step
            if (step > 0 and nxt + w > nx0 - 1) or (step < 0 and nxt < nx0 + nw + 1):
                break
            xx = nxt
        boxes[fi] = (xx, y0, w, h)
    cnt = 0
    for (x0, y0, w, h) in boxes:
        for r in range(h):
            for c in range(w):
                y, x = y0 + r, x0 + c
                if not (0 <= y < a.shape[0] and 0 <= x < a.shape[1]):
                    continue
                # eyes win over single bang-tip pixels (Gemini r5: hair splitting the iris)
                if not (face[y, x] or hairm[y, x]):
                    continue
                if r == 0:
                    col = OUTL
                elif h >= 4:
                    # lash / eye[0] upper half / eye[1] lower half (+ glint top-left, key light)
                    col = C["eye"][0] if r <= (h - 1) // 2 else C["eye"][1]
                    if r == 1 and c == 0 and (w >= 3 or h >= 5):
                        col = C["steel"][2]
                else:
                    col = C["eye"][0] if r == 1 else C["eye"][1]
                put(a, y, x, col)
                cnt += 1
    stats["eye_px"] = cnt
    stats["eye_boxes"] = [list(b) for b in boxes]
    # round 9 (AD/GD 'eye pixels run down'): 3D eye / lash / glint / blush remnants touching a
    # stamped box from the side or below (rows under the lash row) become face skin[1], so each
    # eye is exactly its box
    inbox = np.zeros(face.shape, bool)
    for (x0, y0, w, h) in boxes:
        inbox[max(0, y0):y0 + h, max(0, x0):x0 + w] = True
    ring = np.zeros(face.shape, bool)
    for (x0, y0, w, h) in boxes:
        ring[max(0, y0 + 1):y0 + h + 2, max(0, x0 - 1):x0 + w + 1] = True
    ink = eq(a, OUTL) | eq(a, C["eye"][0]) | eq(a, C["eye"][1]) | eq(a, C["steel"][2])
    # anywhere on the face: eye / lash / glint remnants outside the boxes; next to a box: blush too
    tidy = face & ~inbox & (ink | (ring & eq(a, C["pink"][0])))
    a[tidy] = np.append(C["skin"][1], 255)
    stats["eye_tidy_px"] = int(tidy.sum())
    if d in ("E", "W") and boxes:
        # profile cheek/nose: the face pixels in front of the eye become skin[1] (not a bang
        # tip), and a 1 px skin nose bump is added just below the eye on the face edge
        x0, y0, w, h = boxes[0]
        fwd = 1 if d == "E" else -1
        fx = x0 + w if fwd > 0 else x0 - 1
        nose = 0
        for r in range(2, h + 2):
            y = y0 + r
            if 0 <= y < a.shape[0] and 0 <= fx < a.shape[1] and (face[y, fx] or (hairm[y, fx] and r >= h - 1)):
                put(a, y, fx, C["skin"][1])
                nose += 1
        y = y0 + h
        bx = fx + fwd
        while 0 <= bx < a.shape[1] and a[y, bx, 3] == 255 and (face[y, bx] or hairm[y, bx]):
            bx += fwd
        if 0 <= bx < a.shape[1] and a[y, bx, 3] == 0 and abs(bx - fx) <= 2:
            put(a, y, bx, C["skin"][1])
            nose += 1
        stats["profile_skin_px"] = nose
    return a


def bun_pass(a, ids, stats):
    """Round 5 (AD/GD 'snowman'): the bun is a second circle: hair[1] base, hair[0] on its
    lower-right (shadow) half, one short hair[2] sheen arc on the upper-left (<= 3 px), and a
    1 px outline crease wherever it touches the skull hair."""
    op = a[..., 3] == 255
    bun = (ids == GID["bun"]) & op
    hair = ((ids == GID["hair"]) | (ids == GID["sheen"])) & op
    stats["bun_px"] = int(bun.sum())
    if bun.sum() < 4:
        return a
    ys, xs = np.where(bun)
    cy, cx = ys.mean(), xs.mean()
    r = max(1.5, np.sqrt(bun.sum() / np.pi))
    for y, x in zip(ys, xs):
        if eq(a[y:y + 1, x:x + 1], C["pink"][0])[0, 0]:
            continue
        dd = ((x - cx) + (y - cy)) / (r * 1.414)
        put(a, y, x, C["hair"][0] if dd > 0.12 else C["hair"][1])
    # sheen arc upper-left
    ang = np.degrees(np.arctan2(ys - cy, xs - cx))
    rad = np.hypot(ys - cy, xs - cx) / r
    cand = [(abs(an + 125), y, x) for an, rr, y, x in zip(ang, rad, ys, xs) if -165 < an < -85 and 0.35 < rr < 0.85]
    cand.sort()
    for _, y, x in cand[:3]:
        put(a, y, x, C["hair"][2])
    stats["bun_sheen_px"] = min(3, len(cand))
    # crease: bun pixels 4-adjacent to skull hair pixels
    nb = shift(hair, 0, 1) | shift(hair, 0, -1) | shift(hair, 1, 0) | shift(hair, -1, 0)
    crease = bun & nb
    a[crease] = np.append(OUT_A, 255)
    stats["bun_crease_px"] = int(crease.sum())
    return a


def ear_pass(a, ids, stats):
    """Round 5: the ear is skin[1] with a 1 px skin[0] inner line where it meets the face /
    hair, so the pulled-up side reads as an ear, not a bare patch."""
    stats["ear_px"] = 0
    if "ear" not in GID:
        return a
    op = a[..., 3] == 255
    ear = (ids == GID["ear"]) & op
    if not ear.any():
        return a
    other = op & ~ear & ((ids == GID["face"]) | (ids == GID["hair"]))
    edge = ear & (shift(other, 0, 1) | shift(other, 0, -1) | shift(other, 1, 0) | shift(other, -1, 0))
    a[ear] = np.append(C["skin"][1], 255)
    if edge.sum() < ear.sum():
        a[edge] = np.append(C["skin"][0], 255)
    stats["ear_px"] = int(ear.sum())
    return a


def leg_split(a, ids, stats):
    """Round 5 (AD 'SW legs merge'): 1 px outline where the far leg touches the near leg
    (near leg = the one whose lowest pixel is lower on screen)."""
    stats["leg_split_px"] = 0
    if "leg_L" not in GID:
        return a
    op = a[..., 3] == 255
    L = (ids == GID["leg_L"]) & op
    R = (ids == GID["leg_R"]) & op
    if not L.any() or not R.any():
        return a
    near, far = (L, R) if np.where(L)[0].max() >= np.where(R)[0].max() else (R, L)
    touch = far & (shift(near, 0, 1) | shift(near, 0, -1))
    a[touch] = np.append(OUT_A, 255)
    stats["leg_split_px"] = int(touch.sum())
    return a


BLADE_MASKS = {}


CLUSTER_GROUPS = ("skirt", "skirt_under", "sleeve", "torso", "collar", "ornament", "scarf", "bow", "shorts")


N4 = ((0, 1), (0, -1), (1, 0), (-1, 0))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
RED_GROUPS = ("skirt", "skirt_under", "sleeve", "torso", "collar", "ornament", "bow")


def region_labels(ids, key, valid, conn=N4):
    """Connected regions of pixels sharing BOTH the object-ID group and the colour (numpy
    min-label propagation).  Returns (label array, sizes per label)."""
    H, W = valid.shape
    big = H * W + 1
    lab = np.where(valid, np.arange(H * W).reshape(H, W), big)
    links = []
    for dy, dx in conn:
        links.append((dy, dx, valid & shift(valid, dy, dx) & (shift(ids, dy, dx, -1) == ids)
                      & (shift(key, dy, dx, -1) == key)))
    for _ in range(H * W):
        new = lab
        for dy, dx, ok in links:
            new = np.where(ok, np.minimum(new, shift(lab, dy, dx, big)), new)
        if np.array_equal(new, lab):
            break
        lab = new
    sizes = np.bincount(np.where(valid, lab, 0).ravel(), minlength=H * W + 2)
    return lab, sizes


def staircase(mask, region):
    """Make a 1 px line 4-connected: where two line pixels touch only diagonally, add one of
    the two bridge pixels (the one inside `region`), so the line never leaves lone pixels."""
    m = mask.copy()
    for dy, dx in ((1, 1), (1, -1)):
        diag = m & shift(m, dy, dx)
        b1 = shift(diag, -dy, 0)            # p + (dy, 0)
        b2 = shift(diag, 0, -dx)            # p + (0, dx)
        con = (b1 & m) | (b2 & m)
        need = diag & ~(shift(m, dy, 0) | shift(m, 0, dx))
        nb1 = shift(need, -dy, 0) & region
        m |= nb1
        rest = need & ~shift(nb1, dy, 0)
        m |= shift(rest, 0, -dx) & region
    return m


def colour_key(a):
    rgb = a[..., :3].astype(np.int64)
    return rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]


def cluster_clean(a, ids, stats, protect=None, red_min=3, tag="cluster_orphans_fixed"):
    """Round 6 (AD 'sprite noise'), round 7 (AD/TA 'cloth_lone_px must be 0 for red'):
    minimum cluster size per material, 4-connected, counted INSIDE the pixel's own object group
    (so a pixel that only touches the same tone in a neighbouring part is still noise and is
    merged into its own part).  Red-ramp groups: min 3 px, other cloth: min 2 px.  A small
    cluster takes the most common other colour among its in-group 8-neighbours.  Kept: the <= 3
    purple ribbon pixels, outline pixels and `protect` (the red[1] separation lines)."""
    fixed = 0
    keep = eq(a, C["purple"][0]) | eq(a, OUTL)
    if protect is not None:
        keep |= protect
    gsel = [GID[g] for g in CLUSTER_GROUPS if g in GID]
    redsel = [GID[g] for g in RED_GROUPS if g in GID]
    for _ in range(4):
        op = a[..., 3] == 255
        valid = op & np.isin(ids, gsel)
        key = colour_key(a)
        lab, sz = region_labels(ids, key, valid)
        minsz = np.where(np.isin(ids, redsel), red_min, 2)
        small = valid & (sz[lab] < minsz) & ~keep
        if not small.any():
            break
        changed = 0
        # round 7: a small region is merged as ONE unit (all its pixels take the same colour), so
        # a 2 px region never splits into two different lone pixels
        for L in np.unique(lab[small]):
            reg = small & (lab == L)
            ys, xs = np.where(reg)
            if not len(ys):
                continue
            own = tuple(a[ys[0], xs[0], :3])
            gid = ids[ys[0], xs[0]]
            cnt, cnt_any, has_in, n_tr = {}, {}, False, 0
            for y, x in zip(ys, xs):
                for dy, dx in N8:
                    yy, xx = y + dy, x + dx
                    if not (0 <= yy < a.shape[0] and 0 <= xx < a.shape[1]) or reg[yy, xx]:
                        continue
                    w_ = 2 if abs(dy) + abs(dx) == 1 else 1
                    c = tuple(a[yy, xx, :3])
                    if ids[yy, xx] == gid and op[yy, xx]:
                        if c != OUTL:
                            has_in = True
                        if c != own and c != OUTL and not (protect is not None and protect[yy, xx]):
                            cnt[c] = cnt.get(c, 0) + w_
                    elif op[yy, xx] and ids[yy, xx] > 0 and c not in (own, OUTL) and w_ == 2:
                        cnt_any[c] = cnt_any.get(c, 0) + 1
                    if w_ == 2 and not op[yy, xx]:
                        n_tr += 1
            if not cnt and not has_in:
                if len(ys) == 1 and n_tr >= 2:
                    # a 1 px tooth sticking out into the background: removed (the outline closes it)
                    a[ys[0], xs[0], 3] = 0
                    changed += 1
                    continue
                # a FRAGMENT of a part (no other in-group pixel around it): it takes the touching
                # tone of the neighbouring part, so it merges visually
                cnt = cnt_any
            if cnt:
                col = max(cnt, key=cnt.get)
                a[reg, :3] = col
                changed += len(ys)
        fixed += changed
        if not changed:
            break
    stats[tag] = fixed
    return a


def speck_merge(a, ids, stats):
    """Round 7 (AD 'cloth_lone_px must be 0 for red; lone pixels touching the same tone in a
    neighbouring part must also be merged'): last pass over what the EYE sees -- a cloth pixel
    with no 4-neighbour of its own colour in ANY part takes the most common 4-neighbour colour of
    the same ramp (red stays red, pink stays pink), whichever part that neighbour belongs to."""
    op = a[..., 3] == 255
    gsel = [GID[g] for g in CLUSTER_GROUPS if g in GID]
    cl = op & np.isin(ids, gsel) & ~eq(a, OUTL) & ~eq(a, C["purple"][0])
    n = 0
    for _ in range(4):
        key = colour_key(a)
        kk = np.where(a[..., 3] == 255, key, -2)
        same = np.zeros(kk.shape, bool)
        for dy, dx in N4:
            same |= shift(kk, dy, dx, -1) == kk
        sp = cl & ~same
        ys, xs = np.where(sp)
        if not len(ys):
            break
        for y, x in zip(ys, xs):
            ramp = RAMP_OF.get(tuple(a[y, x, :3]))
            cnt, cnt_any = {}, {}
            for dy, dx in N4:
                yy, xx = y + dy, x + dx
                if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and a[yy, xx, 3] == 255:
                    c = tuple(a[yy, xx, :3])
                    if c != OUTL and c != tuple(a[y, x, :3]):
                        cnt_any[c] = cnt_any.get(c, 0) + 1
                        if RAMP_OF.get(c) == ramp:
                            cnt[c] = cnt.get(c, 0) + 1
            if not cnt:
                # 1 px of cloth peeking between other parts (corset straps, skin): it takes the
                # dominant touching colour (that part simply covers it)
                cnt = cnt_any
            if cnt:
                a[y, x, :3] = max(cnt, key=cnt.get)
                n += 1
    stats["speck_merged"] = n
    return a


def red_sep(a, ids, stats):
    """Round 7 (AD must-fix 'red mass at 64 px'): a 1 px interior line on the SLEEVE side
    wherever the cuff overlaps the skirt / under-skirt / bodice: red[1] where the neighbour is a
    lit red (red[2] / red[3]), red[0] violet where the neighbour is already red[1] crimson, so
    the bell cuff always separates from the petal skirt and the bodice by one value step."""
    op = a[..., 3] == 255
    g = lambda n: (ids == GID[n]) & op
    sl = g("sleeve")
    other = g("skirt") | g("skirt_under") | g("torso")
    lit = other & (eq(a, C["red"][2]) | eq(a, C["red"][3]))
    dark = other & eq(a, C["red"][1])
    nb_lit = np.zeros_like(sl)
    nb_dark = np.zeros_like(sl)
    for dy, dx in N4:
        nb_lit |= shift(lit, dy, dx)
        nb_dark |= shift(dark, dy, dx)
    slr = sl & (eq(a, C["red"][1]) | eq(a, C["red"][2]) | eq(a, C["red"][3]))
    l1 = slr & nb_lit & ~eq(a, C["red"][1])
    l1 = staircase(l1, slr & ~eq(a, C["red"][1]))
    l0 = slr & nb_dark & ~nb_lit & eq(a, C["red"][1]) & ~l1
    l0 = staircase(l0, slr & eq(a, C["red"][1]) & ~l1)
    a[l1] = np.append(C["red"][1], 255)
    a[l0] = np.append(C["red"][0], 255)
    stats["red_sep_px"] = int(l1.sum() + l0.sum())
    return a, (l1 | l0)


def scarf_pass(a, ids, stats):
    """Round 7 (AD 'flat pink rectangle'): each ribbon reads as a twisted band -- pink[0] body,
    a 1 px pink[1] lit edge on the key side (left) for the upper half of the ribbon and on the
    right for the lower half (the twist), and a skin[2] glint where it turns over.
    Ribbons narrower than 2 px or shorter than 6 px keep their render."""
    stats["scarf_twist_px"] = 0
    if "scarf" not in GID:
        return a
    op = a[..., 3] == 255
    # round 7: the violet back face (M_scarf_under) is included -- at 64 px it read as a dark
    # stick beside the arm; the twist is now drawn with the pink ramp instead
    sc = (ids == GID["scarf"]) & op & (eq(a, C["pink"][0]) | eq(a, C["pink"][1]) | eq(a, C["skin"][2])
                                       | eq(a, C["red"][0]) | eq(a, C["red"][1]))
    if sc.sum() < 6:
        return a
    lab, sz = components(sc)
    n = 0
    for k in range(1, len(sz)):
        m = lab == k
        if sz[k] < 6:
            continue
        ys, xs = np.where(m)
        y0, y1 = ys.min(), ys.max()
        x0_, x1_ = xs.min(), xs.max()
        if max(y1 - y0, x1_ - x0_) < 3:
            continue
        Y = np.broadcast_to(np.arange(a.shape[0])[:, None], m.shape)
        X = np.broadcast_to(np.arange(a.shape[1])[None, :], m.shape)
        if y1 - y0 >= x1_ - x0_:
            # mostly vertical ribbon: left / right edges, twist at the middle row
            ym = (y0 + y1) / 2.0
            L = m & ~shift(m, 0, -1)
            R = m & ~shift(m, 0, 1)
            upper = Y < ym
        else:
            # mostly horizontal (streaming) ribbon: top / bottom edges, twist at the middle column
            ym = (x0_ + x1_) / 2.0
            L = m & ~shift(m, -1, 0)      # top edge = key side
            R = m & ~shift(m, 1, 0)
            upper = X < ym
            Y = X
        lit = staircase((L & upper) | (R & ~upper), m)
        shd = staircase(((R & upper) | (L & ~upper)) & ~lit, m & ~lit)
        body = m & ~lit
        a[body] = np.append(C["pink"][0], 255)       # pink[0] body / shadow side (GD r3 base)
        a[lit] = np.append(C["pink"][1], 255)        # pink[1] lit edge, swapping sides at the twist
        # skin[2] glint where the ribbon turns over (the twist row), 1-2 px on the lit edge
        tw = lit & (np.abs(Y - ym) <= 0.6)
        tw &= ~shd
        a[tw] = np.append(C["skin"][2], 255)
        n += int(lit.sum())
    stats["scarf_twist_px"] = n
    return a


def bow_lobes(a, ids, d, stats):
    """Round 7 (AD must-fix 'one heart blob'): the bow must read as TWO lobes in every direction:
    find the dip in the bow's top contour between the two ear peaks (or the bow's centre column
    if there is none), cut a 1 px notch there (outline fills it) and draw a 1 px red[1] (red[0]
    over crimson) knot line down from the notch to ~45 % of the bow height."""
    stats["bow_notch"] = 0
    op = a[..., 3] == 255
    bow = (ids == GID["bow"]) & op
    if bow.sum() < 10:
        return a
    ys, xs = np.where(bow)
    x0, x1 = xs.min(), xs.max()
    if x1 - x0 < 4:
        return a
    top = {x: ys[xs == x].min() for x in range(x0, x1 + 1) if (xs == x).any()}
    cols = sorted(top)
    lo, hi = x0 + (x1 - x0) * 0.25, x0 + (x1 - x0) * 0.75
    mid = [x for x in cols if lo <= x <= hi]
    if not mid:
        return a
    # deepest dip between the left and right peak
    lp = min((top[x], x) for x in cols if x < (x0 + x1) / 2.0)
    rp = min((top[x], x) for x in cols if x > (x0 + x1) / 2.0)
    inner = [x for x in cols if lp[1] < x < rp[1]]
    if not inner:
        return a
    c = max(inner, key=lambda x: (top[x], -abs(x - (lp[1] + rp[1]) / 2.0)))
    ty = top[c]
    peak = max(lp[0], rp[0])
    by = ys.max()
    depth = max(2, int(round(0.45 * (by - ty + 1))))
    if ty <= peak and bow[ty, c - 1] and bow[ty, c + 1]:
        a[ty, c, 3] = 0                    # carve the notch: the outline pass fills it
        ty += 1
        stats["bow_notch"] = 1
    else:
        stats["bow_notch"] = 2             # natural V between the ears
    n = 0
    for y in range(ty, min(by + 1, ty + depth)):
        if bow[y, c] and a[y, c, 3] == 255:
            col = C["red"][0] if eq(a[y:y + 1, c:c + 1], C["red"][1])[0, 0] else C["red"][1]
            put(a, y, c, col)
            n += 1
    stats["bow_line_px"] = n
    return a


def bow_knot(a, ids, d, stats):
    """Round 6 (AD nice-to-have): a red[1] knot pixel where the bow meets the bun in S/SE/SW,
    so the bow reads as tied, not as a flat red block."""
    stats["bow_knot_px"] = 0
    if d not in ("S", "SE", "SW"):
        return a
    op = a[..., 3] == 255
    bow = (ids == GID["bow"]) & op
    bun = (ids == GID["bun"]) & op
    if bow.sum() < 6 or not bun.any():
        return a
    near = bow & (shift(bun, 0, 1) | shift(bun, 0, -1) | shift(bun, 1, 0) | shift(bun, -1, 0))
    if not near.any():
        return a
    by, bx = np.where(bow)
    cy, cx = by.mean(), bx.mean()
    ys, xs = np.where(near)
    i = int(np.argmin((ys - cy) ** 2 + (xs - cx) ** 2))
    y, x = ys[i], xs[i]
    put(a, y, x, C["red"][1])
    n = 1
    # a second knot pixel toward the bow centre (2 px knot = survives the cluster rule)
    sx = int(np.sign(round(cx - x))) if abs(cx - x) >= 0.5 else 0
    sy = int(np.sign(round(cy - y))) if abs(cy - y) >= 0.5 else 0
    for yy, xx in ((y + sy, x) if sy else (y, x + (sx or 1)), (y, x + (sx or 1)), (y + (sy or 1), x)):
        if (yy, xx) != (y, x) and 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and bow[yy, xx]:
            put(a, yy, xx, C["red"][1])
            n += 1
            break
    stats["bow_knot_px"] = n
    return a


def blade_redraw(a, ids, name, stats):
    """Round 5 (AD 'saw-tooth blade'): the sprite blade is re-rasterised as a clean constant
    2 px line (steel[2] lit edge on the top/left pixel, steel[0] spine on the other), fitted to
    the rendered blade pixels; 1 px tip.  The outline pass draws only the shadow-side outline
    next to it (no lit-side steel[0] outline -> no notches)."""
    op = a[..., 3] == 255
    sword = (ids == GID["sword"]) & op
    blade = sword & eq(a, C["steel"][2])
    stats["blade_px"] = 0
    if blade.sum() < 6:
        return a, np.zeros_like(blade)
    ys, xs = np.where(blade)
    P = np.stack([xs, ys], 1).astype(float)
    c0 = P.mean(0)
    u, sv, vt = np.linalg.svd(P - c0, full_matrices=False)
    dvec = vt[0]
    t = (P - c0) @ dvec
    # base end = the end nearer to the guard / tsuka
    other = sword & ~blade
    if "kagi" in GID:
        other |= (ids == GID["kagi"]) & op
    if other.any():
        oy, ox = np.where(other)
        oc = np.array([ox.mean(), oy.mean()])
        if ((oc - c0) @ dvec) > 0:
            dvec = -dvec
            t = -t
    t0, t1 = t.min(), t.max()
    bodyp = os.path.join(M, name[:-4] + "_body.png")
    body = np.array(Image.open(bodyp).convert("RGBA"))[..., 3] > 127 if os.path.exists(bodyp) else np.zeros_like(blade)
    # erase the old blade
    by, bx = np.where(blade)
    fills = neighbour_mode(a, by, bx, {tuple(C["steel"][2]), tuple(C["steel"][1]), tuple(C["steel"][0]), OUTL})
    for y, x, col in zip(by, bx, fills):
        if body[y, x] and col is not None:
            a[y, x, :3] = col
        else:
            a[y, x, 3] = 0
    newm = np.zeros_like(blade)
    allowed = blade.copy()
    for dy_ in (-1, 0, 1):
        for dx_ in (-1, 0, 1):
            allowed |= shift(blade, dy_, dx_)
    allowed |= ~body          # never draw the blade over body parts that hid it
    p0 = c0 + dvec * t0
    p1 = c0 + dvec * t1
    dx, dy = p1 - p0
    steep = abs(dy) > abs(dx)
    n = int(round(max(abs(dx), abs(dy))))
    for k in range(n + 1):
        f = k / max(1, n)
        x = p0[0] + dx * f
        y = p0[1] + dy * f
        if steep:
            yy = int(round(y)); xx = int(np.floor(x))
            px = [(yy, xx), (yy, xx + 1)]          # left = lit edge
        else:
            xx = int(round(x)); yy = int(np.floor(y))
            px = [(yy, xx), (yy + 1, xx)]          # top = lit edge
        if k >= n - 1:
            px = px[1:]                            # 1 px tip
        for j, (py_, px_) in enumerate(px):
            if 0 <= py_ < a.shape[0] and 0 <= px_ < a.shape[1]:
                # do not paint over the hand / tsuka / kagi (blade is behind the grip)
                if other[py_, px_] or ((ids[py_, px_] == GID["hand"]) & op[py_, px_]) or not allowed[py_, px_]:
                    continue
                lit = (j == 0 and len(px) == 2)
                put(a, py_, px_, C["steel"][2] if lit else C["steel"][0])
                newm[py_, px_] = True
    stats["blade_px"] = int(newm.sum())
    return a, newm


def paint_connected(a, mask, col, min_nb=1):
    """Round 9: paint `mask` in `col`, but only the pixels that keep >= 1 4-neighbour inside the
    painted set (iterated), so a stepped line never leaves single-pixel specks."""
    m = mask.copy()
    for _ in range(3):
        nb = shift(m, 0, 1) | shift(m, 0, -1) | shift(m, 1, 0) | shift(m, -1, 0)
        m2 = m & nb
        if (m2 == m).all():
            break
        m = m2
    a[m] = np.append(np.asarray(col, np.uint8), 255)
    return int(m.sum())


def back_polish(a, ids, d, stats):
    """Round 9 (AD / GD / TA nice-to-haves for the back three-quarter and back views, plus the
    feet in every direction):
      * N / NE / NW crown sheen: a 1 px hair[2] arc 2 px inside the top contour of the skull hair
        on the lit (screen-left) half, so the back of the head is not a flat hair[0]/[1] mass
        (skipped when the 3D angel ring already shows >= 5 px)
      * N / NE / NW bun: the bun keeps >= 3 hair[2] px on its top (bun_pass places them)
      * N / NE / NW skirt: red[3] fold highlights, a 1 px vertical line up from each lit tail tip
        (tails in the left 60% of the skirt)
      * NE / NW: red[0] rim on the sleeve-cuff hem where it overlaps the skirt (arm vs body)
      * NE / NW: 2 px skin[1] cheek on the facing side of the head (NE != N)
      * all: sandal value break -- the lowest shoe row of each foot dark[0], dark[1] above"""
    op = a[..., 3] == 255
    g = lambda n: (ids == GID[n]) & op
    st = {}
    if d in ("N", "NE", "NW"):
        skull = (g("hair") | g("sheen"))
        has = int((skull & eq(a, C["hair"][2])).sum())
        st["crown_sheen_px"] = 0
        ys, xs = np.where(skull)
        if len(xs) and has < 5:
            x0, x1 = xs.min(), xs.max()
            wdt = x1 - x0 + 1
            xa, xb = x0 + 3, x0 + int(0.55 * wdt)
            newm = np.zeros(skull.shape, bool)
            for x in range(xa, xb):
                col = np.where(skull[:, x])[0]
                if not len(col):
                    continue
                y = col.min() + 2
                # 2 px tall over the middle third of the arc, 1 px toward its ends
                for yy in ((y, y + 1) if xa + (xb - xa) / 3.0 <= x < xa + 2 * (xb - xa) / 3.0 else (y,)):
                    if skull[yy, x] and skull[yy - 1, x] and (eq(a[yy:yy + 1, x:x + 1], C["hair"][1])[0, 0]
                                                           or eq(a[yy:yy + 1, x:x + 1], C["hair"][0])[0, 0]):
                        newm[yy, x] = True
            # where the arc steps a row, the step pixel is bridged so the arc stays 4-connected
            for x in range(xa, xb - 1):
                c0, c1 = np.where(newm[:, x])[0], np.where(newm[:, x + 1])[0]
                if len(c0) and len(c1) and c0.min() != c1.min() and abs(c0.min() - c1.min()) == 1:
                    y = max(c0.min(), c1.min())
                    xx = x if c0.min() < c1.min() else x + 1
                    if skull[y, xx]:
                        newm[y, xx] = True
            st["crown_sheen_px"] = paint_connected(a, newm, C["hair"][2])
        # skirt fold highlights on the lit tails
        sk = g("skirt")
        ys, xs = np.where(sk)
        st["skirt_fold_px"] = 0
        if len(xs):
            x0, x1 = xs.min(), xs.max()
            low = np.full(a.shape[1], -1)
            for x in range(x0, x1 + 1):
                c_ = np.where(sk[:, x])[0]
                if len(c_):
                    low[x] = c_.max()
            foldm = np.zeros(sk.shape, bool)
            for x in range(x0 + 1, x0 + int(0.6 * (x1 - x0 + 1))):
                if low[x] < 0:
                    continue
                # a tail tip: lower than both neighbours' hem (local minimum of the hem line)
                if not (low[x] >= low[x - 1] and low[x] >= low[x + 1] and (low[x] > low[x - 1] or low[x] > low[x + 1])):
                    continue
                if low[x] < ys.min() + 0.6 * (ys.max() - ys.min()):
                    continue
                cx = x + 1 if (x + 1 < a.shape[1] and sk[low[x] - 1, x + 1]) else x
                if not sk[low[x] - 1, cx - 1]:
                    continue
                for y in range(low[x] - 1, low[x] - 5, -1):
                    if sk[y, cx] and (eq(a[y:y + 1, cx:cx + 1], C["red"][2])[0, 0] or eq(a[y:y + 1, cx:cx + 1], C["red"][1])[0, 0]):
                        foldm[y, cx] = True
                    else:
                        break
            st["skirt_fold_px"] = paint_connected(a, foldm, C["red"][3])
    if d in ("NE", "NW"):
        sl = g("sleeve")
        body = g("skirt") | g("skirt_under")
        hem = sl & shift(body, -1, 0)
        st["cuff_hem_px"] = paint_connected(a, hem, C["red"][0])
        # cheek tell on the facing side (NE faces screen-right, NW screen-left)
        head = g("hair") | g("sheen") | g("face") | (g("ear") if "ear" in GID else False)
        a[g("face") & (eq(a, C["steel"][2]) | eq(a, C["eye"][0]) | eq(a, C["eye"][1]))] = np.append(C["skin"][1], 255)
        ys, xs = np.where(head)
        st["cheek_px"] = 0
        if len(ys):
            hy1 = ys.max()
            for y in range(hy1 - 6, hy1 - 3):
                row = np.where(head[y])[0]
                if not len(row):
                    continue
                x = row.max() if d == "NE" else row.min()
                if eq(a[y:y + 1, x:x + 1], OUTL)[0, 0]:
                    x += -1 if d == "NE" else 1
                if not eq(a[y:y + 1, x:x + 1], C["skin"][1])[0, 0]:
                    put(a, y, x, C["skin"][1])
                st["cheek_px"] += 1
                if st["cheek_px"] >= 2:
                    break
    # sandals: value break
    nfeet = 0
    for gname in ("leg_L", "leg_R"):
        if gname not in GID:
            continue
        shoe = g(gname) & eq(a, C["dark"][1])
        lab, sz = components(shoe)
        for k in range(1, len(sz)):
            yy, xx = np.where(lab == k)
            if yy.max() - yy.min() < 1:
                continue
            bot = yy == yy.max()
            rest = np.zeros(shoe.shape, bool)
            rest[yy[~bot], xx[~bot]] = True
            nb = shift(rest, 0, 1) | shift(rest, 0, -1) | shift(rest, 1, 0) | shift(rest, -1, 0)
            if rest.sum() >= 2 and not (rest & ~nb).any():     # the dark[1] upper stays one piece
                for y, x in zip(yy[bot], xx[bot]):
                    put(a, y, x, C["dark"][0])
                nfeet += 1
    st["sandal_break_feet"] = nfeet
    stats.update(st)
    return a


def clean(a, ids, stats):
    op = a[..., 3] == 255
    g = lambda n: (ids == GID[n]) & op
    hair = g("hair") | g("sheen") | g("bun")
    bow = g("bow")
    # ---- a. hair ramp: outline specks inside the hair mass -> hair[0]; ring = 1 px, continuous
    rec = hair & eq(a, OUTL)
    nb_hair = sum(shift(hair, dy, dx) for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)))
    a[rec & (nb_hair >= 3)] = np.append(C["hair"][0], 255)
    ring = hair & eq(a, C["hair"][2])
    above = shift(ring, -1, 0)
    horiz = shift(ring, 0, -1) | shift(ring, 0, 1)
    thin = ring & above & horiz
    ring2 = ring & ~thin
    ring3 = drop_small(ring2, 3)
    a[ring & ~ring3] = np.append(C["hair"][1], 255)
    stats["sheen_components"] = int(components(ring3)[1].shape[0] - 1)
    # ---- b. pink rim, round 4 (AD): ONLY the right (back-right, away from the key) contour,
    # 1 px.  Hair: rows between 15% and 75% of the head height (no crown cap outline in N/NW).
    # Bow: right contour of the bow only, so >= 70% of the bow stays red[1]/red[2].
    head = hair | bow
    a[hair & eq(a, C["pink"][0])] = np.append(C["hair"][0], 255)     # material rim leftovers
    a[bow & eq(a, C["pink"][0])] = np.append(C["red"][2], 255)
    tr = ~op
    right = head & shift(tr, 0, 1, True)
    ys_ = np.where(head.any(axis=1))[0]
    if len(ys_):
        Y = np.arange(a.shape[0])[:, None].repeat(a.shape[1], 1)
        hy = np.where(hair.any(axis=1))[0]
        band = np.ones_like(hair)
        if len(hy):
            band = (Y >= hy.min() + 0.15 * (hy.max() - hy.min())) & (Y <= hy.min() + 0.75 * (hy.max() - hy.min()))
        rim = (right & hair & band) | (right & bow)
        rim = drop_small(rim, 3)
        a[rim] = np.append(C["pink"][0], 255)
        stats["rim_px"] = int(rim.sum())
    # bow value (AD): coral red[3] at most ~12% of the bow (a lit sliver), the rest red[2] /
    # red[1] / red[0] opening
    bw = bow & op
    co = bw & eq(a, C["red"][3])
    if bw.sum() and co.sum() > 0.12 * bw.sum():
        ys, xs = np.where(co)
        order = np.argsort(ys + xs)            # keep the top-left-most coral (key side)
        keep = int(0.12 * bw.sum())
        for i in order[keep:]:
            a[ys[i], xs[i]] = np.append(C["red"][2], 255)
    # ---- b2. chest cluster, round 4 (AD 'S chest blob'): the bodice is flat red[2] with a 1 px
    # red[1] collar-base line; the chest flower is not rendered on sprites; the arm-flower
    # cluster keeps <= 3 red[3] highlight px + <= 3 purple px, its other petals take red[2]
    torso_red = g("torso") & op & (eq(a, C["red"][1]) | eq(a, C["red"][2]) | eq(a, C["red"][3]))
    a[torso_red] = np.append(C["red"][2], 255)
    cbase = torso_red & shift(g("collar") & op, -1, 0)
    a[cbase] = np.append(C["red"][1], 255)
    orn = g("ornament") & op
    orn_red = orn & (eq(a, C["red"][1]) | eq(a, C["red"][2]) | eq(a, C["red"][3]))
    pur = orn & eq(a, C["purple"][0])
    if orn_red.any():
        ys, xs = np.where(orn_red)
        if pur.any():
            py_, px_ = np.where(pur)
            cy, cx = py_.mean(), px_.mean()
        else:
            cy, cx = ys.mean(), xs.mean()
        order = np.argsort((ys - cy) ** 2 + (xs - cx) ** 2)
        a[orn_red] = np.append(C["red"][2], 255)
        for i in order[:3]:
            a[ys[i], xs[i]] = np.append(C["red"][3], 255)
    if pur.sum() > 3:
        ys, xs = np.where(pur)
        order = np.argsort(-ys)                 # keep the lowest = dangling ribbon read
        for i in order[3:]:
            a[ys[i], xs[i]] = np.append(C["red"][2], 255)
    # ---- b3. sleeves, round 4 (AD 'sleeve value'): red[2] base; red[3] only on the top-left lit
    # plane, <= 25% of the sleeve; red[1] separation line where the sleeve meets a lit (red[2])
    # skirt pixel
    sl = g("sleeve") & op
    co = sl & eq(a, C["red"][3])
    if sl.sum() and co.sum() > 0.25 * sl.sum():
        ys, xs = np.where(co)
        order = np.argsort(ys + xs)
        keep = int(0.25 * sl.sum())
        for i in order[keep:]:
            a[ys[i], xs[i]] = np.append(C["red"][2], 255)
    skr = (g("skirt") | g("skirt_under")) & op & eq(a, C["red"][2])
    nb = shift(skr, 0, 1) | shift(skr, 0, -1) | shift(skr, 1, 0) | shift(skr, -1, 0)
    a[sl & nb & eq(a, C["red"][2])] = np.append(C["red"][1], 255)
    # ---- c. stray violet
    purple = eq(a, C["purple"][0]) & op
    stray = purple & ~g("ornament")
    lone = purple & g("ornament") & (sum(shift(purple, dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                                         if dy or dx) == 0)
    v0 = eq(a, C["red"][0]) & g("sleeve")
    v0 &= sum(shift(v0, dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx) == 0
    fix = stray | lone | v0
    ys, xs = np.where(fix)
    for y, x, col in zip(ys, xs, neighbour_mode(a, ys, xs, {tuple(C["purple"][0]), tuple(C["red"][0])})):
        if col is not None:
            a[y, x, :3] = col
    stats["violet_fixed"] = int(fix.sum())
    # ---- d. corset band
    band = g("corset") | g("buckles")
    a[band] = np.append(C["leather"][1], 255)
    topl = band & ~shift(band, -1, 0)
    a[topl] = np.append(C["leather"][2], 255)
    bk = g("buckles") & ~topl
    nsteel = 0
    if bk.sum() >= 2:
        ys, xs = np.where(bk)
        cy, cx = int(round(ys.mean())), int(round(xs.mean()))
        pts = sorted(zip(ys, xs), key=lambda p: (p[0] - cy) ** 2 + (p[1] - cx) ** 2)[:1]
        y0, x0 = pts[0]
        for (yy, xx) in ((y0, x0), (y0 + 1, x0)):
            if 0 <= yy < a.shape[0] and band[yy, xx] and not topl[yy, xx]:
                a[yy, xx] = np.append(C["steel"][1], 255)
                nsteel += 1
    stats["corset_steel_px"] = nsteel
    pouch = g("pouch")
    a[pouch] = np.append(C["leather"][1], 255)
    ptop = pouch & ~shift(pouch | band, -1, 0)
    a[ptop] = np.append(C["leather"][2], 255)
    # ---- e. skirt hems: single-pixel teeth / notches
    sk = (g("skirt") | g("skirt_under"))
    teeth = notches = 0
    for _ in range(2):
        op = a[..., 3] == 255
        below_t = shift(~op, 1, 0, True)
        lft, rgt = shift(sk, 0, -1), shift(sk, 0, 1)
        up = shift(sk, -1, 0)
        up_h = shift(shift(sk, 0, -1) | shift(sk, 0, 1), -1, 0)
        tooth = sk & below_t & ~lft & ~rgt & up & up_h
        a[tooth, 3] = 0
        sk &= ~tooth
        teeth += int(tooth.sum())
        op = a[..., 3] == 255
        notch = ~op & shift(sk, 0, -1) & shift(sk, 0, 1) & shift(sk, -1, 0)
        ys, xs = np.where(notch)
        for y, x in zip(ys, xs):
            a[y, x] = a[y, x - 1]
        sk |= notch
        notches += int(notch.sum())
    stats["hem_teeth_removed"] = teeth
    stats["hem_notches_filled"] = notches
    # ---- g. sprite blade (TA/Gemini): steel[1] body with a 1 px steel[2] edge on the lit (top)
    # side; guard / kagi / tsuka (steel[1], ink, red[2]) untouched
    # (round 5: the blade is re-rasterised in blade_redraw(), called after clean())
    # ---- h. blush: at most 2 px per cheek (bible: SIMPLIFY to 1-2 px)
    bl = g("face") & op & eq(a, C["pink"][0])
    lab, sz = components(bl)
    for k in range(1, len(sz)):
        ys, xs = np.where(lab == k)
        if len(ys) <= 2:
            continue
        cy, cx = ys.mean(), xs.mean()
        order = np.argsort((ys - cy) ** 2 + (xs - cx) ** 2)
        for i in order[2:]:
            a[ys[i], xs[i]] = np.append(C["skin"][1], 255)
    # ---- h1. eyes (round 5, AD): 3x4 near / 2x3 far hand-pixel templates
    a = stamp_eyes(a, ids, cell_dir(stats.get("_name", "")), stats)
    # ---- h2. mouth + blush, round 9 (AD/GD 'S face: 2 px vertical mark reads as a nose / open
    # mouth; blush missing'): every skin[0] mark on the face from the lash row down to 2 rows
    # under the eyes is cleared (bible: no nose); then ONE 1 px skin[0] mouth 2 rows under the
    # eye bottoms, centred between the eyes (or none if there is no skin[1] room), and 1 px
    # pink[0] blush right under each near eye (inner-lower corner when the collar takes the rest)
    op = a[..., 3] == 255
    fm = g("face") & op
    stats["mouth_px"] = 0
    stats["blush_px"] = 0
    boxes = stats.get("eye_boxes") or []
    if boxes:
        ytop = min(b[1] for b in boxes)
        ybot = max(b[1] + b[3] - 1 for b in boxes)
        band = np.zeros_like(fm)
        band[max(0, ytop):ybot + 5, :] = True
        a[fm & band & eq(a, C["skin"][0])] = np.append(C["skin"][1], 255)
        a[fm & band & eq(a, C["pink"][0])] = np.append(C["skin"][1], 255)
        skin1 = fm & eq(a, C["skin"][1])
        mouth = None
        if len(boxes) >= 2:
            xs_ = sorted(b[0] + (b[2] - 1) / 2.0 for b in boxes)
            tx = int(round((xs_[0] + xs_[-1]) / 2.0))
            for ty, dx in ((ybot + 2, 0), (ybot + 2, 1), (ybot + 2, -1), (ybot + 3, 0), (ybot + 3, 1), (ybot + 3, -1)):
                tx_ = tx + dx
                if 0 <= ty < a.shape[0] and 1 <= tx_ < a.shape[1] - 1 and skin1[ty, tx_] \
                        and skin1[ty, tx_ - 1] and skin1[ty, tx_ + 1]:
                    a[ty, tx_] = np.append(C["skin"][0], 255)
                    mouth = (ty, tx_)
                    stats["mouth_px"] = 1
                    break
        skin1 = fm & eq(a, C["skin"][1])
        cxs = [b[0] + (b[2] - 1) / 2.0 for b in boxes]
        cmid = sum(cxs) / len(cxs)
        for (x0, y0, w, h) in boxes:
            if w < 3 and len(boxes) > 1:
                continue                       # far eye in SE / SW: no blush (it would touch the collar)
            yb = y0 + h
            outer = -1 if x0 + (w - 1) / 2.0 < cmid else 1
            cols = [x0 + (0 if outer < 0 else w - 1), x0 + w // 2, x0 + (w - 1 if outer < 0 else 0)]
            done = False
            for yy in (yb, yb + 1):
                for xx in cols:
                    if not (0 <= yy < a.shape[0] and 0 <= xx < a.shape[1]) or not skin1[yy, xx]:
                        continue
                    if mouth and abs(mouth[0] - yy) + abs(mouth[1] - xx) <= 1:
                        continue
                    a[yy, xx] = np.append(C["pink"][0], 255)
                    stats["blush_px"] += 1
                    done = True
                    break
                if done:
                    break
    # ---- f. cloth orphans
    op = a[..., 3] == 255
    cloth = (g("skirt") | g("skirt_under") | g("sleeve") | g("collar") | g("torso") | g("shorts") | hair) & op
    rgb = a[..., :3].astype(np.int32)
    key = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]
    kn = [shift(key, dy, dx, -1) for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))]
    same4 = (kn[0] == kn[1]) & (kn[1] == kn[2]) & (kn[2] == kn[3]) & (kn[0] >= 0)
    orphan = cloth & same4 & (kn[0] != key) & ~eq(a, C["hair"][2]) & ~eq(a, C["pink"][0])
    ys, xs = np.where(orphan)
    for y, x in zip(ys, xs):
        a[y, x] = a[y, x + 1] if x + 1 < a.shape[1] else a[y, x - 1]
    stats["orphans_fixed"] = int(orphan.sum())
    return a


def outline(a, blade=None):
    op = a[..., 3] > 127
    a[..., 3] = np.where(op, 255, 0)
    out = a.copy()
    H, W = op.shape
    for y in range(H):
        for x in range(W):
            if op[y, x]:
                continue
            nb = []
            for dy, dx, lit in ((0, 1, True), (1, 0, True), (0, -1, False), (-1, 0, False)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and op[yy, xx]:
                    nb.append((tuple(a[yy, xx, :3]), lit))
            if not nb:
                continue
            col = OUTL
            if blade is not None and all(l for _, l in nb):
                # round 5: no lit-side outline along the redrawn blade (shadow side only)
                lit_nb = [(y + dy, x + dx) for dy, dx in ((0, 1), (1, 0))
                          if 0 <= y + dy < H and 0 <= x + dx < W and op[y + dy, x + dx]]
                if lit_nb and all(blade[yy, xx] for yy, xx in lit_nb):
                    continue
            if all(l for _, l in nb):     # outline pixel lies above/left of the body = lit side
                r = RAMP_OF.get(nb[0][0])
                col = LIT.get(r, OUTL)
            out[y, x, :3] = col
            out[y, x, 3] = 255
    return out


STATS = {}
for raw in sorted(glob.glob(os.path.join(M, "raw_*.png"))):
    name = os.path.basename(raw)[4:]
    a = np.array(Image.open(raw).convert("RGBA"))
    a[..., 3] = np.where(a[..., 3] > 127, 255, 0)
    ids = load_id(name)
    st = {"_name": name}
    bm = None
    if ids is not None:
        a = clean(a, ids, st)
        a = bun_pass(a, ids, st)
        a = leg_split(a, ids, st)
        a = ear_pass(a, ids, st)
        a, sep = red_sep(a, ids, st)
        a = scarf_pass(a, ids, st)
        a = cluster_clean(a, ids, st, protect=sep | ((ids == GID["scarf"]) if "scarf" in GID else False))
        a = bow_knot(a, ids, cell_dir(name), st)
        a = bow_lobes(a, ids, cell_dir(name), st)
        # final pass, nothing protected: separation-line / knot pixels left as single pixels merge
        a = cluster_clean(a, ids, st, protect=None, red_min=2, tag="cluster_final_fixed")
        a = speck_merge(a, ids, st)
        a = back_polish(a, ids, cell_dir(name), st)
        a, bm = blade_redraw(a, ids, name, st)
        BLADE_MASKS[name] = bm
    st.pop("_name", None)
    STATS[name] = st
    o = outline(a, bm)
    if ids is not None and "kagi" in GID:
        # round 4 (AD): the kagi hook gets a steel[0] outline (not the plum-black one), so the
        # crescent reads as a separate steel shape next to the dark tsuka / hand
        kg = (ids == GID["kagi"]) & (a[..., 3] == 255)
        ring = (shift(kg, 0, 1) | shift(kg, 0, -1) | shift(kg, 1, 0) | shift(kg, -1, 0)) & (a[..., 3] == 0)
        o[ring] = np.append(C["steel"][0], 255)
        st["kagi_outline_px"] = int(ring.sum())
    Image.fromarray(o, "RGBA").save(os.path.join(D, name))


def dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= shift(m, dy, dx)
    return out


checks = {}
for p in sorted(glob.glob(os.path.join(D, "*_64.png"))):
    name = os.path.basename(p)
    tag = name[:-4]
    fin = np.array(Image.open(p).convert("RGBA"))
    alpha = fin[..., 3]
    semi = int(((alpha > 0) & (alpha < 255)).sum())
    cols = {tuple(c) for c in fin[alpha == 255][:, :3]}
    off = [c for c in cols if c not in ALLC]
    c = dict(colours=len(cols), off_palette=len(off), semi_alpha=semi)
    swp, bdp = os.path.join(M, f"{tag}_sword.png"), os.path.join(M, f"{tag}_body.png")
    ids = load_id(name)
    if os.path.exists(swp) and os.path.exists(bdp):
        sw = np.array(Image.open(swp).convert("RGBA"))[..., 3] > 127
        bd = np.array(Image.open(bdp).convert("RGBA"))[..., 3] > 127
        vis = sw & ~bd
        blk = sw[:-1, :-1] & sw[1:, :-1] & sw[:-1, 1:] & sw[1:, 1:]
        in2 = np.zeros_like(sw)
        in2[:-1, :-1] |= blk; in2[1:, :-1] |= blk; in2[:-1, 1:] |= blk; in2[1:, 1:] |= blk
        need = 35 if tag.startswith("iso_") else 30
        c.update(sword_px=int(sw.sum()), sword_px_outside_body=int(vis.sum()),
                 sword_frac_2px=round(float(in2[sw].mean()) if sw.any() else 0.0, 3),
                 blade_outside_ok=bool(vis.sum() >= need), blade_outside_min=need)
        ys = np.where(bd.any(axis=1))[0]
        c["char_height_px"] = int(ys.max() - ys.min() + 1) if len(ys) else 0
        c["lowest_body_px_y"] = int(ys.max()) if len(ys) else -1
        # pivot rule: standing cells (idle + cycles) put the lowest foot pixel at 104 +- 3; wide
        # stances / jumps legitimately extend below or lift off and are reported only
        # round 5: jump air frames and lunging attacks legitimately leave the pivot row
        stand = tag.startswith("iso_") or tag.startswith("anim_idle") or tag.startswith("anim_walk") \
            or tag.startswith("anim_run")
        c["foot_pivot_ok"] = bool(len(ys) and abs(int(ys.max()) - 104) <= 3) if stand else None
    if ids is not None:
        g = lambda n: ids == GID[n]
        headm = g("hair") | g("sheen") | g("bun") | g("bow") | g("face") | (g("ear") if "ear" in GID else False)
        bodym = (ids > 0) & ~g("sword")
        ys = np.where(bodym.any(axis=1))[0]
        hy = np.where(headm.any(axis=1))[0]
        if len(ys) and len(hy):
            c["head_ratio"] = round((hy.max() - hy.min() + 1) / (ys.max() - ys.min() + 1), 3)
        # scarf vs arm proximity (GD): connected scarf pixels within 2 px of arm/hand/sleeve
        # primary (GD 'phantom limb'): pink ribbon running beside a BARE arm (skin arm / glove)
        armm = g("arm") | g("hand")
        near = g("scarf") & dilate(armm, 2)
        lab, sz = components(near)
        c["scarf_near_arm_max_run"] = int(sz[1:].max()) if len(sz) > 1 else 0
        c["scarf_near_arm_ok"] = bool(c["scarf_near_arm_max_run"] <= 6)
        # secondary (reported, not gating): ribbon pixels within 2 px of the red sleeve
        near = g("scarf") & dilate(g("sleeve"), 2)
        lab, sz = components(near)
        c["scarf_near_sleeve_max_run"] = int(sz[1:].max()) if len(sz) > 1 else 0
        # round 6 (AD 'sprite noise'): isolated single pixels left inside the cloth groups
        rgb = fin[..., :3].astype(np.int32)
        key = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]
        lone_n = 0
        lone_red = 0
        lone8 = 0
        frag_n = 0
        legacy = 0
        for gname in CLUSTER_GROUPS:
            if gname not in GID:
                continue
            gm = g(gname) & (alpha == 255) & ~eq(fin, C["purple"][0]) & ~eq(fin, OUTL)
            for sc_ in C["steel"] + C["eye"]:      # round 7: blade / glint pixels drawn over the part
                gm &= ~eq(fin, sc_)
            kk = np.where(gm, key, -1)
            same = np.zeros_like(gm)
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                same |= shift(kk, dy, dx, -1) == kk
            same8 = same.copy()
            for dy, dx in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                same8 |= shift(kk, dy, dx, -1) == kk
            ing = g(gname) & (alpha == 255)
            has_in = np.zeros_like(gm)
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                has_in |= shift(ing, dy, dx)
            frag = gm & ~has_in               # 1 px fragment of the part (no in-group 4-neighbour)
            lone_n += int((gm & ~same & ~frag).sum())
            lone8 += int((gm & ~same8 & ~frag).sum())
            frag_n += int(frag.sum())
            legacy += int((gm & ~same).sum())
            if gname in RED_GROUPS:
                lone_red += int((gm & ~same & ~frag).sum())
        # cloth_lone_px: same definition as round 6 (no same-colour 4-neighbour inside its own
        # group).  cloth_lone_red_px: the red-ramp groups only.  cloth_lone8_px: no same-colour
        # 8-neighbour (a pixel of a 1 px diagonal line counts as connected).
        # round 7: 1 px fragments of a part peeking between other parts (no in-group neighbour,
        # recoloured to the touching tone) are counted separately as cloth_fragment_px;
        # cloth_lone_legacy_px = round-6 number including them
        # round 7: cloth_speck_px = VISUAL specks: a cloth pixel with no 4-neighbour of the same
        # colour in ANY part (what the eye reads as noise); red-ramp parts only in _red
        kk_all = np.where(alpha == 255, key, -2)
        same_any = np.zeros(alpha.shape, bool)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            same_any |= shift(kk_all, dy, dx, -1) == kk_all
        clm = np.zeros(alpha.shape, bool)
        rdm = np.zeros(alpha.shape, bool)
        for gname in CLUSTER_GROUPS:
            if gname in GID:
                gm_ = g(gname) & (alpha == 255) & ~eq(fin, C["purple"][0]) & ~eq(fin, OUTL)
                for sc_ in C["steel"] + C["eye"]:
                    gm_ &= ~eq(fin, sc_)
                clm |= gm_
                if gname in RED_GROUPS:
                    rdm |= gm_
        c["cloth_speck_px"] = int((clm & ~same_any).sum())
        c["cloth_speck_red_px"] = int((rdm & ~same_any).sum())
        c["cloth_lone_px"] = lone_n
        c["cloth_fragment_px"] = frag_n
        c["cloth_lone_legacy_px"] = legacy
        c["cloth_lone_red_px"] = lone_red
        c["cloth_lone8_px"] = lone8
        purple = eq(fin, C["purple"][0]) & (alpha == 255)
        c["violet_outside_ornament"] = int((purple & ~g("ornament")).sum())
        rim = eq(fin, C["pink"][0]) & (g("hair") | g("sheen") | g("bun") | g("bow"))
        lab, sz = components(rim)
        c["rim_orphans"] = int((sz[1:] < 3).sum()) if len(sz) > 1 else 0
        st = (g("corset") | g("buckles")) & eq(fin, C["steel"][1])
        c["corset_steel_px"] = int(st.sum())
        sh = g("sheen") & eq(fin, C["hair"][2])
        c["sheen_components"] = int(len(components(sh)[1]) - 1)
        # round 4 (AD): kagi hook check -- visible hook pixels (own object id), connected, and
        # separate from the blade (pixels with no blade pixel in their 8-neighbourhood)
        if "kagi" in GID:
            kg = g("kagi") & (alpha == 255)
            lab, sz = components(kg)
            big = int(sz[1:].max()) if len(sz) > 1 else 0
            blade = BLADE_MASKS.get(name)
            if blade is None:
                blade = g("sword") & (alpha == 255) & (eq(fin, C["steel"][1]) | eq(fin, C["steel"][2]))
            free = kg & ~dilate(blade, 1)
            c["hook_px"] = big
            c["hook_free_px"] = int(free.sum())
            c["hook_connected"] = bool(big >= 0.8 * kg.sum()) if kg.any() else False
            c["hook_ok"] = bool(big >= 3 and c["hook_connected"] and c["hook_free_px"] >= 2)
            # round 6: a guard that is COMPLETELY hidden behind her own body (0 visible kagi px,
            # two-handed grips seen from behind) is reported separately as hook_occluded; a
            # partially visible hook that fails the rule stays a hook fail
            c["hook_occluded"] = bool(not kg.any())
        # round 4 (AD): bow + sleeve value fractions
        bw = g("bow") & (alpha == 255)
        if bw.any():
            c["bow_red12_frac"] = round(float((bw & (eq(fin, C["red"][1]) | eq(fin, C["red"][2]))).sum() / bw.sum()), 3)
            c["bow_red0_px"] = int((bw & eq(fin, C["red"][0])).sum())
        sl = g("sleeve") & (alpha == 255)
        if sl.any():
            c["sleeve_red3_frac"] = round(float((sl & eq(fin, C["red"][3])).sum() / sl.sum()), 3)
            c["sleeve_red2_frac"] = round(float((sl & eq(fin, C["red"][2])).sum() / sl.sum()), 3)
    c.update({k: v for k, v in STATS.get(name, {}).items() if k not in c})
    checks[tag] = c

checks["_summary"] = dict(
    cells=len([k for k in checks if not k.startswith("_")]),
    palette_exact=all(v.get("off_palette", 0) == 0 for k, v in checks.items() if not k.startswith("_")),
    semi_alpha_zero=all(v.get("semi_alpha", 0) == 0 for k, v in checks.items() if not k.startswith("_")),
    blade_outside_fail=[k for k, v in checks.items() if not k.startswith("_") and v.get("blade_outside_ok") is False],
    scarf_near_arm_fail=[k for k, v in checks.items() if not k.startswith("_") and v.get("scarf_near_arm_ok") is False],
    foot_pivot_fail=[k for k, v in checks.items() if not k.startswith("_") and v.get("foot_pivot_ok") is False],
    rim_orphans_total=sum(v.get("rim_orphans", 0) for k, v in checks.items() if not k.startswith("_")),
    hook_fail=[k for k, v in checks.items() if not k.startswith("_") and v.get("hook_ok") is False
               and not v.get("hook_occluded")],
    hook_occluded=[k for k, v in checks.items() if not k.startswith("_") and v.get("hook_occluded")],
    char_height_px_range=[min(v.get("char_height_px", 999) for k, v in checks.items() if k.startswith("iso_")),
                          max(v.get("char_height_px", 0) for k, v in checks.items() if k.startswith("iso_"))],
    cloth_lone_px_total=sum(v.get("cloth_lone_px", 0) for k, v in checks.items() if not k.startswith("_")),
    cloth_lone_red_px_total=sum(v.get("cloth_lone_red_px", 0) for k, v in checks.items() if not k.startswith("_")),
    cloth_speck_px_total=sum(v.get("cloth_speck_px", 0) for k, v in checks.items() if not k.startswith("_")),
    cloth_speck_red_px_total=sum(v.get("cloth_speck_red_px", 0) for k, v in checks.items() if not k.startswith("_")),
    cloth_fragment_px_total=sum(v.get("cloth_fragment_px", 0) for k, v in checks.items() if not k.startswith("_")),
    cloth_lone_legacy_px_total=sum(v.get("cloth_lone_legacy_px", 0) for k, v in checks.items() if not k.startswith("_")),
    cloth_lone8_px_total=sum(v.get("cloth_lone8_px", 0) for k, v in checks.items() if not k.startswith("_")),
    eye_px_SSESW_min=min([v.get("eye_px", 99) for k, v in checks.items() if k.startswith("iso_S")] or [0]),
    violet_outside_ornament_total=sum(v.get("violet_outside_ornament", 0) for k, v in checks.items()
                                      if not k.startswith("_")),
)
# round 6 (TA): idle height-spread gate over the 8 iso cells (<= 3 px)
_hr = checks["_summary"]["char_height_px_range"]
checks["_summary"]["char_height_spread_px"] = _hr[1] - _hr[0]
checks["_summary"]["char_height_spread_ok"] = bool(_hr[1] - _hr[0] <= 3)
checks["_summary"]["gates_failed"] = [k for k, v in (
    ("palette_exact", not checks["_summary"]["palette_exact"]),
    ("semi_alpha_zero", not checks["_summary"]["semi_alpha_zero"]),
    ("blade_outside", bool(checks["_summary"]["blade_outside_fail"])),
    ("scarf_near_arm", bool(checks["_summary"]["scarf_near_arm_fail"])),
    ("foot_pivot", bool(checks["_summary"]["foot_pivot_fail"])),
    ("hook", bool(checks["_summary"]["hook_fail"])),
    ("char_height_spread", not checks["_summary"]["char_height_spread_ok"])) if v]
json.dump(checks, open(os.path.join(D, "checks.json"), "w"), indent=1, default=float)
for d, c in checks.items():
    if d.startswith("iso_") or d.startswith("_"):
        print(d, c)
