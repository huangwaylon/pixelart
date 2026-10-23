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

# ---- r12 round-2 tuning (reviews docs/review/r12_hd_review_{AD,anim,GD}.md)
SIDELOCK_FRONT_Z = 0.6                       # was 2.8: profile eye glint (AD1)
BOW_LOOP = {"R": [3.4, 1.55], "r": 0.5, "w": 2.8, "taper": 0.35, "round": 0.85}  # AD5 + r13 C (puffy)
BOW_SPRING_GAIN = 0.8
BOW_MAX_DROP = 0.04
PONY_TAPER, PONY_TIP_R, PONY_EXTEND = 0.45, 0.6, 4.5
# round 5 (AD): the run / throw / jump swing frames need a fuller tip radius (a 0.6 tip thins to a 1-px column
# that the silhouette pass trims, leaving a flat cap); every other clip keeps the approved round-4 tip
PONY_SWING = {"tip_r": 0.75, "extend": 1.5}
BOW_TILT, BOW_Y = 26, 11.8
CROWN_LIFT = -0.42                           # GD4: crown clumps 0.12 closer to the cap (1 px crown bump in run NE)
HEM_R, HEM_W, HEM_Y = [8.15, 6.8], 1.15, -5.05   # AD2
CUFF_R, CUFF_Y = [1.65, 1.65], -4.75         # AD4
BELT_R = [3.05, 2.55]
BELT_CLIP = [[0, 0, 1, -0.6]]                # anim1: no belt behind the hips (it grazed the hips and strobed in NE/NW)
PALM_B, MCUFF_R = [1.45, 1.6, 1.2], [1.25, 1.2]
RING = {"ring_w": 0.14}                      # AD3: bang/crown rust highlight arc (legacy hair_style ring_w 0.12)

