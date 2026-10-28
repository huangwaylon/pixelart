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
    if d == "S":
        sizes = [(3, 4)] * len(eyes)
    elif d in ("SE", "SW"):
        sizes = [(3, 4), (2, 3)][:len(eyes)]
    else:   # E / W profile: one eye
        eyes = eyes[:1]
        sizes = [(2, 3)]
    # left-to-right, keep >= 1 px skin between the two eyes
    order = sorted(range(len(eyes)), key=lambda i: eyes[i][2])
    boxes = []
    for i in order:
        n, cy, cx = eyes[i]
        w, h = sizes[i]
        x0 = int(round(cx - (w - 1) / 2.0))
        y0 = int(round(cy)) - (h - 2)          # lash row; blue rows below it
        if boxes and x0 <= boxes[-1][0] + boxes[-1][2]:
            x0 = boxes[-1][0] + boxes[-1][2] + 1
        boxes.append((x0, y0, w, h))
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
                elif h == 4:
                    col = C["eye"][0] if r <= 2 else C["eye"][1]
                    if r == 1 and c == 0:
                        col = C["steel"][2]      # glint on the key-light (left) side
                else:
                    col = C["eye"][0] if r == 1 else C["eye"][1]
                put(a, y, x, col)
                cnt += 1
    stats["eye_px"] = cnt
    stats["eye_boxes"] = [list(b) for b in boxes]
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
    # ---- h2. mouth (GD/TA nice-to-have): a 1 px skin[0] mouth under the eyes whenever both
    # the eyes and enough face skin are visible (S / SE / SW) and no mouth pixel survived
    op = a[..., 3] == 255
    fm = g("face") & op
    eyes = fm & (eq(a, C["eye"][0]) | eq(a, C["eye"][1]))
    stats["mouth_px"] = 0
    if eyes.sum() >= 4:
        ys, xs = np.where(eyes)
        ty, tx = int(ys.max()) + 3, int(round(xs.mean()))
        skin1 = fm & eq(a, C["skin"][1])
        below = np.zeros_like(fm)
        below[ty - 1:ty + 2, tx - 3:tx + 4] = True
        if (fm & eq(a, C["skin"][0]) & below).sum() == 0:
            # round 5: wider search (SE / SW: the eye centroid sits over the collar edge)
            cand = [(0, 0), (-1, 0), (0, 1), (0, -1), (1, 0), (0, 2), (0, -2), (1, 1), (1, -1), (-1, 1), (-1, -1),
                    (-2, 0), (-1, 2), (-1, -2), (-2, 1), (-2, -1), (0, 3), (0, -3), (-1, 3), (-1, -3)]
            for dy, dx in cand:
                yy, xx = ty + dy, tx + dx
                if 0 <= yy < a.shape[0] and 1 <= xx < a.shape[1] - 1 and skin1[yy, xx] \
                        and skin1[yy, xx - 1] and skin1[yy, xx + 1]:
                    a[yy, xx] = np.append(C["skin"][0], 255)
                    stats["mouth_px"] = 1
                    break
        else:
            stats["mouth_px"] = int((fm & eq(a, C["skin"][0]) & below).sum())
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
    hook_fail=[k for k, v in checks.items() if not k.startswith("_") and v.get("hook_ok") is False],
    char_height_px_range=[min(v.get("char_height_px", 999) for k, v in checks.items() if k.startswith("iso_")),
                          max(v.get("char_height_px", 0) for k, v in checks.items() if k.startswith("iso_"))],
    violet_outside_ornament_total=sum(v.get("violet_outside_ornament", 0) for k, v in checks.items()
                                      if not k.startswith("_")),
)
json.dump(checks, open(os.path.join(D, "checks.json"), "w"), indent=1)
for d, c in checks.items():
    if d.startswith("iso_") or d.startswith("_"):
        print(d, c)
