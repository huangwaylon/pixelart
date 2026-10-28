"""S4_textured3d r1 POLISH pass (Claude hand pixel edits).  Reads r1/sprite, writes r1/polished.
Every edit is exact pixels with a reason (logged to polished/polish_log.txt)."""
import os, shutil, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pl
import headfix
import clean as CL
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "s4"))
import fx as FX  # noqa

R = "hybrid/S4_textured3d/r1"
SRC, OUT = f"{R}/sprite", f"{R}/polished"
LOG = {}


def note(n, s):
    LOG.setdefault(n, []).append(s)


def dir_of(n):
    return {"walk": "SE", "slash": "SE", "jump": "E"}.get(n.split("_")[0], n.split("_")[-1])


# ---------------------------------------------------------------- per-frame recipes
BOW = {  # extra bow-cel lag / overshoot on top of the generator's offsets (dx, dy)
    "walk_SE_k0": (0, -1, "contact: body falling -> bow trails up"),
    "walk_SE_k1": (0, -1, "down: bow still rising relative to head (lag)"),
    "walk_SE_k3": (0, 1, "up: bow lags low as the body rises"),
    "slash_SE_k1": (-1, -1, "fast swing right: bow drags back-left"),
    "slash_SE_k2": (2, 1, "hit-stop: body stops, bow overshoots forward"),
    "slash_SE_k3": (-1, -1, "settle back toward rest"),
    "jump_E_crouch": (0, -1, "squash: bow lags high as the head sinks"),
    "jump_E_apex": (-1, 1, "rise: bow trails down-back"),
    "jump_E_land": (1, 1, "landing: bow overshoots down-forward"),
}


def slash_k0(a, n):
    # anticipation glint on the raised blade tip (the 'ting' before the cut)
    st = pl.group(a, "w")
    ys, xs = np.nonzero(st)
    i = np.argmin(xs + ys)                      # up-left-most blade px = tip
    x, y = xs[i], ys[i]
    gx, gy = x - 3, y - 3          # 4-point sparkle floating just off the tip
    for dx, dy, c in ((0, 0, "w"), (-1, 0, "w"), (1, 0, "w"), (0, -1, "w"), (0, 1, "w"),
                      (-2, 0, "P"), (2, 0, "P"), (0, -2, "P"), (0, 2, "P"), (0, -3, "p"), (-3, 0, "p")):
        pl.put(a, gx + dx, gy + dy, c, behind=True)
    note(n, f"tip sparkle at {x - 3},{y - 3} (anticipation read)")
    return a


def slash_k1(a, n):
    # second, thinner concentric arc outside the main crescent (multiple-arc smear) + speed ticks
    L = FX.arc_layer(75.0, 86.0, 35.0, 18.0, -190, -330, 2, "P,p", taper="both", grow="out")
    FX.composite(a, L, "behind")
    L = FX.arc_layer(75.0, 86.0, 27.0, 12.5, -150, -250, 1, "p", taper="none", grow="in")
    FX.composite(a, L, "behind")
    note(n, "outer double-arc (P,p, 2px) + inner 1px trailing arc: multiple-arc blade smear")
    return a


def slash_k2(a, n):
    # strengthen the hit-stop residual: thicker decaying crescent ending at the tip + impact burst
    blade = pl.group(a, "w")
    ys, xs = np.nonzero(blade)
    i = np.argmax(xs)
    tx, ty = int(xs[i]), int(ys[i])
    # remove the old 1px sliver (pink below the tip, outside the body)
    pk = pl.group(a, "pP")
    for y, x in zip(*np.nonzero(pk)):
        if x >= 88 and y >= 88:
            a[y, x] = pl.T(".")
    L = FX.arc_layer(75.0, 86.0, 31.0, 15.0, -275, -364, 4, "w,P,p", taper="lead", grow="in")
    FX.composite(a, L, "behind")
    # impact burst: 4 radial ticks around the spark + bigger star
    sx, sy = tx + 3, ty - 2
    for (dx, dy) in ((1, -1), (1, 1), (-1, -1), (-1, 1)):
        for k in (3, 4):
            pl.put(a, sx + dx * k, sy + dy * k, "P" if k == 3 else "p", behind=True)
    for k in range(1, 6):
        for dx, dy in ((k, 0), (0, -k), (0, k)):
            pl.put(a, sx + dx, sy + dy, "w" if k <= 3 else "P", behind=(k > 3))
    note(n, f"residual crescent 4px w/P/p into tip {tx},{ty}; impact star r5 + 4 diagonal ticks at {sx},{sy}")
    return a