# ---- r15 (user: "bangs longer, esp. at the sides, gentle slope; forehead/temples too exposed, looks bald" and
# "SE far eye still too close"): docs/review/r15_face_bangs.md
# hime bangs: name, root x, tip x, tip y, out (tip y was C 9.5 / L1 8.3 / L2 8.1 / L3 8.0)
# r15: every bang ~0.5-0.8 longer, the outer ones most (slope down toward the temples); fuller tips (0.05 -> 0.3) so the
# extra length reaches the pixel grid instead of thinning to a sub-pixel point. Centre bang stays shortest (hime notch).
BANGS = [("bang_L3", 4.9, 5.8, 7.2, 0.42), ("bang_L2", 3.1, 3.55, 7.6, 0.5), ("bang_L1", 0.75, 1.55, 7.9, 0.55)]
BANG_C_TIP = 8.6
BANG_R = [1.3, 1.1, 0.3]     # root / mid / tip radius of the 6 side bangs
BANG_MID_Y = 10.6
# (name, root [x, y], mid [x, y], tip [x, y], radii, out): temple bangs sloping from the crown into the side locks;
# kept behind the profile eye (x >= 7.7) so E/W keep every eye pixel
TEMPLE_BANGS = [("bang_T", (6.8, 12.2), (7.7, 9.4), (8.0, 7.2), (1.2, 1.05, 0.2), 0.3)]
SIDELOCK_BACK_Z = 0.4
SIDELOCK_DZ = -1.6     # both side-lock clumps moved back along -z (near-side face width in 3/4)
FACE_CELS = "kawaii_hd"      # None = inherit kawaii_v2; "kawaii_hd" = r15 3/4 far eye (same height as the near eye)
CONTOUR_FAR = 2       # far-eye cheek px in 3/4 (None = same as contour)
# round 2 (AD r15-1..5, anim): bang hem pinned to the eye line - exactly 1 skin row over the lashes in S/SE/SW, outer
# columns hang lower (slope), lone face hair pixels cut, profile skin pockets filled (pipeline/face.py _face_hem)
HEM_PIN = True
LASH_OVER_HAIR = True  # a bang tip dipping onto the lash line (head bob / pitch) is trimmed there, never the lash
MOUTH_BIAS = 3         # 3/4 mouth pull toward the nose bridge (px)
# hair_cap front clip plane [nx, ny, nz, d] (unit-cap coords, keep where n.p >= d); None = legacy [0, 0, -1, -0.22].
# r15: tilted so the cap ends further back only low on the side of the head (cheek / eye rows: +1 px near-side face in
# 3/4: z_n <= 0.02 at the eye row) while the temple above stays covered (z_n <= 0.22 at y_n 0.18, legacy)
CAP_FRONT_CUT = [0, 0.49, -1, -0.133]


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
            pts = [on_ell(CAP_C, CAP_R, slerp(u0, u1, t), lift=CROWN_LIFT) for t in np.linspace(0, 1, 13)]
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
    bangs = BANGS + [(n.replace("_L", "_R"), -xr, -xt, yt, o) for n, xr, xt, yt, o in reversed(BANGS)]
    for name, xr, xt, yt, out in bangs:
        root = [xr, 12.9, cap_z(xr, 12.9, out=-0.35)]
        xm, ym = (xr * 0.4 + xt * 0.6), BANG_MID_Y
        mid = [xm, ym, head_z(xm, ym, out + 0.15)]
        tip = [xt, yt, head_z(xt, yt, out)]
        P.append(part(name, "tube", {"pts": [r3(root), r3(mid), r3(tip)], "r": list(BANG_R), "flat": 0.42,
                                     "flat_c": r3(HEAD_C)}))
    root = [0, 13.1, cap_z(0, 13.1, out=-0.45)]
    mid = [0, 11.0, head_z(0, 11.0, 0.35)]
    tip = [0, BANG_C_TIP, head_z(0, BANG_C_TIP, 0.3)]
    P.append(part("bang_C", "tube", {"pts": [r3(root), r3(mid), r3(tip)], "r": [1.15, 0.9, 0.05], "flat": 0.42,
                                     "flat_c": r3(HEAD_C)}))
    # r15: temple bangs - the outer fringe slopes down past the brow and tucks into the side locks
    for name, (xr, yr), (xm, ym), (xt, yt), rr, out in TEMPLE_BANGS:
        for sg, s in ((1, "L"), (-1, "R")):
            pts = [[sg * xr, yr, cap_z(xr, yr, out=-0.35)], [sg * xm, ym, head_z(xm, ym, out + 0.1)],
                   [sg * xt, yt, head_z(xt, yt, out)]]
            P.append(part(f"{name}_{s}", "tube", {"pts": [r3(p) for p in pts], "r": list(rr), "flat": 0.42,
                                                  "flat_c": r3(HEAD_C)}))
    # --- flat-cut hime side locks: 2 clumps per side, cut straight across at the jaw (cone = flat ends)
    for sg, s in ((1, "L"), (-1, "R")):
        # r12 round 2 (AD1): the front clump sits 0.8 further back than M1 so the profile eye + glint stay on skin
        for nm, z, ybot, dx in (("front", SIDELOCK_FRONT_Z + SIDELOCK_DZ, -0.9, 0.0),
                                ("back", SIDELOCK_BACK_Z + SIDELOCK_DZ, -0.2, 0.55)):
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
              # round 4 (AD blocker): one tapered point at the legacy length (clumps converge; extended past the chain
              # end like the legacy end bead) instead of 3 sub-pixel points that read as a flat cap
              "sweep": {"clumps": 5, "twist": 40, "spread": 0.45, "clump_r": 0.6, "tips": 1, "tip": "sharp", "thickness": 2.3,
                        "taper_len": PONY_TAPER, "side_end": 1.0, "root_len": 0.2, "tip_r": PONY_TIP_R,
                        "extend": PONY_EXTEND, "by_clip": {c: dict(PONY_SWING) for c in ("run", "throw", "jump_sc", "land")}}})
    return P


# ---- r13 user request A/B: anime head construction + modelled eyes (reference geometry)
EYE_MARK = (3.55, 5.55)      # eye centre x, y (head-bone space); z found on the face surface
MOUTH_MARK = (0.0, 2.35)
# r13 D: gait-driven lateral hair sway [amp (units/s^2), phase (cycles), periods per loop] per clip; force in phase with
# the torso lean = counter-phase to the hips, the verlet chains add the lag / follow-through
# round 3 (anim4): walk ~1.5x with a flattened (held) extreme [.., shape 0.4]; run unchanged
SWAY_CURTAIN = {"walk": [620, 0.0, 1, 0.4], "carry_walk": [420, 0.0, 1], "run": [650, 0.0, 1]}
SWAY_PONY = {"walk": [1500, 0.0, 1, 0.4], "carry_walk": [1000, 0.0, 1], "run": [1600, 0.0, 1]}
FACE_SET = {"set": "face", "k": 1.6}


