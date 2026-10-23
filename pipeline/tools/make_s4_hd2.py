"""Author data/variants/S4_hd2.json: the refined S4_hd (r21, user: "the original model performed the best as a pixel
reference ... it's ugly quads now, it should be a more well defined, polished model; hair and bow need to be improved,
clothes as well, gloves bigger; keep the shading").

    .venv/bin/python -m pipeline.tools.make_s4_hd2

Same rig, proportions, animations, chains (sim / sway / springs), face pass and shading as S4_hd
(pipeline/tools/make_s4_hd.py, imported - S4_hd itself is untouched). Geometry is rebuilt from smooth swept sheets
(sdf "sweep" kind: densely sampled Catmull-Rom centre line, lens / cupped cross-section, blunt / V-cut ends) and smooth
unions instead of stacked round-cone bead chains:
  hair   one clean dome (cap + broad flow sheets smooth-unioned), 3-panel hime fringe with 2 notches over a dark back
         layer, flat blunt side locks, broad layered back sheets with V tips, ONE S-curve ponytail of 3 layered clumps
  bow    closed teardrop satin loops (thick rim, dark inner hollow, one soft crease), wide horizontal wings swept back,
         rounded knot, swallowtail tails with V-cut ends; same spring chains as S4_hd
  coat   bodice + waist pinch, A-line skirt with soft rounded folds, hem band following the folds, placket, 6 buttons,
         belt + buckle, slightly puffy sleeves, clean cuffs, no pocket flaps (canon)
  scarf  chunky double wrap smooth-unioned, clean ribs, ribbon tail with fringe (her left)
  mittens ~1.5x volume, round, small thumb
  boots  clean shaft / toe / sole / heel, puffy fur cuff
"""
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from pipeline.tools import make_s4_hd as H  # noqa: E402

r3, unit, on_ell, slerp, head_z = H.r3, H.unit, H.on_ell, H.slerp, H.head_z
HEAD_C = H.HEAD_C
# hair cap: the S4_hd cap, 0.45 taller (the crown clumps it replaces stood ~0.5 proud of it: same crown height)
CAP_C, CAP_R = np.array([0, 7.5, 0.0]), np.array([9.0, 9.1, 8.8])


def cap_z(x, y, sign=1, out=0.0):
    q = 1 - (x / CAP_R[0]) ** 2 - ((y - CAP_C[1]) / CAP_R[1]) ** 2
    return CAP_C[2] + sign * (CAP_R[2] * math.sqrt(max(q, 0.0)) + out)
BACK_MAT = H.BACK_MAT


def part(name, shape, params, material="hair", group="head", lod="all", bone="head", **kw):
    d = {"name": name, "bone": bone, "shape": shape, "params": params, "material": material, "group": group, "lod": lod}
    d.update(kw)
    return d


def sweep(name, pts, w, t, material="hair", group="head", n=16, lod="all", bone="head", **kw):
    """Static swept sheet (sdf "sweep"). kw: flat_c / flat_n / nrm, lens, curl, cap0, cap1, vcut, capr, closed and
    part keys (blend, op, follow, clip_all ...)."""
    pk = {k: kw.pop(k) for k in list(kw) if k in ("flat_c", "flat_n", "nrm", "lens", "curl", "cap0", "cap1", "vcut",
                                                    "capr", "closed")}
    prm = {"pts": [r3(p) for p in pts], "n": n, "w": [round(float(x), 3) for x in np.atleast_1d(w)],
           "t": [round(float(x), 3) for x in np.atleast_1d(t)], **pk}
    for k in ("flat_c", "flat_n"):
        if k in prm:
            prm[k] = r3(prm[k])
    if "nrm" in prm:
        prm["nrm"] = [r3(v) for v in prm["nrm"]]
    return part(name, "sweep", prm, material, group, lod, bone, **kw)


# ======================================================================================== head
# user r21: "the sharp face looks off" -> standard 3D anime base-mesh (VRoid-like) construction: a soft rounded oval,
# full smooth cheeks curving continuously into a SMALL ROUNDED chin (no point, no crease), soft jaw line, a slightly flat
# face front plane. Same cranium as S4_hd (eye rows keep their width).
HEAD2 = {"cranium": ([0, 7.6, 0.45], [8.2, 7.6, 7.6]), "jaw": ([0, 3.7, 1.75], [6.05, 4.8, 6.05]),
         "chin": ([0, 1.35, 4.35], [2.55, 2.05, 2.35]), "cheek": ([4.25, 4.35, 4.15], [2.45, 2.2, 2.2], 22),
         "front": ([0, 5.4, 4.2], [5.0, 4.4, 2.5]), "k": 1.8}