def slash_k3(a, n):
    # follow-through: fading dotted remnant of the arc (breaks up = dissipating) behind the blade
    L = FX.arc_layer(75.0, 86.0, 31.0, 15.0, -300, -356, 2, "p,p", taper="lead", grow="in")
    for i, k in enumerate(sorted(L.px)):
        if (k[0] // 2) % 2 == 0:
            del L.px[k]
    FX.composite(a, L, "behind")
    note(n, "dissipating dotted arc remnant (p) along the cut path")
    return a


# hand-typed crouched legs (E facing): front thigh forward out of the skirt, shin down, strappy heel.
LEG_CROUCH = [  # x0=64, y0=97  squat: thigh forward out of the skirt, round knee, shin, strappy heel
    "__KKKKKKK....",
    "__ssSSSssK...",
    "__sssssssSK..",
    "__mmssssssK..",
    "__KmmmmssmK..",
    "___KKKKssmK..",
    "______KssmK..",
    "______KssmK..",
    "______KdsdKK.",
    "_____KdKddddK",
    "_____KK.KKKKK",
]
BACK_CROUCH = [  # far leg (shaded skin_0), x0=63, y0=103
    "KmmK",
    "KmmK",
    "KdmK",
    "KdddK",
    "KK.KK",
]
GROUND = 107


def dust_puff(a, x, y, side, big=True):
    """2-tone cloud puffs kicked out from the feet along the ground (behind the body)."""
    pf = (["_ww_", "wwTw", "TTTT"] if big else ["ww", "TT"])
    for j, r in enumerate(pf):
        for i, c in enumerate(r):
            if c != "_":
                X = x + (i if side > 0 else -i)
                pl.put(a, X, y - len(pf) + 1 + j, c, behind=True)


def jump_crouch(a, n):
    b = a.copy()
    pl.stamp(a, 63, 103, BACK_CROUCH)
    pl.stamp(a, 64, 97, LEG_CROUCH)
    a = pl.outline_new(a, b, max_y=GROUND)
    dust_puff(a, 46, GROUND, -1, big=False)
    dust_puff(a, 78, GROUND, 1, big=False)
    note(n, "hand-typed squat legs (thigh out of skirt, knee, shin, strappy heel with arch) + far shin; small push-off dust")
    return a


LEG_LAND = [  # x0=64, y0=101  planted lunge: thigh forward, knee, heel planted ahead
    "__KKKKKKKK....",
    "__sSSssssssK..",
    "__msssssssssK.",
    "__KmmmmmmssmK.",
    "___KKKKKKdsdKK",
    "________KdKdddK",
    "________KK.KKKK",
]


def jump_land(a, n):
    b = a.copy()
    pl.stamp(a, 64, 101, LEG_LAND)
    a = pl.outline_new(a, b, max_y=GROUND)
    for side, x0 in ((-1, 45), (1, 81)):
        dust_puff(a, x0, GROUND, side, big=True)
        dust_puff(a, x0 + side * 5, GROUND - 2, side, big=False)
    note(n, "hand-typed planted lunge leg + heel; two-tone landing dust clouds both sides (big + small, rising outward)")
    return a


def jump_apex(a, n):
    # rising speed lines under the feet (vertical motion smear), behind
    ys, xs = np.nonzero(a[..., 3])
    by = ys.max()
    feet = xs[ys >= by - 2]
    cx = int(np.median(feet))
    for i, (dx, ln) in enumerate(((-6, 6), (-2, 9), (2, 7), (6, 5))):
        for t in range(ln):
            pl.put(a, cx + dx, by + 2 + t, "P" if t < 2 else "p", behind=True)
    note(n, f"4 vertical speed lines under the feet (stretch read), x~{cx}")
    return a


FX_FN = {"slash_SE_k0": slash_k0, "slash_SE_k1": slash_k1, "slash_SE_k2": slash_k2, "slash_SE_k3": slash_k3,
         "jump_E_crouch": jump_crouch, "jump_E_land": jump_land, "jump_E_apex": jump_apex}


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".png") or fn.endswith("_hires.png"):
            continue
        n = fn[:-4]
        a = pl.load(f"{SRC}/{fn}")
        d = dir_of(n)
        pre = a.copy()
        a, info = headfix.apply(a, d)
        meta[n] = info
        if info[3]:
            note(n, f"bun/skull crease ({info[3]} px, stamp at {info[0]},{info[1]})")
        if n in BOW:
            dx, dy, why = BOW[n]
            a = pl.shift_bow(a, dx, dy, why)
            note(n, f"bow ({dx},{dy}): {why}")
        if n in FX_FN:
            a = FX_FN[n](a, n)
        # protect: head stamp footprint, every px the polish touched, sword
        st = pl.load(headfix.ST % d)
        ox, oy = info[0], info[1]
        prot = np.zeros((128, 128), bool)
        prot[oy:oy + st.shape[0], ox:ox + st.shape[1]] |= st[..., 3] > 0
        prot |= (a != pre).any(-1)
        a, cs = CL.clean(a, prot)
        if cs["orphans"] or cs["spurs"]:
            note(n, f"cleanup: {cs['orphans']} cloth/hair orphans merged, {cs['spurs']} spurs removed")
        pl.save(a, f"{OUT}/{fn}")
        h = f"{SRC}/{n}_hires.png"
        if os.path.exists(h):
            shutil.copy(h, f"{OUT}/{n}_hires.png")
    with open(f"{OUT}/polish_log.txt", "w") as f:
        for n, v in LOG.items():
            f.write(n + "\n" + "".join("  - " + s + "\n" for s in v))
    json.dump(meta, open(f"{OUT}/_stamp_loc.json", "w"))
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