def head_parts():
    """Rounder cranium, cheeks narrowing to a soft pointed chin, a slight cheekbone plane, a jaw line visible in 3/4
    and profile. Replaces the legacy head sphere (which stays as the sim / QA collider)."""
    P = [{"name": "cranium", "bone": "head", "shape": "ellipsoid", "center": [0, 7.6, 0.45], "radii": [8.2, 7.6, 7.6],
          "material": "skin", "group": "head", "blend": dict(FACE_SET), "lod": "all"},
         # lower face: narrower than the cranium (jaw taper), pushed forward
         {"name": "jaw", "bone": "head", "shape": "ellipsoid", "center": [0, 3.9, 1.7], "radii": [6.5, 4.4, 6.35],
          "material": "skin", "group": "head", "blend": dict(FACE_SET), "lod": "all"},
         # chin: soft point, forward and down
         P_("chin", "head", "rcone", {"a": [0, 3.2, 3.9], "b": [0, 0.15, 5.7], "ra": 3.0, "rb": 1.05}, "skin", "head",
            blend=dict(FACE_SET))]
    for sg, s in ((1, "L"), (-1, "R")):
        # cheekbone plane: a flattened pad under each eye that squares the cheek in 3/4
        P.append({"name": f"cheek_{s}", "bone": "head", "shape": "ellipsoid", "center": [sg * 4.2, 4.3, 4.4],
                  "radii": [2.2, 2.0, 1.9], "rot": [0, sg * 28, 0], "material": "skin", "group": "head",
                  "blend": dict(FACE_SET), "lod": "all"})
    return P


def eye_marks():
    """Eye centres on the modelled face surface (head-bone space), used by the sprite face pass for per-eye
    perspective and drawn as dark almond lenses on the hi-res refs / STL only (lod ref)."""
    import sys
    sys.path.insert(0, ROOT)
    from pipeline import sdf
    parts = [dict({"group": "head", "op": "union", "lod": "all"}, **p) for p in head_parts()]
    W = {"head": np.eye(4)}
    prims = []
    for sp in parts:
        prims += sdf._pose_static(sp, W, np.eye(4))
    C = sdf._Compiled(prims)
    out = []
    for sg, (x, y) in ((1, EYE_MARK), (-1, EYE_MARK), (0, MOUTH_MARK)):
        x = sg * x
        lo, hi = 0.0, 12.0
        for _ in range(40):                     # bisection along +z for the front skin surface
            m = (lo + hi) / 2
            d, _ = sdf.scene_sdf(prims, np.array([[x, y, m]]), C)
            lo, hi = (m, hi) if d[0] < 0 else (lo, m)
        out.append([round(x, 3), round(y, 3), round(lo, 3)])
    return out


def eye_ref_parts(marks):
    P = []
    for (x, y, z), s in zip(marks[:2], "LR"):
        yaw = math.degrees(math.atan2(x, 6.0))
        P.append({"name": f"eye_ref_{s}", "bone": "head", "shape": "ellipsoid", "center": [x, y, z - 0.15],
                  "radii": [1.25, 1.55, 0.45], "rot": [0, yaw, 0], "material": "pants", "group": "head", "lod": "ref"})
    return P