def head_parts():
    fs = {"set": "face", "k": HEAD2["k"]}
    P = []
    for n in ("cranium", "jaw", "chin", "front"):
        c, r = HEAD2[n]
        P.append({"name": n if n != "front" else "face_plane", "bone": "head", "shape": "ellipsoid", "center": list(c),
                  "radii": list(r), "material": "skin", "group": "head", "blend": dict(fs), "lod": "all"})
    kc, kr, krot = HEAD2["cheek"]
    for sg, s in ((1, "L"), (-1, "R")):
        P.append({"name": f"cheek_{s}", "bone": "head", "shape": "ellipsoid", "center": [sg * kc[0], kc[1], kc[2]],
                  "radii": list(kr), "rot": [0, sg * krot, 0], "material": "skin", "group": "head",
                  "blend": dict(fs), "lod": "all"})
    return P


def eye_marks():
    """make_s4_hd.eye_marks on the S4_hd2 head (eye / mouth centres on the modelled face surface)."""
    from pipeline import sdf
    parts = [dict({"group": "head", "op": "union", "lod": "all"}, **p) for p in head_parts()]
    W = {"head": np.eye(4)}
    prims = []
    for sp in parts:
        prims += sdf._pose_static(sp, W, np.eye(4))
    C = sdf._Compiled(prims)
    out = []
    for sg, (x, y) in ((1, H.EYE_MARK), (-1, H.EYE_MARK), (0, H.MOUTH_MARK)):
        x = sg * x
        lo, hi = 0.0, 12.0
        for _ in range(40):
            m = (lo + hi) / 2
            d, _ = sdf.scene_sdf(prims, np.array([[x, y, m]]), C)
            lo, hi = (m, hi) if d[0] < 0 else (lo, m)
        out.append([round(x, 3), round(y, 3), round(lo, 3)])
    return out


# ======================================================================================== hair
CAP_SET = {"set": "cap", "k": 0.35}        # fringe roots / back sheets melt into the dome
# crown flow sheets: (azimuth, elevation) of the hairline start (per side), converging on the ponytail root
CROWN_GROOVES = [(13, 50, 0), (36, 46, 0), (60, 36, 0), (86, 24, 0), (112, 12, 0)]
CROWN_END = (180, 20)

# hime fringe (AD r1-1): a curved SHELL of 3 panels following the forehead (radial thickness axis, cupped to the head
# curvature), 2 small V notches, centre widest; each panel convex (lens), thinner at the tip, rounded cut edge, lifted
# 0.3-0.5 off the forehead. (name, x root, x tip, y tip, half-width profile root..tip, lift)
FRINGE = [("fringe_C", 0.0, 0.0, 8.35, (2.75, 2.85, 2.85, 2.7), 0.42),
          ("fringe_L", 4.1, 4.85, 7.95, (2.3, 2.35, 2.35, 2.25), 0.4)]
FRINGE_T = (0.55, 0.52, 0.42, 0.3)
FRINGE_BACK = [("fringeB_L", 2.75, 2.95, 8.1, (0.9, 0.95, 0.9, 0.8), -0.05)]   # dark layer behind the 2 notches
# side locks (AD r1-2): start under the fringe at the temple, run straight down close to the cheek / jaw, cupped toward
# the face, blunt cut at the collarbone
SIDELOCK = {"pts": [(7.3, 11.3, 1.0), (7.95, 7.0, 1.55), (7.05, 3.0, 1.8), (6.35, -2.1, 1.9)],
            "w": (1.3, 1.6, 1.7, 1.6), "t": (0.5, 0.58, 0.6, 0.55), "nrm": (0.52, 0.85), "curl": 0.3}
# side sheets behind the locks (AD r1-3): replace the legacy hair_back ball; layered, lens section, soft V tips
SIDE_SHEETS = [("sideA", [(6.9, 11.6, -3.0), (8.55, 6.5, -3.4), (8.2, 2.0, -3.5), (7.6, -1.0, -3.3)],
                (1.2, 2.2, 2.35, 2.1), -0.5),
               ("sideB", [(5.2, 11.4, -6.6), (6.95, 6.0, -6.9), (6.6, 1.4, -6.8), (6.0, -0.8, -6.4)],
                (1.2, 2.2, 2.35, 2.1), -0.5)]


