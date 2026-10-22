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
            pts = [on_ell(CAP_C, CAP_R, slerp(u0, u1, t), lift=-0.3) for t in np.linspace(0, 1, 13)]
            rr = list(np.interp(np.linspace(0, 1, 13), [0, 0.15, 0.35, 0.7, 1.0], [0.9, 1.45, 1.6, 1.3, 0.8]))
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
        for nm, z, ybot, dx in (("front", 2.8, -0.9, 0.0), ("back", 0.4, -0.2, 0.55)):
            pts = [[sg * (7.3 + dx), 10.2, z - 0.2], [sg * (8.35 + dx), 4.6, z + 0.1], [sg * (7.95 + dx), ybot, z + 0.4]]
            P.append(part(f"sidelock_{s}_{nm}", "tube", {"pts": [r3(p) for p in pts], "r": [1.5, 1.85, 1.65],
                                                          "flat": 0.5, "flat_c": r3(HEAD_C), "cut_end": True}))
        # temple wisps (sub-pixel): hi-res refs only
        P.append(part(f"wisp_{s}", "rcone", {"a": r3([sg * 6.1, 11.8, head_z(6.1, 11.8, 0.25)]),
                                             "b": r3([sg * 6.9, 7.3, head_z(6.9, 7.3, 0.3)]), "ra": 0.55, "rb": 0.04,
                                             "flat": 0.5, "flat_c": r3(HEAD_C)}, lod="ref"))
    # --- back curtain under the bow: 5 simulated chains x 2 sharp clumps (see curtain_chains)
    for k in range(5):
        P.append({"name": f"curtain_{k}_sweep", "chain": f"curtain_{k}", "material": "hair", "group": "head", "lod": "all",
                  "sweep": {"clumps": 2, "spread": 0.5, "clump_r": 0.55, "phase": 0, "tips": 1, "twist": 0,
                            "thickness": 0.75, "taper_len": 0.45}})
    # --- ponytail: 5 twisted sub-clumps swept along the simulated "pony" chain, ending in 3 sharp points
    P.append({"name": "pony_sweep", "chain": "pony", "material": "hair", "group": "head", "lod": "all",
              "sweep": {"clumps": 5, "twist": 40, "spread": 0.45, "clump_r": 0.6, "tips": 3, "tip": "sharp", "thickness": 2.3,
                        "taper_len": 0.35, "side_end": 0.88, "root_len": 0.2}})
    return P


def bow_parts():
    P = []
    for sg, s in ((-1, "L"), (1, "R")):
        # open loop: flattened elliptical band ring, ribbon width along local y, wider toward the outer end
        rot = [0, 180, 18] if sg < 0 else [0, 0, 18]
        zs = 1 if sg < 0 else -1        # local z of the outward (visible) face after the 180 deg yaw
        P.append({"name": f"bow_loop_{s}", "bone": "head", "shape": "torus", "center": [sg * 4.2, 10.9, -9.9], "rot": rot,
                  "params": {"R": [3.7, 1.2], "r": 0.3, "w": 1.95, "taper": 0.18}, "material": "ribbon", "group": "hat",
                  "blend": {"set": f"loop_{s}", "k": 0.0}, "lod": "all"})
        for c, (y0, y1) in enumerate(((0.75, 0.3), (-0.75, -0.3))):
            P.append({"name": f"bow_crease_{s}{c}", "bone": "head", "shape": "capsule", "center": [sg * 4.2, 10.9, -9.9],
                      "rot": rot, "params": {"a": [-2.7, y0 * 1.3, zs * 1.5], "b": [0.9, y1, zs * 1.42], "r": 0.22},
                      "material": "ribbon", "group": "hat", "op": "subtract", "blend": {"set": f"loop_{s}", "k": 0.12},
                      "lod": "ref"})
    P.append({"name": "bow_knot", "bone": "head", "shape": "rbox", "center": [0, 10.8, -10.6],
              "params": {"b": [1.3, 1.55, 1.05], "r": 0.6}, "material": "hatcuff", "group": "hat",
              "blend": {"set": "knot", "k": 0.0}, "lod": "all"})
    for sg in (-1, 1):
        P.append({"name": f"knot_groove_{'L' if sg < 0 else 'R'}", "bone": "head", "shape": "capsule",
                  "center": [0, 10.8, -10.6], "params": {"a": [sg * 0.5, -1.0, -1.12], "b": [sg * 0.45, 1.0, -1.12], "r": 0.2},
                  "material": "hatcuff", "group": "hat", "op": "subtract", "blend": {"set": "knot", "k": 0.1}, "lod": "ref"})
    for s in "LR":
        P.append({"name": f"bow_tail_{s}_sweep", "chain": f"bow_tail_{s}", "material": "hatcuff", "group": "hat",
                  "lod": "all", "sweep": {"clumps": 1, "tip": "fork", "fork_depth": 0.6}})
    return P


