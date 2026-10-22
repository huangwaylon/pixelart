"""Author data/variants/S4_hd.json: S4_halfup_bow on the HD SDF model (r12 M1: hair + bow).

    .venv/bin/python pipeline/tools/make_s4_hd.py

Geometry is in head-bone space (S4: head_r 8.4, head centre (0, 7.14, 0.5); hair cap centre (0, 7.476, 0) radii
(8.988, 8.652, 8.736)). Points on the cap / head are placed with spherical helpers so clumps hug the surface.
"""
import json
import math
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAP_C, CAP_R = np.array([0, 7.476, 0.0]), np.array([8.988, 8.652, 8.736])
HEAD_C, HEAD_R = np.array([0, 7.14, 0.5]), np.array([8.4, 7.98, 7.98])
BACK_C, BACK_R = np.array([0, 4.6, -4.4]), np.array([7.8, 5.2, 4.0])


def r3(v):
    return [round(float(x), 3) for x in v]


def unit(az, el):
    az, el = math.radians(az), math.radians(el)
    return np.array([math.cos(el) * math.sin(az), math.sin(el), math.cos(el) * math.cos(az)])


def on_ell(C, R, u, lift=0.0):
    p = R * u
    return C + p * (1 + lift / np.linalg.norm(p))


def slerp(u0, u1, t):
    w = math.acos(max(-1.0, min(1.0, float(u0 @ u1))))
    if w < 1e-6:
        return u0
    return (math.sin((1 - t) * w) * u0 + math.sin(t * w) * u1) / math.sin(w)


def head_z(x, y, out=0.0):
    """Front surface z of the head ellipsoid at (x, y), pushed `out` along +z."""
    q = 1 - (x / HEAD_R[0]) ** 2 - ((y - HEAD_C[1]) / HEAD_R[1]) ** 2
    return HEAD_C[2] + HEAD_R[2] * math.sqrt(max(q, 0.0)) + out


def cap_z(x, y, sign=1, out=0.0):
    q = 1 - (x / CAP_R[0]) ** 2 - ((y - CAP_C[1]) / CAP_R[1]) ** 2
    return CAP_C[2] + sign * (CAP_R[2] * math.sqrt(max(q, 0.0)) + out)


def back_z(x, y, out=0.0):
    q = 1 - (x / BACK_R[0]) ** 2 - ((y - BACK_C[1]) / BACK_R[1]) ** 2
    return BACK_C[2] - BACK_R[2] * math.sqrt(max(q, 0.0)) - out


def part(name, shape, params, material="hair", group="head", lod="all", **kw):
    d = {"name": name, "bone": "head", "shape": shape, "params": params, "material": material, "group": group,
         "lod": lod}
    d.update(kw)
    return d