def crown_sheets():
    """One clean dome (the hair cap) with the flow of the hair sheets drawn as soft grooves converging from the
    hairline over the crown to the ponytail root (smooth subtraction from the cap; sub-pixel -> refs only)."""
    P = []
    ue = unit(*CROWN_END)
    for k, (az, el, _w) in enumerate(CROWN_GROOVES):
        for sg, s in (((1, "L"), (-1, "R")) if az else ((1, "C"),)):
            u0 = unit(sg * az, el)
            u1 = unit(sg * (180 - 7 - 2.0 * k), CROWN_END[1] - 1.0 * k) if az else ue
            pts = [on_ell(CAP_C, CAP_R, slerp(u0, u1, t), lift=0.12) for t in np.linspace(0, 0.93, 7)]
            P.append(sweep(f"crown_groove_{s}{k}", pts, w=(0.05, 0.2, 0.22, 0.2, 0.05), t=(0.05, 0.2, 0.22, 0.2, 0.05),
                           n=18, flat_c=CAP_C, cap0=0, cap1=0, op="subtract", lod="ref",
                           blend={"set": "cap", "k": 0.35}))
    return P


def fringe_parts():
    P = []
    for layer, mat, rootY in ((FRINGE_BACK, BACK_MAT, 11.6), (FRINGE, "hair", 13.8)):
        for name, xr, xt, yt, wp, out in layer:
            for sg, s in (((1, "L"), (-1, "R")) if xr or xt else ((1, ""),)):
                nm = name if not s else name.replace("_L", f"_{s}")
                ys = [rootY, 11.6, 9.9, yt]
                xs = [xr, xr * 0.7 + xt * 0.3, xr * 0.3 + xt * 0.7, xt]
                outs = [-0.9, out + 0.15, out + 0.12, out]
                pts = []
                for x, y, o in zip(xs, ys, outs):
                    z = cap_z(x, y, out=o) if o < 0 and y > 11 else head_z(x, y, o)
                    pts.append([sg * x, y, z])
                t = FRINGE_T if mat == "hair" else 0.28
                P.append(sweep(nm, pts, w=wp, t=t, material=mat, n=24, flat_c=HEAD_C, lens=0.45, curl=0.24,
                               cap1=1, capr=1.0, blend={"set": "cap", "k": 0.55}))
    return P


def sidelock_parts():
    P = []
    nx, nz = SIDELOCK["nrm"]
    for sg, s in ((1, "L"), (-1, "R")):
        pts = [[sg * x, y, z] for x, y, z in SIDELOCK["pts"]]
        P.append(sweep(f"sidelock2_{s}", pts, w=SIDELOCK["w"], t=SIDELOCK["t"], n=18, nrm=[[sg * nx, 0.0, nz]] * 4,
                       lens=0.45, curl=SIDELOCK["curl"], cap1=1, capr=1.0, blend={"set": "cap", "k": 0.4}))
        for name, ctrl, w, vc in SIDE_SHEETS:
            pts = [[sg * x, y, z] for x, y, z in ctrl]
            P.append(sweep(f"{name}_{s}", pts, w=w, t=(0.5, 0.58, 0.55, 0.42), n=18, flat_c=[0, 5.0, -2.5],
                           lens=0.8, curl=0.2, cap1=1, vcut=vc, capr=1.0, blend={"set": "cap", "k": 1.1}))
    return P


# back curtain: one broad layered sheet per simulated chain (5 chains, same sim / sway as S4_hd)
CURTAIN = {"w": (0.55, 1.4, 2.15, 2.35, 2.25, 1.85), "t": (0.4, 0.5, 0.6, 0.55, 0.4), "lens": 0.7, "curl": 0.3,
           "vcut": -0.55, "dz": (0.0, 0.2), "root_pull": 0.0}
# ponytail: ONE swelling S-curve tail of 3 layered clumps converging on a single sharp point
PONY_S = (0.0, 0.7, 1.2, 1.4, 1.0, 0.3, -0.35, -0.6, -0.45, -0.05, 0.45)        # outward offset (S-curve in the side view)
PONY_W = (0.6, 1.0, 1.5, 1.95, 2.2, 2.2, 1.95, 1.5, 1.0, 0.6, 0.35)
PONY_T = (0.7, 0.95, 1.2, 1.38, 1.45, 1.4, 1.22, 0.95, 0.68, 0.45, 0.3)
PONY_SIDE_DX = (0.1, 0.5, 0.9, 1.25, 1.45, 1.45, 1.25, 0.9, 0.5, 0.15, 0.0)
PONY_EXTEND = 2.2