def curtain_chains():
    out = []
    for k, x in enumerate(np.linspace(-4.8, 4.8, 5)):
        out.append({"name": f"curtain_{k}", "anchor_bone": "head", "anchor": r3([x, 8.6, cap_z(x, 8.6, sign=-1, out=-0.4)]),
                    "rest_dir": r3([x * 0.07, -1, -0.22]), "segments": 2, "seg_len": 4.6 if k % 2 == 0 else 4.1,
                    "widths": [1.7, 1.55], "thickness": 0.75, "material": "hair", "group": "head", "stiffness": 260,
                    "damping": 0.15, "gravity": 900, "collide": True})
    return out


def surf(C, R, x, y, sign=1, out=0.0):
    """z on an ellipsoid (centre C, radii R) at (x, y), front (sign 1) or back (-1), pushed `out`."""
    q = 1 - ((x - C[0]) / R[0]) ** 2 - ((y - C[1]) / R[1]) ** 2
    return C[2] + sign * (R[2] * math.sqrt(max(q, 0.0)) + out)


def P_(name, bone, shape, params, material, group, lod="all", **kw):
    d = {"name": name, "bone": bone, "shape": shape, "params": params, "material": material, "group": group, "lod": lod}
    d.update(kw)
    return d


BODICE_C, BODICE_R = np.array([0, -0.25, 0.05]), np.array([4.992, 4.5, 4.16])     # chest bone