def hair_parts():
    P = []
    # --- 12 crown clumps: hairline / sides sweep back over the cap and converge on the bow knot
    starts = [(20, 60, 25), (45, 54, 24), (70, 36, 19), (100, 34, 18), (86, 10, 13), (118, 4, 12)]
    for k, (az, el, el_end) in enumerate(starts):
        for sg, s in ((1, "L"), (-1, "R")):
            u0 = unit(sg * az, el)
            u1 = unit(sg * (180 - 7 - 3.2 * k), el_end)
            pts = [on_ell(CAP_C, CAP_R, slerp(u0, u1, t), lift=-0.2) for t in np.linspace(0, 1, 7)]
            rr = list(np.linspace(1.6, 0.85, 7))
            P.append(part(f"crown_{s}{k}", "tube", {"pts": [r3(p) for p in pts], "r": r3(rr), "flat": 0.42,
                                                     "flat_c": r3(CAP_C)}))
    # --- centre part line (groove cut into the cap) and 8-point crown whorl: sub-pixel, hi-res refs only
    path = [unit(0, 46), unit(0, 58), unit(0, 70), unit(0, 82), unit(180, 86), unit(180, 76)]
    P.append(part("part_line", "tube", {"pts": [r3(on_ell(CAP_C, CAP_R, u, 0.05)) for u in path], "r": [0.3] * 6},
                  op="subtract", blend={"set": "cap", "k": 0.15}, lod="ref"))
    wc = unit(180, 74)
    for k in range(8):
        a = math.radians(45 * k)
        # tangent basis at the whorl centre
        t1 = np.array([1.0, 0, 0])
        t2 = np.cross(wc, t1)
        d = math.cos(a) * t1 + math.sin(a) * t2
        d2 = math.cos(a + 0.6) * t1 + math.sin(a + 0.6) * t2
        p0 = on_ell(CAP_C, CAP_R, wc, 0.05)
        p1 = on_ell(CAP_C, CAP_R, (wc + 0.13 * d) / np.linalg.norm(wc + 0.13 * d), 0.15)
        p2 = on_ell(CAP_C, CAP_R, (wc + 0.24 * d2) / np.linalg.norm(wc + 0.24 * d2), 0.05)
        P.append(part(f"whorl_{k}", "tube", {"pts": [r3(p0), r3(p1), r3(p2)], "r": [0.5, 0.4, 0.04], "flat": 0.5,
                                             "flat_c": r3(CAP_C)}, lod="ref"))
    # --- hime bangs: 7 points along a straight line; the centre pair splits apart, a short back bang fills the V
    bangs = [  # name, root x, tip x, tip y, out
        ("bang_L3", 4.9, 5.7, 8.0, 0.42), ("bang_L2", 3.1, 3.55, 8.1, 0.5), ("bang_L1", 0.75, 1.55, 8.3, 0.55),
        ("bang_R1", -0.75, -1.55, 8.3, 0.55), ("bang_R2", -3.1, -3.55, 8.1, 0.5), ("bang_R3", -4.9, -5.7, 8.0, 0.42),
    ]
    for name, xr, xt, yt, out in bangs:
        root = [xr, 12.9, cap_z(xr, 12.9, out=-0.35)]
        xm, ym = (xr * 0.4 + xt * 0.6), 10.6
        mid = [xm, ym, head_z(xm, ym, out + 0.15)]
        tip = [xt, yt, head_z(xt, yt, out)]
        P.append(part(name, "tube", {"pts": [r3(root), r3(mid), r3(tip)], "r": [1.3, 1.05, 0.05], "flat": 0.42,
                                     "flat_c": r3(HEAD_C)}))
    root = [0, 13.1, cap_z(0, 13.1, out=-0.45)]
    mid = [0, 11.0, head_z(0, 11.0, 0.35)]
    tip = [0, 9.5, head_z(0, 9.5, 0.3)]
    P.append(part("bang_C", "tube", {"pts": [r3(root), r3(mid), r3(tip)], "r": [1.15, 0.9, 0.05], "flat": 0.42,
                                     "flat_c": r3(HEAD_C)}))
    # --- flat-cut hime side locks: 2 clumps per side, cut straight across at the jaw (cone = flat ends)
    for sg, s in ((1, "L"), (-1, "R")):
        P.append(part(f"sidelock_{s}_front", "cone", {"a": r3([sg * 8.0, 9.8, 2.6]), "b": r3([sg * 8.1, -0.9, 3.0]),
                                                      "ra": 1.45, "rb": 1.3, "flat": 0.62, "flat_n": [sg, 0, 0]}))
        P.append(part(f"sidelock_{s}_back", "cone", {"a": r3([sg * 8.25, 9.8, 0.4]), "b": r3([sg * 8.3, -0.3, 0.6]),
                                                     "ra": 1.6, "rb": 1.4, "flat": 0.62, "flat_n": [sg, 0, 0]}))
        # temple wisps (sub-pixel): hi-res refs only
        P.append(part(f"wisp_{s}", "rcone", {"a": r3([sg * 6.1, 11.8, head_z(6.1, 11.8, 0.25)]),
                                             "b": r3([sg * 6.9, 7.3, head_z(6.9, 7.3, 0.3)]), "ra": 0.55, "rb": 0.04,
                                             "flat": 0.5, "flat_c": r3(HEAD_C)}, lod="ref"))
    # --- back curtain under the bow: 5 pairs of sharp clumps over the back mass, alternating lengths
    for k, xt in enumerate(np.linspace(-6.3, 6.3, 10)):
        xr = xt * 0.8
        yt = -1.3 if k % 2 == 0 else -0.3
        root = [xr, 8.6, cap_z(xr, 8.6, sign=-1, out=-0.3)]
        mid = [xt * 0.95, 3.6, back_z(xt * 0.95, 3.6, 0.25)]
        tip = [xt, yt, -6.0 - 0.25 * (1 - abs(xt) / 6.3)]
        P.append(part(f"curtain_{k}", "tube", {"pts": [r3(root), r3(mid), r3(tip)], "r": [1.55, 1.4, 0.05], "flat": 0.42,
                                               "flat_c": r3(BACK_C + np.array([0, 0, 2.4]))}))
    # --- ponytail: 5 twisted sub-clumps swept along the simulated "pony" chain, ending in 3 sharp points
    P.append({"name": "pony_sweep", "chain": "pony", "material": "hair", "group": "head", "lod": "all",
              "sweep": {"clumps": 5, "twist": 40, "spread": 0.45, "clump_r": 0.6, "tips": 3, "tip": "sharp",
                        "taper_len": 0.35, "side_end": 0.88}})
    return P