def hair_chain_parts():
    P = []
    for k in range(5):
        dz = CURTAIN["dz"][k % 2]
        st = {"dz": [dz], "w": list(CURTAIN["w"]), "t": list(CURTAIN["t"]), "lens": CURTAIN["lens"],
              "curl": CURTAIN["curl"], "vcut": CURTAIN["vcut"], "cap1": 1, "capr": 1.0}
        x = -4.8 + 2.4 * k
        # AD r1-3: the back sheets fan out from the ponytail root (prepended bone-space root under the knot)
        P.append({"name": f"curtain_{k}_sheet", "chain": f"curtain_{k}", "material": "hair", "group": "head",
                  "lod": "all", "blend": {"set": "cap", "k": 1.0},
                  "sweep": {"mode": "ribbon", "n": 22, "root_to": ["head", r3([x * 0.28, 9.9, cap_z(x * 0.28, 9.9, -1, -0.3)])],
                            "strands": [st]}})
    # 4 layered clumps: 2 on top split by a soft central groove, 2 tucked under at the sides; all converge on one point
    side = lambda sg: {"dx": [sg * v for v in PONY_SIDE_DX[:-1]] + [sg * 0.3], "dz": [v - 0.4 for v in PONY_S],
                       "w": [v * 0.6 for v in PONY_W[:-2]] + [0.3, 0.18], "t": [v * 0.78 for v in PONY_T], "lens": 0.6, "curl": 0.1,
                       "nz_tilt": [sg * 0.6], "cap1": 1, "capr": 0.9}
    top = lambda sg: {"dx": [sg * v * 0.42 for v in PONY_SIDE_DX], "dz": list(PONY_S),
                      "w": [v * 0.62 for v in PONY_W], "t": list(PONY_T), "lens": 0.55, "curl": 0.12,
                      "nz_tilt": [sg * 0.15], "cap1": 1, "capr": 0.9}
    P.append({"name": "pony_ribbons", "chain": "pony", "material": "hair", "group": "head", "lod": "all",
              "blend": {"set": "pony", "k": 0.25},
              "sweep": {"mode": "ribbon", "n": 48, "extend": PONY_EXTEND, "root_pull": 0.8,
                        "strands": [side(1), side(-1), top(1), top(-1)]}})
    return P


def hair_parts():
    return crown_sheets() + fringe_parts() + sidelock_parts() + hair_chain_parts()


# ======================================================================================== bow
# user r21: "bow is detached from head" -> the knot sits ON the hair at the ponytail root, sunk ~0.8 into the hair
KNOT = np.array([0.0, 9.75, -8.95])
# AD r1-5: wide flat satin RIBBON folded into each loop: a thin lens-section band (width ~1.5x the r1 tube diameter)
# around a teardrop, the loop plane rolled about the wing axis so the broad ribbon face shows from behind / in front as
# a puffy pillow with a dark inner opening; pinched into a chunky knot. Wide horizontal wings, swept back.
BOW = {"up_deg": 5.0, "back_deg": 22.0, "roll_deg": 72.0, "root": 0.7, "dy": 0.0,
       "outline": [(0.5, 0.0), (2.1, 0.8), (4.4, 1.45), (6.9, 1.75), (8.9, 1.4), (9.8, 0.35), (9.4, -0.75),
                   (7.5, -1.4), (4.8, -1.3), (2.3, -0.75)],
       "w": (0.55, 1.15, 1.7, 2.05, 2.2, 2.05, 1.7, 1.15, 0.55), "t": (0.45, 0.52, 0.6, 0.64, 0.6, 0.52, 0.45),
       "lens": 0.6, "curl": 0.35}


def loop_frame(sg):
    """Head-space origin + axes of one wing: x along the wing (out, slightly up, swept back), y / z the loop plane /
    ribbon-width axes rolled about x."""
    up, back, roll = math.radians(BOW["up_deg"]), math.radians(BOW["back_deg"]), math.radians(BOW["roll_deg"])
    ex = np.array([sg * math.cos(up) * math.cos(back), math.sin(up), -math.cos(up) * math.sin(back)])
    ey = np.array([0.0, 1.0, 0.0]) - ex[1] * ex
    ey /= np.linalg.norm(ey)
    ez = np.cross(ex, ey)
    ey, ez = math.cos(roll) * ey + math.sin(roll) * ez * sg, -math.sin(roll) * ey * sg + math.cos(roll) * ez
    o = KNOT + np.array([sg * BOW["root"], BOW["dy"], -0.15])
    return o, ex, ey, ez