def coat_parts():
    P = []
    # princess seams (front + back) cut into the blended bodice; placket + 4 buttons: sub-pixel -> refs only
    for sgz in (1, -1):
        for sx in (-1, 1):
            pts = [[sx * x, y, surf(BODICE_C, BODICE_R, sx * x, y, sgz, 0.05)] for x, y in ((2.9, 3.0), (2.4, 1.0), (2.2, -1.0), (2.35, -3.2))]
            P.append(P_(f"seam_{'F' if sgz > 0 else 'B'}{'L' if sx > 0 else 'R'}", "chest", "tube",
                        {"pts": [r3(p) for p in pts], "r": [0.2] * 4}, "coat", "torso", lod="ref", op="subtract",
                        blend={"set": "torso", "k": 0.15}))
    pl = [[0, y, surf(BODICE_C, BODICE_R, 0, y, 1, 0.02)] for y in (2.8, 0.8, -1.4, -3.6)]
    P.append(P_("placket", "chest", "tube", {"pts": [r3(p) for p in pl], "r": [0.6] * 4, "flat": 0.3,
                                             "flat_c": r3(BODICE_C)}, "coat", "torso", lod="ref"))
    for k, y in enumerate((2.0, 0.6, -0.8, -2.2)):
        P.append({"name": f"button_{k}", "bone": "chest", "shape": "ellipsoid", "material": "coat_trim", "group": "torso",
                  "center": r3([0, y, surf(BODICE_C, BODICE_R, 0, y, 1, 0.2)]), "radii": [0.42, 0.42, 0.22], "lod": "ref"})
    # stand collar (under the scarf) and belt band with a buckle (hole + tongue on refs)
    P.append(P_("collar_band", "neck", "torus", {"R": [3.0, 2.5], "r": 0.4, "w": 1.2}, "coat_trim", "torso", center=[0, -0.5, 0.0]))
    P.append(P_("belt_band", "spine", "torus", {"R": [3.05, 2.55], "r": 0.45, "w": 0.75}, "coat_trim", "belt",
                center=[0, -0.3, 0.1]))
    bz = 0.1 + 2.55 + 0.45 + 0.1
    P.append(P_("buckle", "spine", "rbox", {"b": [0.95, 0.75, 0.22], "r": 0.15}, "ribbon", "belt", center=[0, -0.3, bz],
                blend={"set": "buckle", "k": 0.0}))
    P.append(P_("buckle_hole", "spine", "rbox", {"b": [0.5, 0.38, 0.6], "r": 0.08}, "ribbon", "belt", lod="ref",
                center=[0, -0.3, bz], op="subtract", blend={"set": "buckle", "k": 0.0}))
    P.append(P_("buckle_tongue", "spine", "capsule", {"a": [-0.5, 0, 0.05], "b": [0.3, 0, 0.12], "r": 0.12},
                "coat_trim", "belt", lod="ref", center=[0, -0.3, bz]))
    # A-line skirt: flattened cone blended into the bodice, 10 box pleats deepening to the hem; scalloped hem band
    P.append(P_("skirt_cone", "pelvis", "cone", {"a": [0, 1.6, 0], "b": [0, -5.25, 0], "ra": 5.2, "rb": 8.4,
                                                 "flat": 0.83, "flat_n": [0, 0, 1]}, "coat", "torso", center=[0, 0, 0.15],
                blend={"set": "torso", "k": 0.8},
                detail={"type": "pleats", "n": 10, "depth": 0.45, "y0": -0.8, "y1": -5.25, "lod": "all"}))
    P.append(P_("hem_band", "pelvis", "torus", {"R": [8.15, 6.8], "r": 0.45, "w": 0.75}, "coat_trim", "torso",
                center=[0, -5.45, 0.15], detail={"type": "scallop", "n": 16, "depth": 0.45, "y0": -0.15, "y1": -0.75, "lod": "all"}))
    # pocket flaps on the skirt front, following the cone slope
    for sx in (-1, 1):
        y = -1.3
        r = 5.2 + 3.2 * (1.6 - y) / 6.85
        phi = math.asin(3.4 / r)
        z = 0.15 + r * 0.83 * math.cos(phi) + 0.12
        P.append(P_(f"pocket_{'L' if sx > 0 else 'R'}", "pelvis", "rbox", {"b": [1.35, 0.68, 0.16], "r": 0.12}, "coat_trim",
                    "torso", center=r3([sx * 3.4, y, z]), rot=[26, sx * math.degrees(phi) * 0.8, 0]))
    return P


def scarf_parts():
    P = [P_("scarf_wrap_1", "neck", "torus", {"R": [3.5, 3.2], "r": 1.25, "w": 1.9}, "scarf", "scarf", center=[0, 0.5, 0.3],
            detail={"type": "ridges", "n": 28, "depth": 0.18, "lod": "ref"}),
         P_("scarf_wrap_2", "neck", "torus", {"R": [3.95, 3.45], "r": 1.3, "w": 1.6}, "scarf", "scarf",
            center=[0.3, -0.9, 0.6], rot=[0, 0, 6], detail={"type": "ridges", "n": 30, "depth": 0.18, "lod": "ref"}),
         P_("scarf_knot_hd", "neck", "rbox", {"b": [1.45, 1.2, 1.05], "r": 0.75}, "scarf", "scarf", center=[3.3, -0.4, 3.7]),
         {"name": "scarf_tail", "chain": "scarf_front", "material": "scarf", "group": "scarf", "lod": "all",
          "sweep": {"clumps": 1, "tip": "cut"}},
         {"name": "scarf_fringe", "chain": "scarf_front", "material": "scarf", "group": "scarf", "lod": "ref",
          "sweep": {"clumps": 1, "tip": "fringe", "only_fringe": True, "fringe": 6, "fringe_len": 1.3, "fringe_r": 0.32}}]
    return P