def bow_parts():
    P = []
    for sg, s in ((-1, "L"), (1, "R")):
        # open loop: flattened elliptical band ring, ribbon width along local y, wider toward the outer end
        rot = [0, 180, 24] if sg < 0 else [0, 0, 24]
        zs = 1 if sg < 0 else -1        # local z of the outward (visible) face after the 180 deg yaw
        P.append({"name": f"bow_loop_{s}", "bone": "head", "shape": "torus", "center": [sg * 4.2, 11.2, -9.9], "rot": rot,
                  "params": {"R": [3.7, 1.2], "r": 0.3, "w": 2.2, "taper": 0.32}, "material": "ribbon", "group": "hat",
                  "blend": {"set": f"loop_{s}", "k": 0.0}, "lod": "all"})
        for c, (y0, y1) in enumerate(((0.75, 0.3), (-0.75, -0.3))):
            P.append({"name": f"bow_crease_{s}{c}", "bone": "head", "shape": "capsule", "center": [sg * 4.2, 11.2, -9.9],
                      "rot": rot, "params": {"a": [-2.7, y0 * 1.3, zs * 1.5], "b": [0.9, y1, zs * 1.42], "r": 0.22},
                      "material": "ribbon", "group": "hat", "op": "subtract", "blend": {"set": f"loop_{s}", "k": 0.12},
                      "lod": "ref"})
    P.append({"name": "bow_knot", "bone": "head", "shape": "rbox", "center": [0, 10.8, -10.35],
              "params": {"b": [1.3, 1.55, 1.05], "r": 0.6}, "material": "hatcuff", "group": "hat",
              "blend": {"set": "knot", "k": 0.0}, "lod": "all"})
    for sg in (-1, 1):
        P.append({"name": f"knot_groove_{'L' if sg < 0 else 'R'}", "bone": "head", "shape": "capsule",
                  "center": [0, 10.8, -10.35], "params": {"a": [sg * 0.5, -1.0, -1.12], "b": [sg * 0.45, 1.0, -1.12], "r": 0.2},
                  "material": "hatcuff", "group": "hat", "op": "subtract", "blend": {"set": "knot", "k": 0.1}, "lod": "ref"})
    for s in "LR":
        P.append({"name": f"bow_tail_{s}_sweep", "chain": f"bow_tail_{s}", "material": "hatcuff", "group": "hat",
                  "lod": "all", "sweep": {"clumps": 1, "tip": "fork", "fork_depth": 0.6}})
    return P


def tail_chains():
    out = []
    for sg, s in ((-1, "L"), (1, "R")):
        out.append({"name": f"bow_tail_{s}", "anchor_bone": "head", "anchor": [sg * 0.9, 9.9, -10.7],
                    "rest_dir": [sg * 0.29, -1, -0.05], "segments": 3, "seg_len": 2.2, "widths": [1.2, 1.3, 1.45],
                    "thickness": 0.32, "material": "hatcuff", "group": "hat", "stiffness": 420, "damping": 0.2,
                    "gravity": 900, "collide": True, "max_swing": 35})
    return out


def main():
    spec = {
        "extends": "S4_halfup_bow",
        "name": "S4_hd",
        "label": "S4 HD - SDF reference model (r12 M1: hair + bow)",
        "model": "hd",
        "remove_parts": ["fringe", "sidelock_L", "sidelock_R", "ribbon_loop_0", "ribbon_loop_1", "ribbon_knot",
                         "ribbon_tail_L", "ribbon_tail_R"],
        "part_overrides": {"hair_cap": {"blend": {"set": "cap", "k": 0.0}}},
        "hd_chains": tail_chains(),
        "parts": hair_parts() + bow_parts(),
    }
    path = os.path.join(ROOT, "data", "variants", "S4_hd.json")
    with open(path, "w") as f:
        json.dump(spec, f, indent=1)
    print("wrote", path, len(spec["parts"]), "parts")


if __name__ == "__main__":
    main()