def bow_parts():
    """r13 C: puffy bow. Loops are thick rounded band rings (real volume, not plates) riding spring chains (bounce on
    run / jump / land, lag on turns); unequal soft folds (refs); a pinched knot; V-cut tails on their own chains."""
    P = []
    for sg, s in ((-1, "L"), (1, "R")):
        rot = [0, 180, BOW_TILT] if sg < 0 else [0, 0, BOW_TILT]
        zs = 1 if sg < 0 else -1        # local z of the outward (visible) face after the 180 deg yaw
        # round 3 (anim3): rigid in the idle loops (no blips); anim2: never sinks behind the crown
        fol = {"chain": f"bow_spring_{s}", "gain": BOW_SPRING_GAIN, "gain_by_clip": {"idle": 0.0, "carry_idle": 0.0},
               "max_drop": BOW_MAX_DROP, "drop_frame": "world"}
        P.append({"name": f"bow_loop_{s}", "bone": "head", "shape": "torus", "center": [sg * 4.2, BOW_Y, -9.9], "rot": rot,
                  # group = its spring chain: like the pom / scarf, a bouncing loop is secondary motion for the QA height
                  "params": dict(BOW_LOOP), "material": "ribbon", "group": f"bow_spring_{s}", "follow": fol,
                  "blend": {"set": f"loop_{s}", "k": 0.0}, "lod": "all"})
        # unequal soft folds: two creases on the left loop, three on the right, at different heights
        folds = ((0.75, 0.3), (-0.75, -0.3)) if sg < 0 else ((0.95, 0.45), (0.05, -0.1), (-0.85, -0.4))
        dz = BOW_LOOP["R"][1] + BOW_LOOP["r"]
        for c, (y0, y1) in enumerate(folds):
            P.append({"name": f"bow_crease_{s}{c}", "bone": "head", "shape": "capsule", "center": [sg * 4.2, BOW_Y, -9.9],
                      "rot": rot, "params": {"a": [-2.7, y0 * 1.3, zs * dz], "b": [0.9, y1, zs * (dz - 0.08)], "r": 0.26},
                      "material": "ribbon", "group": f"bow_spring_{s}", "op": "subtract", "follow": fol,
                      "blend": {"set": f"loop_{s}", "k": 0.15}, "lod": "ref"})
    # pinched knot: a narrow waisted core (the loops' rounded inner ends pinch into it)
    P.append({"name": "bow_knot", "bone": "head", "shape": "rbox", "center": [0, 10.8, -10.7],
              "params": {"b": [1.05, 1.45, 1.1], "r": 0.65}, "material": "hatcuff", "group": "hat",
              "blend": {"set": "knot", "k": 0.0}, "lod": "all"})
    for sg in (-1, 1):
        P.append({"name": f"knot_groove_{'L' if sg < 0 else 'R'}", "bone": "head", "shape": "capsule",
                  "center": [0, 10.8, -10.7], "params": {"a": [sg * 0.45, -1.0, -1.2], "b": [sg * 0.4, 1.0, -1.2], "r": 0.2},
                  "material": "hatcuff", "group": "hat", "op": "subtract", "blend": {"set": "knot", "k": 0.1}, "lod": "ref"})
    for s in "LR":
        P.append({"name": f"bow_tail_{s}_sweep", "chain": f"bow_tail_{s}", "material": "hatcuff", "group": "hat",
                  "lod": "all", "sweep": {"clumps": 1, "tip": "fork", "fork_depth": 0.6}})
    return P


def loop_chains():
    """Invisible 1-segment spring chains that carry the bow loops (draw_segments False: only the loops render)."""
    out = []
    for sg, s in ((-1, "L"), (1, "R")):
        out.append({"name": f"bow_spring_{s}", "anchor_bone": "head", "anchor": [sg * 1.0, 10.9, -10.6],
                    "rest_dir": [sg * 0.92, 0.38, 0.0], "segments": 1, "seg_len": 3.6, "widths": [1.0],
                    "thickness": 0.5, "material": "ribbon", "group": "hat", "draw_segments": False,
                    "stiffness": 480, "damping": 0.16, "gravity": 160, "collide": False, "max_swing": 15})
    return out


def curtain_chains():
    out = []
    for k, x in enumerate(np.linspace(-4.8, 4.8, 5)):
        out.append({"name": f"curtain_{k}", "anchor_bone": "head", "anchor": r3([x, 8.6, cap_z(x, 8.6, sign=-1, out=-0.4)]),
                    "rest_dir": r3([x * 0.07, -1, -0.22]), "segments": 2, "seg_len": 4.6 if k % 2 == 0 else 4.1,
                    "widths": [1.7, 1.55], "thickness": 0.75, "material": "hair", "group": "head", "stiffness": 260,
                    "damping": 0.15, "gravity": 900, "collide": True, "sway": SWAY_CURTAIN})
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
    P.append(P_("belt_band", "spine", "torus", {"R": BELT_R, "r": 0.45, "w": 0.75}, "coat_trim", "belt",
                center=[0, -0.3, 0.1], clip_all=BELT_CLIP))
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
    # r12 round 2 (AD2/GD5): a 2-px rust hem band at sprite size (legacy y49-50); scallops only on the hi-res refs
    P.append(P_("hem_band", "pelvis", "torus", {"R": HEM_R, "r": 0.45, "w": HEM_W}, "coat_trim", "torso",
                center=[0, HEM_Y, 0.15], detail={"type": "scallop", "n": 16, "depth": 0.45, "y0": HEM_W - 0.9,
                                                 "y1": -HEM_W, "lod": "ref"}))
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