def bow_parts():
    P = []
    for sg, s in ((-1, "L"), (1, "R")):
        o, ex, ey, ez = loop_frame(sg)
        L = lambda x, y, z=0.0: o + x * ex + y * ey + z * ez
        fol = {"chain": f"bow_spring_{s}", "gain": H.BOW_SPRING_GAIN, "gain_by_clip": {"idle": 0.0, "carry_idle": 0.0},
               "max_drop": H.BOW_MAX_DROP, "drop_frame": "world"}
        grp = f"bow_spring_{s}"
        pts = [L(x, y) for x, y in BOW["outline"]]
        cen = L(5.0, 0.1)
        P.append(sweep(f"bow_loop_{s}", pts, w=BOW["w"], t=BOW["t"], material="ribbon", group=grp, n=44, closed=True,
                       flat_c=cen, lens=BOW["lens"], curl=BOW["curl"], follow=fol, blend={"set": f"loop_{s}", "k": 0.5}))
        # dark inner opening: a membrane deep inside the loop
        P.append(sweep(f"bow_hollow_{s}", [L(1.0, 0.0, -0.4), L(4.6, 0.1, -0.5), L(8.2, 0.15, -0.4)],
                       w=(0.3, 1.0, 1.1, 0.5), t=0.14, material="ribbon_in", group=grp, n=10, flat_n=ey, cap1=1,
                       capr=0.9, follow=fol))
        # one soft crease: a shallow fold line along the outer face of the upper ribbon band (refs)
        cr = []
        for (x, y), tk in zip([(2.4, 0.85), (4.4, 1.45), (6.9, 1.75), (8.7, 1.45)], (0.42, 0.55, 0.6, 0.55)):
            d = np.array([x - 5.0, y - 0.1])
            d /= np.linalg.norm(d)
            cr.append(L(x + d[0] * tk, y + d[1] * tk, 0.25))
        P.append(sweep(f"bow_crease_{s}", cr, w=(0.05, 0.22, 0.22, 0.05), t=(0.05, 0.2, 0.2, 0.05),
                       material="ribbon", group=grp, n=12, flat_c=cen, op="subtract", lod="ref", cap0=0, cap1=0,
                       follow=fol, blend={"set": f"loop_{s}", "k": 0.3}))
    P.append(part("bow_knot", "rbox", {"b": [1.3, 1.6, 1.2], "r": 0.95}, material="hatcuff", group="hat",
                  center=r3(KNOT), blend={"set": "knot", "k": 0.0}))
    for sg in (-1, 1):
        P.append(part(f"knot_groove_{'L' if sg < 0 else 'R'}", "capsule", {"a": [sg * 0.55, -1.15, -1.3],
                      "b": [sg * 0.5, 1.15, -1.3], "r": 0.17}, material="hatcuff", group="hat", lod="ref",
                      center=r3(KNOT), op="subtract", blend={"set": "knot", "k": 0.1}))
    for s in "LR":
        P.append({"name": f"bow_tail_{s}_ribbon", "chain": f"bow_tail_{s}", "material": "hatcuff", "group": "hat",
                  "lod": "all", "sweep": {"mode": "ribbon", "n": 14, "root_pull": 0.6,
                                          "strands": [{"w": [0.85, 1.1, 1.3, 1.42], "t": [0.24, 0.22, 0.2],
                                                       "curl": 0.25, "lens": 0.3, "vcut": 1.25, "cap1": 1,
                                                       "capr": 0.4}]}})
    return P


# ======================================================================================== coat
FOLDS = {"n": 6, "depth": 0.75}


