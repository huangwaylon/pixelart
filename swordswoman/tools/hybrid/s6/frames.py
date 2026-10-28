"""S6 r1: every STANDARD TEST SET sprite, composed from hand-authored layers.
Run: .venv/bin/python tools/hybrid/s6/frames.py [names...]"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from compose import *

F = {}


def frame(fn):
    F[fn.__name__] = fn
    return fn


def body(cv, fn, x, y, mirror=False):
    rows = read_body(fn)
    if mirror:
        w = max(len(r) for r in rows)
        rows = [r.ljust(w, ".")[::-1] for r in rows]
    cv.pix(x, y, rows)


def mx(x):  # mirror a cell column about the cell centre (pivot x 64 -> 63.5 axis)
    return 127 - x


@frame
def turn_S(cv):
    body(cv, "body_S.txt", 48, 70)
    ribbon(cv, [(55, 79), (52, 80), (49, 82), (47, 85), (47, 88), (48, 91), (46, 95)], behind=False)
    ribbon(cv, [(72, 79), (75, 80), (78, 82), (80, 85), (80, 88)], behind=False)
    cv.stamp(stamp("head_S"), 51, 44)
    katana_stamp(cv, "katana_idle_2to1", 71, 83, rows=30)
    fist(cv, 74, 88)


@frame
def turn_SE(cv):
    body(cv, "body_SE.txt", 46, 70)
    ribbon(cv, [(56, 79), (53, 80), (50, 82), (48, 85), (48, 88), (49, 91), (47, 94)], behind=False)
    cv.stamp(stamp("head_SE"), 50, 44)
    katana_stamp(cv, "katana_idle_2to1", 69, 82, rows=30)
    fist(cv, 72, 87)


@frame
def turn_E(cv):
    body(cv, "body_E.txt", 40, 72)
    ribbon(cv, [(56, 78), (53, 80), (51, 83), (51, 87), (52, 90), (50, 94)], behind=True)
    ribbon(cv, [(57, 79), (55, 82), (55, 85), (56, 88)], tones=("p", "P"), behind=True)
    cv.stamp(stamp("head_E"), 48, 44)
    katana_stamp(cv, "katana_idle_2to1", 65, 81, rows=30)
    fist(cv, 69, 87)


@frame
def turn_NE(cv):
    body(cv, "body_NE.txt", 40, 72)
    ribbon(cv, [(58, 79), (57, 82), (56, 85), (57, 88), (58, 91), (56, 94)], behind=False)
    ribbon(cv, [(63, 79), (64, 82), (63, 85), (62, 88), (63, 91)], tones=("p", "P"), behind=False)
    cv.stamp(stamp("head_NE"), 50, 44)
    katana_stamp(cv, "katana_idle_2to1", 35, 89, rows=26, flip=True)
    fist(cv, 50, 94)


@frame
def turn_N(cv):
    body(cv, "body_N.txt", 44, 68)
    ribbon(cv, [(60, 76), (59, 79), (58, 82), (59, 85), (60, 88), (58, 92)], behind=False)
    ribbon(cv, [(67, 76), (68, 79), (69, 82), (68, 85), (67, 88), (69, 92)], tones=("p", "P"), behind=False)
    cv.stamp(stamp("head_N"), 51, 44)
    katana_stamp(cv, "katana_idle_2to1", 36, 85, rows=28, flip=True)
    fist(cv, 50, 90)


@frame
def turn_NW(cv):
    body(cv, "body_NE.txt", mx(79), 72, mirror=True)
    ribbon(cv, [(mx(58), 79), (mx(57), 82), (mx(56), 85), (mx(57), 88), (mx(58), 91), (mx(56), 94)], behind=False)
    ribbon(cv, [(mx(63), 79), (mx(64), 82), (mx(63), 85), (mx(62), 88), (mx(63), 91)], tones=("p", "P"), behind=False)
    cv.stamp(stamp("head_NW"), mx(75), 44)
    # her left hand is the screen-left (near) cuff of the mirrored body
    katana_stamp(cv, "katana_idle_2to1", 43, 88, rows=26, flip=True)
    fist(cv, 57, 92)


@frame
def turn_W(cv):
    body(cv, "body_E.txt", mx(79), 72, mirror=True)
    ribbon(cv, [(mx(56), 78), (mx(53), 80), (mx(51), 83), (mx(51), 87), (mx(52), 90), (mx(50), 94)], behind=True)
    cv.stamp(stamp("head_W"), mx(73), 44)
    katana_stamp(cv, "katana_idle_2to1", 44, 92, rows=24, flip=True)
    fist(cv, 61, 96)


@frame
def turn_SW(cv):
    body(cv, "body_SE.txt", mx(81), 70, mirror=True)
    ribbon(cv, [(mx(56), 79), (mx(53), 80), (mx(50), 82), (mx(48), 85), (mx(48), 88), (mx(49), 91), (mx(47), 94)], behind=False)
    cv.stamp(stamp("head_SW"), mx(75), 44)
    katana_stamp(cv, "katana_idle_2to1", 72, 92, rows=24)
    fist(cv, 75, 96)


def foot_stats(g):
    rows = [y for y in range(128) if any(c not in ".wtTpP" for c in g[y])]
    low = rows[-1]
    xs = [x for y in range(low - 2, low + 1) for x in range(128) if g[y][x] not in ".wtTpPK"]
    return low, (min(xs) + max(xs)) / 2 if xs else 64


ANCHOR = {"walk_SE": "turn_SE", "slash_SE": "turn_SE", "jump_E": "turn_E"}


def build(names=None):
    shifts = {}
    order = sorted(F, key=lambda n: 0 if n.startswith("turn") else 1)
    for n in order:
        cv = Canvas(blank())
        F[n](cv)
        low, fx = foot_stats(cv.g)
        if n.startswith("turn"):
            dx = int(round(64 - fx))
            shifts[n] = dx
        else:
            dx = shifts.get(ANCHOR.get(n.rsplit("_", 1)[0], ""), 0)
        dy = 104 - low
        if names and n not in names:
            continue
        g = np.full((128, 128), ".", "<U1")
        for y in range(128):
            for x in range(128):
                if cv.g[y, x] != "." and 0 <= y + dy < 128 and 0 <= x + dx < 128:
                    g[y + dy, x + dx] = cv.g[y, x]
        cv.g = g
        save(n, cv)



# ---------------------------------------------------------------- WALK SE (contact, down, passing, up)
WALK_LEGS = {
    # legs anchored to the ground (cells 52..71), first row = 105 - len + 1
    0: [".....KsmK.KsmK......",
        "....KsmK...KsmK.....",
        "...KsmK.....KsmK....",
        "...KsmK......KsmK...",
        "..KddK.......KsmK...",
        "..KdK.......KKddddK.",
        "..KK........KKKKKK.."],
    1: ["....KsmK..KssK......",
        "...KsmK...KsmmK.....",
        "..KmmK.....KsmK.....",
        "..KdK.....KKdddK....",
        "..KK......KKKKKK...."],
    2: ["......KsmKsmK.......",
        "......KsmKsmK.......",
        ".......KsmmsmK......",
        ".......KKsmKsmK.....",
        "........KddKsmK.....",
        "........KKKKsmK.....",
        "...........KddddK..."],
    3: ["......KsmKKsmK......",
        "......KsmKKsmK......",
        "......KsmKKsmK......",
        "......KsmKKsmK......",
        "......KsmKKsmK......",
        ".......KsmKKsmK.....",
        ".......KdKKKdK......",
        ".......KdK.KdK......",
        ".......KK..KK......."],
}
WALK = {  # body dy, head dy, bow dy (vs head), free-cuff dx, sword (dx,dy), tail dy, ribbon tip flutter
    0: dict(b=1, h=0, bow=0, cuff=2, sw=(-1, 1), tail=0, rib=[(52, 81), (49, 83), (47, 86), (46, 89), (44, 92)]),
    1: dict(b=3, h=3, bow=-1, cuff=1, sw=(0, 3), tail=1, rib=[(52, 82), (49, 85), (48, 88), (46, 91), (45, 95)]),
    2: dict(b=1, h=2, bow=1, cuff=-2, sw=(1, 1), tail=-2, rib=[(52, 80), (49, 82), (46, 84), (45, 87), (43, 89)]),
    3: dict(b=-1, h=0, bow=1, cuff=-1, sw=(0, -1), tail=-1, rib=[(52, 79), (49, 81), (47, 84), (45, 86), (44, 89)]),
}


def walk_key(cv, k):
    p = WALK[k]
    b = p["b"]
    body(cv, "body_SE.txt", 46, 70 + b)
    # legs: clear the turn legs, draw the key legs anchored on the ground
    erase(cv, 53, 98 + b, 72, 110)
    legs = WALK_LEGS[k]
    cv.pix(52, 105 - len(legs) + 1, legs)
    # skirt back tail (cells 46..50) lifts after the down frame
    if p["tail"]:
        shift_region(cv, 46, 92 + b, 49, 104, 0, p["tail"])
    # free arm (big sleeve) cuff + hand swing opposite the legs
    if p["cuff"]:
        shift_region(cv, 47, 95 + b, 54, 101 + b, p["cuff"], 0)
    if k == 1:  # down: skirt bell squashes wider 1 px on the front side
        for y in range(92 + b, 97 + b):
            row = "".join(cv.g[y, 56:76])
            i = row.rfind("K")
            if i > 0:
                cv.put(56 + i + 1, y, "K")
                cv.put(56 + i, y, "r")
    ribbon(cv, [(56, 79 + b)] + [(x, y + b) for x, y in p["rib"]], behind=False)
    head(cv, "SE", 50, 44 + p["h"], bow_dy=p["bow"])
    sx, sy = p["sw"]
    katana_stamp(cv, "katana_idle_2to1", 69 + sx, 82 + sy, rows=30)
    fist(cv, 72 + sx, 87 + sy)


for _k in range(4):
    F[f"walk_SE_k{_k}"] = (lambda kk: (lambda cv: walk_key(cv, kk)))(_k)


# ---------------------------------------------------------------- SLASH SE
import subprocess


def smear_op(cv, op):
    """run one tools/hybrid/draw.py smear/streak/echo op on the canvas (exact pixels, hard alpha)."""
    import tempfile
    t = tempfile.mktemp(suffix=".png")
    o = tempfile.mktemp(suffix=".png")
    save_rgba(to_rgba(cv.g), t)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools/hybrid/draw.py"), t, "--out", o, op],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr)
    cv.g = np.array([list(rw) for rw in rgba_to_chars(load_rgba(o))])
    return r.stdout


def blade(cv, hands, tip, guard_t=2, hook=1, fist_at=None, two_hand=True, behind=False):
    """katana from the hands: pommel 6 px behind the guard; same parts as the lock stamp."""
    hx, hy = hands
    tx, ty = tip
    L = math.hypot(tx - hx, ty - hy)
    ux, uy = (tx - hx) / L, (ty - hy) / L
    gx, gy = hx + ux * guard_t, hy + uy * guard_t
    pe = (int(round(hx - ux * 4)), int(round(hy - uy * 4)))
    katana(cv, pe, (gx, gy), (tx, ty), hook_side=hook, behind=behind)
    if fist_at is not False:
        fx, fy = fist_at or (int(round(hx - ux)), int(round(hy - uy)))
        fist(cv, fx, fy)


@frame
def slash_SE_k2(cv):
    # ribbons whip: root already reversing (to the right), tips still trailing left: S-curve
    body(cv, "slash_k2.txt", 40, 72)
    ribbon(cv, [(58, 80), (55, 78), (51, 79), (47, 81), (44, 80), (41, 82)], behind=False)
    ribbon(cv, [(58, 81), (55, 82), (52, 84), (49, 85), (46, 85)], tones=("p", "P"), behind=False)
    head(cv, "SE", 54, 49)
    # thin sliver: the last 35 % of the cut-plane arc behind the crisp blade
    smear_op(cv, "smear 74,88 29,14 -318 -354 2 tones=P,p taper=lead grow=in")
    blade(cv, (81, 88), (103, 90), fist_at=False)
    # hit spark (1 frame): steel_2 star at the contact point
    cv.pix(101, 86, ["...w...", "...w...", "..PwP..", "wwwPwww", "..PwP..", "...w...", "...w..."])


@frame
def slash_SE_k0(cv):
    # secondaries trail to her left (screen right): ribbons, skirt tail
    body(cv, "slash_k0.txt", 40, 72)
    ribbon(cv, [(70, 80), (74, 81), (78, 83), (82, 82), (86, 84), (89, 83)], behind=False)
    ribbon(cv, [(71, 81), (75, 84), (78, 87), (82, 87)], tones=("p", "P"), behind=False)
    blade(cv, (47, 80), (31, 62), fist_at=(46, 80))
    head(cv, "SE", 48, 49, bow_dx=1)


@frame
def slash_SE_k1(cv):
    # secondaries still point where the body WAS (screen left/up)
    body(cv, "slash_k1.txt", 40, 72)
    ribbon(cv, [(56, 80), (52, 78), (48, 79), (44, 77), (40, 78)], behind=False)
    ribbon(cv, [(56, 81), (52, 82), (48, 83), (44, 82)], tones=("p", "P"), behind=False)
    # full blade-arc smear: coil tip -> past the blade (front pass, over the body, clear of the face)
    smear_op(cv, "smear 74,88 30,15 -165 -302 6 tones=w,P,p taper=lead grow=in over")
    # stretched sleeve in-between: arms + cuffs smeared along the swing into one red shape
    smear_op(cv, "streak 54,83 70,92 4 tones=C,R over")
    # hand echo 4 px back along the arc
    cv.pix(65, 90, ["pp", "pp"])
    blade(cv, (72, 93), (89, 101), fist_at=(71, 92))
    head(cv, "SE", 51, 46, bow_dy=1, bow_dx=-1)


@frame
def slash_SE_k3(cv):
    # secondaries overshoot past rest to the front-left (screen right/down), 6-10 px
    ribbon(cv, [(72, 79), (76, 84), (80, 88), (84, 90), (88, 92), (91, 91)], behind=True)
    ribbon(cv, [(73, 80), (78, 87), (82, 92), (86, 95)], tones=("p", "P"), behind=True)
    body(cv, "slash_k3.txt", 40, 72)
    # arc-tail wisps (pink_0, <= 3 px) behind the carried-past blade
    head(cv, "SE", 55, 46, bow_dy=-1, bow_dx=1)
    # both arms carried up-right past the target: sleeve + flared cuff (hand-placed)
    cv.pix(66, 80, ["..........KKKK.",
                    ".....KKKKKRRRsSK",
                    "....KRRRRRRRRRmK",
                    "...KRRRRRRRrrKK.",
                    "...KRRRrrrrKK...",
                    "..KrrRRrrKK.....",
                    "..KvvrrvK.......",
                    "...KKvvK........",
                    ".....KK........."])
    cv.pix(99, 69, ["p..", ".p.", "..p"])
    blade(cv, (81, 81), (100, 72), fist_at=False)


# ---------------------------------------------------------------- JUMP E (crouch, apex, land)
@frame
def jump_E_crouch(cv):
    body(cv, "jump_crouch.txt", 36, 78)
    # ribbons still falling from the previous state (lag 1): hang down behind
    ribbon(cv, [(57, 84), (53, 86), (51, 90), (52, 93), (50, 96)], behind=True)
    ribbon(cv, [(57, 85), (55, 89), (55, 92)], tones=("p", "P"), behind=True)
    head(cv, "E", 50, 50)
    # arms swung back: sword trails back-low
    blade(cv, (47, 93), (30, 101), fist_at=(46, 92))


@frame
def jump_E_apex(cv):
    body(cv, "jump_apex.txt", 36, 70)
    # cloth floats UP: ribbons lift and stream back above the shoulders
    ribbon(cv, [(59, 77), (55, 74), (51, 73), (47, 70), (43, 70), (40, 67)], behind=False)
    ribbon(cv, [(59, 78), (55, 77), (51, 77), (47, 75), (44, 75)], tones=("p", "P"), behind=False)
    head(cv, "E", 49, 40, bow_dy=-1, bow_dx=-1)
    # refs/3: sword hand raised in front, long blade down-back as the counter-diagonal
    blade(cv, (70, 79), (50, 105), fist_at=(69, 79))
    # take-off motion lines: 2 pink_0 streaks, 4-5 px, under the trailing foot (clear of the toes)
    for x, y0, n in ((59, 100, 5), (56, 97, 4)):
        for k in range(n):
            cv.put(x, y0 + k, "p", behind=True)


@frame
def jump_E_land(cv):
    body(cv, "jump_land.txt", 34, 80)
    # ribbons drop onto the shoulders
    ribbon(cv, [(55, 86), (52, 87), (49, 89), (48, 92)], behind=True)
    head(cv, "E", 49, 51, bow_dy=1, bow_dx=1)
    # arms down-forward for balance; blade forward-down
    blade(cv, (66, 92), (84, 102), fist_at=(65, 91))
    # dust puffs at the feet (steel_1 -> steel_0)
    cv.pix(46, 101, [".T.", "TtT"], behind=True)
    cv.pix(76, 101, [".TT", "Tt."], behind=True)
    cv.pix(43, 103, ["T"], behind=True)
    cv.pix(80, 103, ["t"], behind=True)


if __name__ == "__main__":  # noqa
    build(sys.argv[1:] or None)
    order = [n for n in NAMES if n in F]
    grid_preview([n for n in order if n.startswith("turn")], os.path.join(OUT, "work", "turn_preview.png"))
    grid_preview(["turn_SE"] + [f"walk_SE_k{k}" for k in range(4)], os.path.join(OUT, "work", "walk_preview.png"), cols=5)
    grid_preview(["turn_SE"] + [f"slash_SE_k{k}" for k in range(4) if f"slash_SE_k{k}" in F], os.path.join(OUT, "work", "slash_preview.png"), cols=5, crop=(24, 36, 116, 112))
    grid_preview(["turn_E", "jump_E_crouch", "jump_E_apex", "jump_E_land"], os.path.join(OUT, "work", "jump_preview.png"), cols=4, crop=(24, 30, 104, 110))