SOLE_Y = -1.95        # GD3: flat sole plane in ankle space (cuts the boot set smooth-min bulge below the sole)
TOE_SPRING = (2.0, 0.5)   # GD3: sole turns up 0.5 per unit forward of z=2.0 (a planted forward foot no longer dips
                           # a pixel below the ground line through the 16 deg camera)
HEEL_SPRING = (-1.4, 0.5)  # GD4: same for the heel back edge (back views of the run stride sat 1 px lower)


def sole_clip(c, radii=(1.0, 1.0, 1.0)):
    """clip_all planes (ankle space: y >= SOLE_Y and the toe spring) in the local frame of a part centred at c
    (ellipsoid parts: local = unit sphere scaled by radii)."""
    z0, k = TOE_SPRING
    out = []
    zh, kh = HEEL_SPRING
    for n, d in (((0.0, 1.0, 0.0), SOLE_Y), ((0.0, 1.0, -k), SOLE_Y - k * z0), ((0.0, 1.0, kh), SOLE_Y + kh * zh)):
        nl = [n[i] * radii[i] for i in range(3)]
        out.append([round(v, 4) for v in nl] + [round(d - sum(n[i] * c[i] for i in range(3)), 4)])
    return out


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
        # r12 round 2 (AD4): slimmer cuff set back from the wrist so the teal mitten always wins over it
        P.append(P_(f"cuff_hd_{s}", f"elbow_{s}", "torus", {"R": CUFF_R, "r": 0.35, "w": 0.68}, "coat_trim", f"arm_{s}",
                    center=[0, CUFF_Y, 0]))
        # mitten: rounded palm box, thumb at 35 deg with a gap, ribbed knit cuff
        P.append(P_(f"palm_{s}", f"hand_{s}", "rbox", {"b": PALM_B, "r": 1.0}, "mitten", f"arm_{s}",
                    center=[0, -1.25, 0.15]))
        a = np.array([-sg * 0.85, -0.5, 0.95])
        dvec = np.array([-sg * math.sin(math.radians(35)) * 0.6, -math.cos(math.radians(35)), math.sin(math.radians(35)) * 0.8])
        dvec /= np.linalg.norm(dvec)
        P.append(P_(f"thumb_hd_{s}", f"hand_{s}", "rcone", {"a": r3(a), "b": r3(a + 1.3 * dvec), "ra": 0.68, "rb": 0.58},
                    "mitten", f"arm_{s}"))
        P.append(P_(f"mitten_cuff_{s}", f"hand_{s}", "torus", {"R": MCUFF_R, "r": 0.42, "w": 0.68}, "mitten", f"arm_{s}",
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
                    center=[0, -0.95, 0.55], blend={"set": bs, "k": 0.7}, clip_all=sole_clip([0, -0.95, 0.55])))
        P.append({"name": f"toe_{s}", "bone": f"ankle_{s}", "shape": "ellipsoid", "center": [0, -0.8, 1.75],
                  "radii": [2.0, 1.0, 1.5], "material": "boots", "group": f"leg_{s}", "lod": "all",
                  "blend": {"set": bs, "k": 0.35}, "clip_all": sole_clip([0, -0.8, 1.75], [2.0, 1.0, 1.5])})
        P.append(P_(f"sole_{s}", f"ankle_{s}", "rbox", {"b": [2.05, 0.3, 2.3], "r": 0.25}, "boots", f"leg_{s}",
                    center=[0, -1.6, 0.3], blend={"set": bs, "k": 0.1}, clip_all=sole_clip([0, -1.6, 0.3])))
        P.append(P_(f"welt_{s}", f"ankle_{s}", "rbox", {"b": [2.13, 0.07, 2.38], "r": 0.05}, "boots", f"leg_{s}", lod="ref",
                    center=[0, -1.27, 0.3], blend={"set": bs, "k": 0.0}))
        P.append(P_(f"heel_{s}", f"ankle_{s}", "rbox", {"b": [1.55, 0.6, 0.95], "r": 0.2}, "boots", f"leg_{s}",
                    center=[0, -1.3, -1.25], blend={"set": bs, "k": 0.1}, clip_all=sole_clip([0, -1.3, -1.25])))
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