def limb_parts():
    P = []
    for s, sg in (("L", 1), ("R", -1)):
        st = f"sleeve_{s}"
        P.append(P_(f"uparm_hd_{s}", f"shoulder_{s}", "rcone", {"a": [0, -1.0, 0], "b": [0, -6.1, 0], "ra": 2.1, "rb": 1.95},
                    "coat", f"arm_{s}", blend={"set": st, "k": 0.9}))
        P.append(P_(f"forearm_hd_{s}", f"elbow_{s}", "rcone", {"a": [0, 0, 0], "b": [0, -4.5, 0], "ra": 1.95, "rb": 1.8},
                    "coat", f"arm_{s}", blend={"set": st, "k": 0.9}))
        for c, y in enumerate((0.9, -0.9)):
            P.append(P_(f"sleeve_crease_{s}{c}", f"elbow_{s}", "torus", {"R": [2.05, 2.05], "r": 0.16}, "coat", f"arm_{s}",
                        lod="ref", center=[0, y, 0], rot=[0, 0, 8 * (1 - 2 * c)], op="subtract", blend={"set": st, "k": 0.1}))
        P.append(P_(f"cuff_hd_{s}", f"elbow_{s}", "torus", {"R": [1.65, 1.65], "r": 0.45, "w": 0.75}, "coat_trim", f"arm_{s}",
                    center=[0, -4.75, 0]))
        # mitten: rounded palm box, thumb at 35 deg with a gap, ribbed knit cuff
        P.append(P_(f"palm_{s}", f"hand_{s}", "rbox", {"b": [1.45, 1.6, 1.2], "r": 1.0}, "mitten", f"arm_{s}",
                    center=[0, -1.25, 0.15]))
        a = np.array([-sg * 0.85, -0.5, 0.95])
        dvec = np.array([-sg * math.sin(math.radians(35)) * 0.6, -math.cos(math.radians(35)), math.sin(math.radians(35)) * 0.8])
        dvec /= np.linalg.norm(dvec)
        P.append(P_(f"thumb_hd_{s}", f"hand_{s}", "rcone", {"a": r3(a), "b": r3(a + 1.3 * dvec), "ra": 0.68, "rb": 0.58},
                    "mitten", f"arm_{s}"))
        P.append(P_(f"mitten_cuff_{s}", f"hand_{s}", "torus", {"R": [1.25, 1.2], "r": 0.42, "w": 0.68}, "mitten", f"arm_{s}",
                    center=[0, 0.05, 0.1], detail={"type": "ridges", "n": 12, "depth": 0.12, "lod": "ref"}))
        # tights: thigh capsule + calf cone blended at the knee
        P.append(P_(f"thigh_hd_{s}", f"hip_{s}", "rcone", {"a": [0, -0.2, 0], "b": [0, -6.5, 0], "ra": 1.75, "rb": 1.45},
                    "pants", f"leg_{s}", blend={"set": f"tights_{s}", "k": 0.6}))
        P.append(P_(f"calf_{s}", f"knee_{s}", "rcone", {"a": [0, 0, 0], "b": [0, -3.0, 0], "ra": 1.45, "rb": 1.25},
                    "pants", f"leg_{s}", blend={"set": f"tights_{s}", "k": 0.6}))
        # tall boot: shaft, fold-over cuff (+ rim), toe box, sole (+ welt), heel, back seam
        bs = f"boot_{s}"
        P.append(P_(f"shaft_{s}", f"knee_{s}", "cone", {"a": [0, -0.2, 0], "b": [0, -6.3, 0], "ra": 1.95, "rb": 1.7},
                    "boots", f"leg_{s}", blend={"set": bs, "k": 0.7}))
        P.append(P_(f"foot_{s}", f"ankle_{s}", "rbox", {"b": [1.95, 0.95, 2.6], "r": 0.95}, "boots", f"leg_{s}",
                    center=[0, -0.95, 0.55], blend={"set": bs, "k": 0.7}))
        P.append({"name": f"toe_{s}", "bone": f"ankle_{s}", "shape": "ellipsoid", "center": [0, -0.8, 1.75],
                  "radii": [2.0, 1.0, 1.5], "material": "boots", "group": f"leg_{s}", "lod": "all",
                  "blend": {"set": bs, "k": 0.35}})
        P.append(P_(f"sole_{s}", f"ankle_{s}", "rbox", {"b": [2.05, 0.3, 2.3], "r": 0.25}, "boots", f"leg_{s}",
                    center=[0, -1.6, 0.3], blend={"set": bs, "k": 0.1}))
        P.append(P_(f"welt_{s}", f"ankle_{s}", "rbox", {"b": [2.13, 0.07, 2.38], "r": 0.05}, "boots", f"leg_{s}", lod="ref",
                    center=[0, -1.27, 0.3], blend={"set": bs, "k": 0.0}))
        P.append(P_(f"heel_{s}", f"ankle_{s}", "rbox", {"b": [1.55, 0.6, 0.95], "r": 0.2}, "boots", f"leg_{s}",
                    center=[0, -1.3, -1.25], blend={"set": bs, "k": 0.1}))
        P.append(P_(f"boot_seam_{s}", f"knee_{s}", "capsule", {"a": [0, -1.2, -1.95], "b": [0, -6.0, -1.72], "r": 0.14},
                    "boots", f"leg_{s}", lod="ref", op="subtract", blend={"set": bs, "k": 0.05}))
        P.append(P_(f"bootcuff_hd_{s}", f"knee_{s}", "torus", {"R": [1.9, 1.9], "r": 0.6, "w": 1.3}, "boot_cuff",
                    f"leg_{s}", center=[0, -0.6, 0.1]))
        P.append(P_(f"bootcuff_rim_{s}", f"knee_{s}", "torus", {"R": [2.05, 2.05], "r": 0.3}, "boot_cuff", f"leg_{s}",
                    lod="ref", center=[0, 0.55, 0.1]))
    return P


