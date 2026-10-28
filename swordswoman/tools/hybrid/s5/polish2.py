"""S5 r1 POLISH pass (Claude hand pixel artist, exact pixels).  Reads r1/sprite/<name>.png (pre-polish set, kept),
writes r1/polished/<name>.png (+ _4x, _src).  Every edit carries a reason; see EDITS log printed per sprite.

  .venv/bin/python tools/hybrid/s5/polish2.py [names]
"""
import sys, os, math, shutil, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *          # noqa
sys.path.insert(0, f"{ROOT}/tools/hybrid")
import draw as D               # noqa
from norm import steel_layer, remove_orphans   # noqa

SRC = f"{OUT}/sprite"; DST = f"{OUT}/polished"
INV = {}
for k, v in TRGB.items(): INV.setdefault(v, k)
INV[TRGB["outline"]] = "outline"
CH = {"K": "outline", "w": "steel_2", "T": "steel_1", "t": "steel_0", "S": "skin_2", "s": "skin_1", "m": "skin_0",
      "P": "pink_1", "p": "pink_0", "C": "red_3", "R": "red_2", "r": "red_1", "v": "red_0", "l": "leather_1"}
LOG = {}

def tone(a, x, y):
    if not (0 <= x < 128 and 0 <= y < 128) or not a[y, x, 3]: return None
    return INV.get(tuple(a[y, x, :3]))

def put(a, x, y, t):
    if t is None or t == ".": a[y, x] = 0; return
    a[y, x, :3] = TRGB[CH.get(t, t)]; a[y, x, 3] = 255

def note(name, msg): LOG.setdefault(name, []).append(msg)