def pony_chain():
    """The legacy pony chain (S4_halfup_bow add_chains) with the r13 gait sway."""
    with open(os.path.join(ROOT, "data", "variants", "S4_halfup_bow.json")) as f:
        base = json.load(f)["add_chains"]
    # round 3 (Anim5): the ponytail is its own group, so the depth-break line separates it from the back curtain
    return [dict(c, sway=SWAY_PONY, group="pony") if c["name"] == "pony" else c for c in base]


def main():
    marks = eye_marks()
    spec = {
        "extends": "S4_halfup_bow",
        "name": "S4_hd",
        "label": "S4 HD - SDF reference model (r12 M1-M3: hair, bow, coat, scarf, limbs)",
        "model": "hd",
        "remove_parts": ["head", "fringe", "sidelock_L", "sidelock_R", "ribbon_loop_0", "ribbon_loop_1", "ribbon_knot",
                         "ribbon_tail_L", "ribbon_tail_R",
                         # M2/M3: body ellipsoids replaced by HD parts (legacy prims stay as sim/QA colliders)
                         "skirt_coat", "hem", "belt", "collar", "scarf_wrap1", "scarf_wrap2", "scarf_knot"]
                        + [f"{n}_{s}" for s in "LR" for n in ("uparm", "forearm", "cuff", "mitten", "thumb", "thigh",
                                                              "shin", "boot", "bootcuff")],
        "part_overrides": {"hair_cap": {"blend": {"set": "cap", "k": 0.0}, "vote": "hair|head",
                                        **({"clip_any": [list(CAP_FRONT_CUT), [0, 1, 0, 0.32]]}
                                           if CAP_FRONT_CUT is not None else {})},
                           "hair_back": {"vote": "hair|head"},
                           **{n: {"blend": {"set": "torso", "k": 0.8}} for n in ("bodice", "waist", "hips_coat")}},
        "render": {"hair_style": dict(RING),
                   # r13 B: sprite face eyes at their own projected modelled eye positions (perspective)
                   "face_eyes": {"markers": marks[:2], "mouth": marks[2], "gap": 2, "contour": 1,
                                 "gap_front": 3, "mouth_bias": MOUTH_BIAS,   # round 3: AD4 locked S bridge, AD5 mouth
                                 **({"contour_far": CONTOUR_FAR} if CONTOUR_FAR is not None else {}),
                                 **({"lash_over_hair": True} if LASH_OVER_HAIR else {}),
                                 **({"hem_pin": True} if HEM_PIN else {})},
                   **({"face_cels": FACE_CELS} if FACE_CELS else {}),
                   "lineart": {"keep_selout_runs": ["ribbon", "hair"], "skin_edge_dark": True,
                               "ring_trim": {"margin": 2, "min_run": 3, "stop_at": ["ribbon", "hatcuff"],
                                             "fill_gaps": 2}},   # round 3 AD1 head rust only; round 4 no 1-px arc break
                   # anim3: bow loop vs raised teal mitten get a 1 px teal_0 separation (same fill colour)
                   "separate_materials": [["ribbon", "mitten"]],
                   # round 3 (AD2 / anim1): designed bow volume - 2 px teal_2 highlight + 1 teal_0 fold per loop
                   "final_orphan_pass": True,
                   "bow_shine": {"material": "ribbon", "hi": "teal_2", "fold": "teal_0", "knot": "hatcuff", "min_px": 7},
                   # anim2 (round 2) + anim3 (round 3): hold 1-frame crown, bow and scarf-tail flicker in the idle loops
                   "temporal_hold": {"clips": ["idle", "carry_idle"], "rows": 30,
                                     "colors": ["outline", "plum_0", "hair_1", "hair_2", "teal_0", "teal_1", "teal_2", "mauve", "oat_1"]}},
        "add_chains": pony_chain(),
        "hd_chains": tail_chains() + curtain_chains() + loop_chains(),
        "parts": head_parts() + eye_ref_parts(marks) + hair_parts() + bow_parts() + coat_parts() + scarf_parts()
                 + limb_parts(),
    }
    path = os.path.join(ROOT, "data", "variants", "S4_hd.json")
    with open(path, "w") as f:
        json.dump(spec, f, indent=1)
    print("wrote", path, len(spec["parts"]), "parts")


if __name__ == "__main__":
    main()