def coat_parts():
    surf, BC, BR, P_ = H.surf, H.BODICE_C, H.BODICE_R, H.P_
    P = []
    # placket: a clean flat strip down the bodice front (refs), 6 gold buttons: 3 above the belt, 3 on the skirt
    pl = [[0, y, surf(BC, BR, 0, y, 1, 0.04)] for y in (3.0, 1.2, -0.6, -2.4, -3.8)]
    P.append(sweep("placket", pl, w=0.62, t=0.17, material="coat", group="torso", bone="chest", n=10, flat_n=[0, 0, 1],
                   lod="ref", cap0=1, cap1=1, capr=0.5))
    for k, y in enumerate((2.3, 0.9, -0.5)):
        P.append({"name": f"button_{k}", "bone": "chest", "shape": "ellipsoid", "material": "button", "group": "torso",
                  "center": r3([0, y, surf(BC, BR, 0, y, 1, 0.2)]), "radii": [0.4, 0.4, 0.2], "lod": "ref"})
    for k, y in enumerate((-1.2, -2.7, -4.2)):
        r = 5.2 + 3.2 * (1.6 - y) / 6.85
        P.append({"name": f"button_s{k}", "bone": "pelvis", "shape": "ellipsoid", "material": "button", "group": "torso",
                  "center": r3([0, y, 0.15 + r * 0.83 + 0.12]), "radii": [0.4, 0.4, 0.2], "lod": "ref"})
    P.append(sweep("placket_skirt", [[0, 1.0, 0.15 + 5.2 * 0.83 + 0.0], [0, -2.0, 0.15 + (5.2 + 3.2 * 3.6 / 6.85) * 0.83],
                                     [0, -4.6, 0.15 + (5.2 + 3.2 * 6.2 / 6.85) * 0.83]],
                   w=0.62, t=0.12, material="coat", group="torso", bone="pelvis", n=8, flat_n=[0, 0.3, 1], lod="ref"))
    P.append(P_("collar_band", "neck", "torus", {"R": [3.0, 2.5], "r": 0.4, "w": 1.2}, "coat_trim", "torso",
                center=[0, -0.5, 0.0]))
    P.append(P_("belt_band", "spine", "torus", {"R": H.BELT_R, "r": 0.42, "w": 0.72, "round": 0.0}, "coat_trim", "belt",
                center=[0, -0.3, 0.1], clip_all=H.BELT_CLIP))
    bz = 0.1 + 2.55 + 0.42 + 0.12
    P.append(P_("buckle", "spine", "rbox", {"b": [0.95, 0.78, 0.2], "r": 0.2}, "ribbon", "belt", center=[0, -0.3, bz],
                blend={"set": "buckle", "k": 0.0}))
    P.append(P_("buckle_hole", "spine", "rbox", {"b": [0.52, 0.38, 0.6], "r": 0.14}, "ribbon", "belt", lod="ref",
                center=[0, -0.3, bz], op="subtract", blend={"set": "buckle", "k": 0.0}))
    P.append(P_("buckle_tongue", "spine", "capsule", {"a": [-0.5, 0, 0.05], "b": [0.3, 0, 0.1], "r": 0.11},
                "coat_trim", "belt", lod="ref", center=[0, -0.3, bz]))
    # A-line skirt: the same flattened cone blended into the bodice, with soft rounded folds easing in toward the hem
    P.append(P_("skirt_cone", "pelvis", "cone", {"a": [0, 1.6, 0], "b": [0, -5.25, 0], "ra": 5.2, "rb": 8.4,
                                                 "flat": 0.83, "flat_n": [0, 0, 1]}, "coat", "torso", center=[0, 0, 0.15],
                blend={"set": "torso", "k": 0.8},
                detail={"type": "folds", "n": FOLDS["n"], "depth": FOLDS["depth"], "y0": -0.6, "y1": -5.25,
                        "lod": "all"}))
    # hem band: follows the skirt folds (curved hem), rounded
    P.append(P_("hem_band", "pelvis", "torus", {"R": H.HEM_R, "r": 0.5, "w": H.HEM_W}, "coat_trim", "torso",
                center=[0, H.HEM_Y, 0.15],
                detail={"type": "folds", "n": FOLDS["n"], "depth": FOLDS["depth"] * 0.8, "y0": 60.0, "y1": -60.0,
                        "lod": "all"}))
    return P


def scarf_parts():
    P_ = H.P_
    sset = {"set": "scarf", "k": 0.55}
    return [P_("scarf_wrap_1", "neck", "torus", {"R": [3.5, 3.2], "r": 1.3, "w": 1.85}, "scarf", "scarf",
               center=[0, 0.5, 0.3], blend=dict(sset), detail={"type": "ridges", "n": 34, "depth": 0.13, "lod": "ref"}),
            P_("scarf_wrap_2", "neck", "torus", {"R": [3.95, 3.45], "r": 1.32, "w": 1.6}, "scarf", "scarf",
               center=[0.3, -0.9, 0.6], rot=[0, 0, 6], blend=dict(sset),
               detail={"type": "ridges", "n": 36, "depth": 0.13, "lod": "ref"}),
            P_("scarf_knot_hd", "neck", "rbox", {"b": [1.4, 1.2, 1.0], "r": 0.95}, "scarf", "scarf",
               center=[3.3, -0.4, 3.7], blend=dict(sset)),
            {"name": "scarf_tail", "chain": "scarf_front", "material": "scarf", "group": "scarf", "lod": "all",
             "sweep": {"mode": "ribbon", "n": 14, "root_pull": 0.4,
                       "strands": [{"w": [1.35, 1.45, 1.5], "t": [0.85, 0.8, 0.75], "lens": 0.3, "curl": 0.05,
                                    "cap1": 1, "capr": 0.35}]}},
            {"name": "scarf_fringe", "chain": "scarf_front", "material": "scarf", "group": "scarf", "lod": "ref",
             "sweep": {"clumps": 1, "tip": "fringe", "only_fringe": True, "fringe": 9, "fringe_len": 0.95,
                       "fringe_r": 0.2}}]


