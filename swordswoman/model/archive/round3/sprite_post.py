"""Sprite post pass for the model preview cells (stand-in for the pixel pipeline), round 3.

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


def clean(a, ids, stats):
    op = a[..., 3] == 255
    g = lambda n: (ids == GID[n]) & op
    hair = g("hair") | g("sheen")
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
    # ---- b. pink rim on hair + bow: right contour + top contour on the right half, 1 px
    head = hair | bow
    a[head & eq(a, C["pink"][0])] = np.append(C["hair"][1], 255)     # material rim leftovers
    tr = ~op
    right = head & shift(tr, 0, 1, True)
    top = head & shift(tr, -1, 0, True)
    xs = np.where(head.any(axis=0))[0]
    if len(xs):
        cx = (xs.min() + xs.max()) / 2.0
        X = np.arange(a.shape[1])[None, :].repeat(a.shape[0], 0)
        rim = right | (top & (X >= cx))
        ys_ = np.where(head.any(axis=1))[0]
        Y = np.arange(a.shape[0])[:, None].repeat(a.shape[1], 1)
        rim &= Y <= ys_.min() + 0.75 * (ys_.max() - ys_.min())     # not down the jaw strands
        rim = drop_small(rim, 3)
        a[rim] = np.append(C["pink"][0], 255)
        stats["rim_px"] = int(rim.sum())
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
    op = a[..., 3] == 255
    blade = g("sword") & op & eq(a, C["steel"][2])
    if blade.any():
        lit = blade & ~shift(blade, -1, 0)          # pixel above is not blade -> top edge
        a[blade] = np.append(C["steel"][1], 255)
        a[lit] = np.append(C["steel"][2], 255)
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


def outline(a):
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
    st = {}
    if ids is not None:
        a = clean(a, ids, st)
    STATS[name] = st
    Image.fromarray(outline(a), "RGBA").save(os.path.join(D, name))


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
        stand = tag.startswith("iso_") or tag.startswith("anim_")
        c["foot_pivot_ok"] = bool(len(ys) and abs(int(ys.max()) - 104) <= 3) if stand else None
    if ids is not None:
        g = lambda n: ids == GID[n]
        headm = g("hair") | g("sheen") | g("bow") | g("face")
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
        rim = eq(fin, C["pink"][0]) & (g("hair") | g("sheen") | g("bow"))
        lab, sz = components(rim)
        c["rim_orphans"] = int((sz[1:] < 3).sum()) if len(sz) > 1 else 0
        st = (g("corset") | g("buckles")) & eq(fin, C["steel"][1])
        c["corset_steel_px"] = int(st.sum())
        sh = g("sheen") & eq(fin, C["hair"][2])
        c["sheen_components"] = int(len(components(sh)[1]) - 1)
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
    violet_outside_ornament_total=sum(v.get("violet_outside_ornament", 0) for k, v in checks.items()
                                      if not k.startswith("_")),
)
json.dump(checks, open(os.path.join(D, "checks.json"), "w"), indent=1)
for d, c in checks.items():
    if d.startswith("iso_") or d.startswith("_"):
        print(d, c)