# ------------------------------------------------------------------ generic cleanup
def stray_steel_to_skin(a, name):
    """steel_2/steel_1 pixels that are not part of the blade but touch skin are Gemini highlight misreads -> skin."""
    st = steel_layer(a); n = 0
    for y in range(1, 127):
        for x in range(1, 127):
            t = tone(a, x, y)
            if t not in ("steel_2", "steel_1", "steel_0"): continue
            nb = [tone(a, x+dx, y+dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            skin = sum(1 for q in nb if q and q.startswith("skin"))
            steel = sum(1 for q in nb if q and q.startswith("steel"))
            if (not st[y, x] or skin >= 2) and skin >= 1 and steel <= 1:
                put(a, x, y, "skin_2" if t == "steel_2" else "skin_1"); n += 1
    if n: note(name, f"{n} stray steel px on legs/arms -> skin (highlight misread)")
    return a

def blade_mask(a, region):
    """blade steel inside region + the outline px that only border the blade (side outline)."""
    st = steel_layer(a); x0, y0, x1, y1 = region
    m = np.zeros_like(st); m[y0:y1, x0:x1] = st[y0:y1, x0:x1]
    side = np.zeros_like(st)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if tone(a, x, y) != "outline": continue
            nb = [(x+dx, y+dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]
            if any(m[yy, xx] for xx, yy in nb if 0 <= xx < 128 and 0 <= yy < 128):
                others = [tone(a, xx, yy) for xx, yy in nb]
                if not any(o and o != "outline" and not o.startswith("steel") for o in others): side[y, x] = True
    return m | side

def clear_loose_outline(a, region):
    """remove outline px left floating (no non-outline opaque 8-neighbour) after a part was erased."""
    x0, y0, x1, y1 = region
    for _ in range(3):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if tone(a, x, y) == "outline":
                    nb = [tone(a, x+dx, y+dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]
                    if not any(q and q != "outline" for q in nb): a[y, x] = 0

def draw_blade(a, x0, y0, ang, L, behind=True):
    """2 px katana blade from (x0,y0) at screen angle ang (deg, 0=+x, 90=down) for L px: core steel_2,
    shade steel_1 on the lower/right side, outline both sides, tapered 1 px tip."""
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    x1, y1 = int(round(x0 + ux * L)), int(round(y0 + uy * L))
    core = D.pixel_perfect(D.bresenham(x0, y0, x1, y1))
    steep = abs(uy) >= abs(ux)
    nx, ny = (1, 0) if steep else (0, 1)          # shade side
    def p(x, y, t):
        if 0 <= x < 128 and 0 <= y < 128 and (not behind or not a[y, x, 3] or tone(a, x, y) in ("outline",)):
            put(a, x, y, t)
    for i, (x, y) in enumerate(core):
        tip = i >= len(core) - 2
        p(x, y, "steel_2")
        if not tip:
            p(x + nx, y + ny, "steel_1")
            p(x + 2 * nx, y + 2 * ny, "outline")
        else:
            p(x + nx, y + ny, "outline")
        p(x - nx, y - ny, "outline")
    xe, ye = core[-1]
    p(xe + int(round(ux)), ye + int(round(uy)), "outline")
    return (x1, y1)

def layer(a, ops, front=None):
    """draw ops on an empty layer; composite behind the figure (front=None) or everywhere where front(x,y)."""
    L = np.zeros_like(a); cv = D.Canvas(L)
    for op in ops: D.run_op(cv, op, ".")
    for y, x in zip(*np.nonzero(L[..., 3] > 0)):
        if not a[y, x, 3] or (front and front(x, y)): a[y, x] = L[y, x]
    return a

def squash_rows(a, rows, cols, dx_cols=1):
    """squash: delete body rows `rows` (everything above drops down), widen by duplicating columns `cols`
    symmetric about their centre (left half shifts left, right half right) -> volume kept."""
    b = a.copy()
    for r in sorted(rows, reverse=True):
        b[1:r+1] = b[0:r].copy(); b[0] = 0
    c = b.copy()
    if cols is not None:
        c[:, :cols] = b[:, 1:cols+1]          # left half moves 1 px left, column `cols` doubles
    return c

# ------------------------------------------------------------------ per-sprite polish
def p_turn_NE(a, n):
    # short blade with a broken, offset side outline -> redraw a full-length blade from under the skirt tail
    m = blade_mask(a, (40, 96, 58, 112)); a[m] = 0
    clear_loose_outline(a, (40, 96, 58, 112))
    tip = draw_blade(a, 52, 97, 112, 22)
    note(n, f"blade redrawn full length 22 px at 112 deg (was 13 px, broken outline) tip {tip}")
    # odd skirt-tail flap: trim its far-left point (x<44) so the tail reads as a flare, not a wing
    for y in range(85, 92):
        for x in range(36, 44): a[y, x] = 0
    for y in range(85, 92):
        xs = [x for x in range(44, 60) if a[y, x, 3]]
        if xs: put(a, xs[0], y, "outline")
    note(n, "skirt-tail flap tip trimmed 4 px, re-outlined")
    return a

def p_turn_W(a, n):
    # W had almost no scarf ribbons while E has big ones: mirror E's ribbon tails behind her back (x' = 124 - x)
    e = load(f"{SRC}/turn_E.png"); k = 0
    for y in range(78, 99):
        for x in range(40, 52):
            t = tone(e, x, y)
            if t in ("pink_0", "pink_1", "red_3", "outline"):
                X = 124 - x
                if 0 <= X < 128 and not a[y, X, 3]: a[y, X] = e[y, x]; k += 1
    # drop outline px that ended up isolated
    for y in range(78, 99):
        for X in range(70, 90):
            if tone(a, X, y) == "outline":
                nb = [tone(a, X+dx, y+dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]
                if not any(q and q != "outline" for q in nb): a[y, X] = 0
    note(n, f"scarf ribbon tails added behind her back, mirrored from turn_E ({k} px) -> E/W costume match")
    return a

WALK_ANG = {"walk_SE_k0": 30, "walk_SE_k1": 39, "walk_SE_k2": 45, "walk_SE_k3": 36}   # pendulum, lags the bob
def p_walk(a, n):
    m = blade_mask(a, (76, 92, 110, 110))
    ys, xs = np.nonzero(m & steel_layer(a))
    top = min((y, x) for y, x in zip(ys, xs) if x >= 78)             # blade root just below the guard
    a[m] = 0
    clear_loose_outline(a, (76, 91, 110, 110))
    L = 19
    tip = draw_blade(a, int(top[1]), int(top[0]), WALK_ANG[n], L)
    note(n, f"blade redrawn at {WALK_ANG[n]} deg from root {top[1]},{top[0]} (sword swing: pendulum lagging the bob) tip {tip}")
    return a

def p_slash_k1(a, n):
    # the front half of the arc smear covered the whole lower body: keep the 2 leading rows (core + edge) over
    # the legs, restore the body underneath from the pre-smear base so the legs read through the cut.
    base = load(f"{OUT}/work/legs_slash_SE_k1.png") if os.path.exists(f"{OUT}/work/legs_slash_SE_k1.png") else load(f"{OUT}/work/norm_slash_SE_k1.png")
    sm = ("steel_2", "pink_1", "pink_0"); k = 0
    for x in range(44, 84):
        col = [y for y in range(88, 106) if tone(a, x, y) in sm and base[y, x, 3]]
        keep = set(sorted(col)[-2:])
        for y in col:
            if y not in keep and tone(base, x, y) not in sm:
                a[y, x] = base[y, x]; k += 1
    note(n, f"smear thinned over the legs: {k} px restored to body, 2 px lead band kept in front")
    # stronger speed: 3 motion lines trailing the sword hand (fast-swing read) + a second, fainter outer arc
    a = layer(a, ["smear 74,86 44,17 -175 -320 2 tones=p taper=both grow=out"])
    note(n, "faint outer arc echo (pink_0) for a double-crescent smear")
    return a

def p_slash_k2(a, n):
    # hit-stop: radial impact ticks around the spark star (106,84)
    for (x0, y0, x1, y1) in ((111, 79, 113, 77), (111, 89, 113, 91), (101, 78, 100, 76), (101, 90, 100, 92), (114, 84, 116, 84)):
        D.run_op(D.Canvas(a), f"line {x0},{y0} {x1},{y1} w", ".")
    note(n, "5 impact ticks around the spark (hit-stop read)")
    return a

def p_jump_crouch(a, n):
    # crouch = anticipation: weight pressed into the ground -> small pressure dust curling out at the toes
    ys, xs = np.nonzero(a[100:107, :, 3]); x0, x1 = xs.min(), xs.max()
    for (x, y, t) in ((x0-2, 104, "steel_1"), (x0-3, 103, "steel_1"), (x1+2, 104, "steel_1"), (x1+3, 103, "skin_2")):
        if not a[y, x, 3]: put(a, x, y, t)
    note(n, "toe pressure dust")
    return a

def p_jump_apex(a, n):
    # take-off speed lines under the body (rising) + open shout mouth
    a = layer(a, ["speed 58,104 0,1 1 7 0 w", "speed 64,100 0,1 1 9 0 w", "speed 70,99 0,1 1 6 0 T", "speed 52,96 0,1 1 6 0 T"])
    for (x, y, t) in ((71, 62, "K"), (72, 62, "K"), (71, 63, "C"), (72, 63, "K")): put(a, x, y, t)
    note(n, "4 vertical take-off speed lines below; open shout mouth (2x2) on the E profile")
    return a

def p_jump_land(a, n):
    # stronger landing squash: drop 2 skirt rows (head comes down 2 px), widen 2 cols at the body centre
    ys, xs = np.nonzero(a[..., 3]); cx = int(np.median(xs[ys > 80]))
    a = squash_rows(a, [88, 92], cx, 1)
    a = squash_rows(a, [], cx + 1, 1)
    # impact lines out along the ground
    ys, xs = np.nonzero(a[98:107, :, 3]); x0, x1 = xs.min(), xs.max()
    a = layer(a, [f"line {x0-4},106 {x0-9},106 T", f"line {x0-3},103 {x0-7},101 T", f"line {x1+4},106 {x1+9},106 T", f"line {x1+3},103 {x1+7},101 T"])
    note(n, "landing squash pushed: -2 rows / +2 cols (volume kept); ground impact lines both sides")
    return a

FIX = {"turn_NE": p_turn_NE, "turn_W": p_turn_W, "slash_SE_k1": p_slash_k1, "slash_SE_k2": p_slash_k2,
       "jump_E_crouch": p_jump_crouch, "jump_E_apex": p_jump_apex, "jump_E_land": p_jump_land}
for k in WALK_ANG: FIX[k] = p_walk

def polish(name):
    a = load(f"{SRC}/{name}.png")
    a = stray_steel_to_skin(a, name)
    if name in FIX: a = FIX[name](a, name)
    import polish as P1
    P1.INV[TRGB["outline"]] = "outline"          # P1's inverse map aliased the outline colour to leather_0
    b = P1.merge_orphans(a, name, 2)
    k = int((b != a).any(-1).sum())
    if k: note(name, f"{k} orphan px merged into their dominant neighbour tone (head stamp, steel, eyes, pink exempt)")
    a = b
    a = remove_orphans(a, 3)
    return a

if __name__ == "__main__":
    os.makedirs(DST, exist_ok=True)
    for nm in (sys.argv[1:] or NAMES):
        a = polish(nm)
        save(a, f"{DST}/{nm}.png")
        Image.fromarray(a).resize((512, 512), Image.NEAREST).save(f"{DST}/{nm}_4x.png")
        if os.path.exists(f"{SRC}/{nm}_src.png"): shutil.copy(f"{SRC}/{nm}_src.png", f"{DST}/{nm}_src.png")
        print(nm, "|", "; ".join(LOG.get(nm, ["(clean only)"])))
    json.dump(LOG, open(f"{DST}/edits_log.json", "w"), indent=1)