# ======================================================================================== limbs
PALM_B, PALM_R, PALM_C = [1.85, 2.0, 1.6], 1.45, [0, -1.75, 0.15]       # AD r1-6: clearly bigger, round + puffy
MCUFF_R = [1.45, 1.4]


def limb_parts():
    P_, sole_clip = H.P_, H.sole_clip
    P = []
    for s, sg in (("L", 1), ("R", -1)):
        st = f"sleeve_{s}"
        # slightly puffy sleeve: a soft shoulder puff smooth-unioned into the upper arm, clean forearm
        P.append({"name": f"sleeve_puff_{s}", "bone": f"shoulder_{s}", "shape": "ellipsoid", "center": [0, -2.4, 0],
                  "radii": [2.3, 2.75, 2.25], "material": "coat", "group": f"arm_{s}", "lod": "all",
                  "blend": {"set": st, "k": 1.1}})
        P.append(P_(f"uparm_hd_{s}", f"shoulder_{s}", "rcone", {"a": [0, -1.0, 0], "b": [0, -6.1, 0], "ra": 2.1, "rb": 1.95},
                    "coat", f"arm_{s}", blend={"set": st, "k": 1.0}))
        P.append(P_(f"forearm_hd_{s}", f"elbow_{s}", "rcone", {"a": [0, 0, 0], "b": [0, -4.5, 0], "ra": 1.95, "rb": 1.82},
                    "coat", f"arm_{s}", blend={"set": st, "k": 1.0}))
        P.append(P_(f"cuff_hd_{s}", f"elbow_{s}", "torus", {"R": H.CUFF_R, "r": 0.36, "w": 0.68}, "coat_trim", f"arm_{s}",
                    center=[0, H.CUFF_Y, 0], blend={"set": st, "k": 0.25}))
        # mitten: big round palm, small thumb, soft knit cuff
        P.append(P_(f"palm_{s}", f"hand_{s}", "rbox", {"b": PALM_B, "r": PALM_R}, "mitten", f"arm_{s}",
                    center=PALM_C, blend={"set": f"mitt_{s}", "k": 0.45}))
        a = np.array([-sg * 1.15, -0.95, 1.15])
        dvec = np.array([-sg * math.sin(math.radians(35)) * 0.6, -math.cos(math.radians(35)), math.sin(math.radians(35)) * 0.8])
        dvec /= np.linalg.norm(dvec)
        P.append(P_(f"thumb_hd_{s}", f"hand_{s}", "rcone", {"a": r3(a), "b": r3(a + 1.25 * dvec), "ra": 0.78, "rb": 0.68},
                    "mitten", f"arm_{s}", blend={"set": f"mitt_{s}", "k": 0.45}))
        P.append(P_(f"mitten_cuff_{s}", f"hand_{s}", "torus", {"R": MCUFF_R, "r": 0.45, "w": 0.7}, "mitten", f"arm_{s}",
                    center=[0, 0.05, 0.1], detail={"type": "ridges", "n": 14, "depth": 0.1, "lod": "ref"}))
        # tights
        P.append(P_(f"thigh_hd_{s}", f"hip_{s}", "rcone", {"a": [0, -0.2, 0], "b": [0, -6.5, 0], "ra": 1.75, "rb": 1.45},
                    "pants", f"leg_{s}", blend={"set": f"tights_{s}", "k": 0.6}))
        P.append(P_(f"calf_{s}", f"knee_{s}", "rcone", {"a": [0, 0, 0], "b": [0, -3.0, 0], "ra": 1.45, "rb": 1.25},
                    "pants", f"leg_{s}", blend={"set": f"tights_{s}", "k": 0.6}))
        # boot: shaft with a slight calf curve, toe, sole, heel; puffy fur cuff
        bs = f"boot_{s}"
        P.append(P_(f"shaft_{s}", f"knee_{s}", "cone", {"a": [0, -0.2, 0], "b": [0, -6.3, 0], "ra": 1.95, "rb": 1.72},
                    "boots", f"leg_{s}", blend={"set": bs, "k": 0.8}))
        P.append(P_(f"foot_{s}", f"ankle_{s}", "rbox", {"b": [1.95, 0.95, 2.6], "r": 0.95}, "boots", f"leg_{s}",
                    center=[0, -0.95, 0.55], blend={"set": bs, "k": 0.8}, clip_all=sole_clip([0, -0.95, 0.55])))
        P.append({"name": f"toe_{s}", "bone": f"ankle_{s}", "shape": "ellipsoid", "center": [0, -0.8, 1.75],
                  "radii": [2.0, 1.0, 1.5], "material": "boots", "group": f"leg_{s}", "lod": "all",
                  "blend": {"set": bs, "k": 0.5}, "clip_all": sole_clip([0, -0.8, 1.75], [2.0, 1.0, 1.5])})
        P.append(P_(f"sole_{s}", f"ankle_{s}", "rbox", {"b": [2.05, 0.3, 2.3], "r": 0.25}, "boots", f"leg_{s}",
                    center=[0, -1.6, 0.3], blend={"set": bs, "k": 0.1}, clip_all=sole_clip([0, -1.6, 0.3])))
        P.append(P_(f"welt_{s}", f"ankle_{s}", "rbox", {"b": [2.13, 0.07, 2.38], "r": 0.05}, "boots", f"leg_{s}", lod="ref",
                    center=[0, -1.27, 0.3], blend={"set": bs, "k": 0.0}))
        P.append(P_(f"heel_{s}", f"ankle_{s}", "rbox", {"b": [1.55, 0.6, 0.95], "r": 0.25}, "boots", f"leg_{s}",
                    center=[0, -1.3, -1.25], blend={"set": bs, "k": 0.1}, clip_all=sole_clip([0, -1.3, -1.25])))
        P.append(P_(f"bootcuff_hd_{s}", f"knee_{s}", "torus", {"R": [2.0, 2.0], "r": 0.72, "w": 1.05}, "boot_cuff",
                    f"leg_{s}", center=[0, -0.55, 0.1], detail={"type": "ridges", "n": 18, "depth": 0.1, "lod": "ref"}))
    return P