def tail_chains():
    out = []
    for sg, s in ((-1, "L"), (1, "R")):
        out.append({"name": f"bow_tail_{s}", "anchor_bone": "head", "anchor": [sg * 0.9, 10.0, -11.9],
                    "rest_dir": [sg * 0.8, -1, -0.55], "segments": 3, "seg_len": 2.0, "widths": [1.2, 1.3, 1.45],
                    "thickness": 0.32, "material": "hatcuff", "group": "hat", "stiffness": 600, "damping": 0.2,
                    "gravity": 900, "collide": True, "max_swing": 35})
    return out


def main():
    spec = {
        "extends": "S4_halfup_bow",
        "name": "S4_hd",
        "label": "S4 HD - SDF reference model (r12 M1-M3: hair, bow, coat, scarf, limbs)",
        "model": "hd",
        "remove_parts": ["fringe", "sidelock_L", "sidelock_R", "ribbon_loop_0", "ribbon_loop_1", "ribbon_knot",
                         "ribbon_tail_L", "ribbon_tail_R",
                         # M2/M3: body ellipsoids replaced by HD parts (legacy prims stay as sim/QA colliders)
                         "skirt_coat", "hem", "belt", "collar", "scarf_wrap1", "scarf_wrap2", "scarf_knot"]
                        + [f"{n}_{s}" for s in "LR" for n in ("uparm", "forearm", "cuff", "mitten", "thumb", "thigh",
                                                              "shin", "boot", "bootcuff")],
        "part_overrides": {"hair_cap": {"blend": {"set": "cap", "k": 0.0}},
                           **{n: {"blend": {"set": "torso", "k": 0.8}} for n in ("bodice", "waist", "hips_coat")}},
        "hd_chains": tail_chains() + curtain_chains(),
        "parts": hair_parts() + bow_parts() + coat_parts() + scarf_parts() + limb_parts(),
    }
    path = os.path.join(ROOT, "data", "variants", "S4_hd.json")
    with open(path, "w") as f:
        json.dump(spec, f, indent=1)
    print("wrote", path, len(spec["parts"]), "parts")


if __name__ == "__main__":
    main()