def seat_chain(c):
    """Bow spring / tail chains re-anchored on the seated knot (same springs, so the same secondary motion)."""
    c = dict(c)
    sg = -1 if c["name"].endswith("_L") else 1
    if c["name"].startswith("bow_spring_"):
        c["anchor"] = r3(KNOT + np.array([sg * 0.9, 0.1, 0.1]))
    elif c["name"].startswith("bow_tail_"):
        c["anchor"] = r3(KNOT + np.array([sg * 0.8, -0.8, -1.0]))
    return c


WAIST = {"bodice": [4.85, 4.3, 4.05], "waist": [2.75, 3.25, 2.3], "hips_coat": [5.35, 2.7, 4.4]}


def main():
    marks = eye_marks()
    with open(os.path.join(ROOT, "data", "variants", "S4_hd.json")) as f:
        hd = json.load(f)
    render = json.loads(json.dumps(hd["render"]))
    spec = {
        "extends": "S4_halfup_bow",
        "name": "S4_hd2",
        "label": "S4 HD2 - refined S4_hd: smooth swept hair sheets, satin bow, clean coat, bigger mittens (r21)",
        "model": "hd",
        "remove_parts": hd["remove_parts"],
        "part_overrides": hd["part_overrides"],
        "render": dict(render, mesh_export={"polish": True, "max_tris": 260000}),
        "ramp_overrides": dict(hd.get("ramp_overrides", {}), ribbon_in=["teal_0", "teal_0"], button=["gold_0", "gold_1"]),
        "material_bands": dict(hd.get("material_bands", {})),
        "add_chains": hd["add_chains"],
        "hd_chains": [seat_chain(c) for c in hd["hd_chains"]],
        "parts": head_parts() + H.eye_ref_parts(marks) + hair_parts() + bow_parts() + coat_parts() + scarf_parts()
                 + limb_parts(),
    }
    # the hair cap joins the crown flow sheets' smooth union
    spec["part_overrides"] = dict(spec["part_overrides"])
    spec["part_overrides"]["hair_cap"] = dict(spec["part_overrides"]["hair_cap"], blend={"set": "cap", "k": 0.0},
                                              center=r3(CAP_C), radii=r3(CAP_R))
    # the legacy hair_back ball is replaced by the layered side / back sheets (its primitive stays the sim collider)
    spec["remove_parts"] = list(spec["remove_parts"]) + ["hair_back"]
    # AD r1-7: waist pinch (narrower waist / lower bodice, the hips flare into the A-line skirt)
    for n, r in WAIST.items():
        spec["part_overrides"][n] = dict(spec["part_overrides"].get(n, {}), radii=r)
    path = os.path.join(ROOT, "data", "variants", "S4_hd2.json")
    with open(path, "w") as f:
        json.dump(spec, f, indent=1)
    print("wrote", path, len(spec["parts"]), "parts")


if __name__ == "__main__":
    main()
