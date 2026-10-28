"""Animation director: writes the dirpose/1 key + cycle pose JSONs to hybrid/anim/poses/.

  .venv/bin/python tools/hybrid/anim/make_poses.py

Every number here is the motion bible (hybrid/ANIM_DIRECTION.md) made executable.  Character space:
she faces -Y, +X = her LEFT (katana hand), +Z up.  rot X+ = top tips FORWARD, Z+ = front turns to her
LEFT, Y+ = top tips to her LEFT.  1 sprite px ~ 0.059 rig units vertically (cog z), ~0.051 across.
Preview / convert: tools/hybrid/anim/pose_preview.py (Blender).
"""
import json, math, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = os.path.join(ROOT, "hybrid", "anim", "poses")
os.makedirs(OUT, exist_ok=True)
PXV = 0.059
TAU = 2 * math.pi
ALL8 = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
written = []


def r1(x):
    return round(x, 3)


def save(name, ops, intent, dirs=("SE",), **kw):
    P = {"format": "dirpose/1", "name": name, "dirs": list(dirs), "ops": ops, "intent": intent}
    P.update(kw)
    json.dump(P, open(os.path.join(OUT, name + ".json"), "w"), indent=1)
    written.append(name)


def chain(prefix, axis, base, n=5, grow=1.0):
    """chain angles: base deg at the root, growing toward the tip by `grow` per segment ratio."""
    return ["chain", prefix, axis, [r1(base * grow ** i) for i in range(n)]]


# ------------------------------------------------------------------ IDLE (6 f)
IDLE_MS = [220, 140, 140, 220, 140, 140]
# breathing: f0 = exhale settled (low, hold), f3 = inhale top (hold); chest leads, head 1 f late,
# bun 1 f late, bow 2 f late, ribbons a travelling wave (root 1 f, tip 3 f late)
IDLE = {
    "cog_z_px": [-1.0, -0.5, 0.0, 0.2, -0.3, -0.8],     # hem/knees: 1 px
    "chest_x": [3.0, 1.0, -1.5, -2.5, -0.5, 2.0],      # slump on exhale, lift on inhale -> crown 2 px
    "shoulder": [-2.0, 0.0, 3.0, 4.0, 1.5, -1.0],      # shoulders rise on the inhale (deg)
    "head_x": [1.5, 2.5, 0.5, -1.5, -2.5, -0.5],       # 1 f behind chest
    "hips_y": [0.8, 0.3, -0.3, -0.8, -0.3, 0.3],       # weight rocks into the hip
    "bun_x": [-1.0, 1.5, 3.0, 1.0, -1.5, -3.0],        # 1 f behind the head
    "skirt_tail_x": [2.0, 3.0, 1.0, -2.0, -3.0, -1.0],  # 1 f behind the cog
    "sleeve_x": [-2.0, 2.0, 4.0, 2.0, -2.0, -4.0],
    "sword_z": [1.0, 2.0, 1.0, -1.0, -2.0, -1.0],      # tip drifts +-1 px, 2 f behind
}
for f in range(6):
    ph = TAU * f / 6
    ops = [["base", "idle_{D}"],
           ["move", "cog", [0, 0, r1(IDLE["cog_z_px"][f] * PXV)]],
           ["rot", "chest", "X", IDLE["chest_x"][f]],
           ["rot", "shoulder.L", "Y", -IDLE["shoulder"][f]], ["rot", "shoulder.R", "Y", IDLE["shoulder"][f]],
           ["rot", "head", "X", IDLE["head_x"][f]],
           ["rot", "hips", "Y", IDLE["hips_y"][f]],
           ["rot", "bun", "X", IDLE["bun_x"][f]],
           ["rot", "bow", "X", IDLE["bun_x"][(f - 1) % 6] * 1.5],
           ["scarf_hang", r1(ph - 0.9), 0.0, 0.16],
           chain("skirt.tail", "X", IDLE["skirt_tail_x"][f], 3, 1.1),
           ["rot", "sleeve.L", "X", IDLE["sleeve_x"][f]], ["rot", "sleeve.R", "X", IDLE["sleeve_x"][(f + 1) % 6]],
           ["rot", "sword", "Z", IDLE["sword_z"][f]]]
    save(f"idle_f{f}", ops, {
        "anim": "idle", "frame": f, "ms": IDLE_MS[f],
        "beat": ["exhale settled (low hold)", "inhale rising", "inhale", "inhale top (hold)", "exhale", "exhale falling"][f],
        "crown_px_vs_f0": [0, 1, 2, 2, 1, 0][f], "hem_px_vs_f0": [0, 0, 1, 1, 1, 0][f],
        "expression": "calm half-lid; f3 has an optional blink alt (idle_blink) every 3rd loop",
    }, dirs=("SE", "S", "NW"), no_dir_turn=True)
# turn key = idle f1 (neutral mid-breath) in all 8 directions
save("turn", json.load(open(os.path.join(OUT, "idle_f1.json")))["ops"],
     {"anim": "idle", "frame": 1, "note": "STANDARD TEST SET turn_<DIR>.png: idle neutral key"}, dirs=ALL8, no_dir_turn=True)

# ------------------------------------------------------------------ WALK (8 f, 100 ms)
# L foot track (y, z, heel, toe) per frame; R = L shifted by 4
WALK_L = [(-0.32, 0.0, 0, 14), (-0.17, 0.0, 0, 0), (-0.02, 0.0, 0, 0), (0.13, 0.0, 8, 0),
          (0.28, 0.0, 30, 0), (0.16, 0.10, 35, 0), (-0.04, 0.17, 15, 0), (-0.24, 0.08, 0, 10)]
WALK_COG = [-0.06, -0.17, -0.06, 0.03]        # contact, DOWN (2 px under contact), passing, UP (+1 px)
WALK_NAMES = ["contact", "down", "passing", "up"]


def walk_ops(f):
    c = math.cos(TAU * f / 8)
    cl = math.cos(TAU * (f - 1) / 8)          # arms 1 f behind the legs
    cz = WALK_COG[f % 4]
    czp = WALK_COG[(f - 1) % 4]
    L = WALK_L[f]
    R = WALK_L[(f + 4) % 8]
    ops = [["base", "rest"],
           ["move", "cog", [r1(0.03 * math.sin(TAU * (f + 2) / 8)), -0.02, r1(cz)]],
           ["rot", "hips", "Z", r1(-8 * c)],
           ["rot", "hips", "Y", [0, -3, -1, 0, 0, 3, 1, 0][f]],
           ["rot", "spine", "X", 4],
           ["rot", "chest", "Z", r1(10 * c)],
           ["rot", "head", "X", r1(-6 + [-1, 1, 2, 0][f % 4])],
           ["rot", "head", "Z", r1(-3 * c)],
           ["feet", "L", [0.15, L[0], L[1]], 6, L[2], L[3]],
           ["feet", "R", [-0.15, R[0], R[1]], -6, R[2], R[3]],
           ["knee", "L", [0.1, -1, 0]], ["knee", "R", [-0.1, -1, 0]],
           ["rot", "upper_arm.R", "X", r1(-22 * cl)], ["rot", "forearm.R", "X", r1(-12 - 8 * max(0, cl))],
           ["rot", "upper_arm.R", "Y", 8],
           ["rot", "upper_arm.L", "X", r1(12 * cl)], ["rot", "upper_arm.L", "Y", -10],
           ["sword", r1(2 + 8 * math.cos(TAU * (f - 2) / 8)), 38],
           ["scarf_hang", r1(TAU * f / 8), 1.0, 0.10],
           chain("skirt.tail", "X", r1(8 - 45 * czp), 3, 1.1),
           ["rot", "skirt.F", "X", r1(-4 * c)],
           ["rot", "sleeve.L", "X", r1(-10 * (math.cos(TAU * (f - 1) / 8) - math.cos(TAU * (f - 2) / 8)) * 2)],
           ["rot", "sleeve.R", "X", r1(10 * (math.cos(TAU * (f - 1) / 8) - math.cos(TAU * (f - 2) / 8)) * 2)],
           ["rot", "bun", "X", r1(-30 * (czp - WALK_COG[(f - 2) % 4]))],
           ["rot", "bow", "X", r1(-40 * (WALK_COG[(f - 2) % 4] - WALK_COG[(f - 3) % 4]))]]
    return ops


for f in range(8):
    k = f % 4
    save(f"walk_f{f}", walk_ops(f), {"anim": "walk", "frame": f, "ms": 100, "beat": WALK_NAMES[k] + (" (L lead)" if f < 4 else " (R lead)"),
                                     "cog_px": round(WALK_COG[k] / PXV, 1), "expression": "calm"})
    if f < 4:
        save(f"walk_SE_k{f}", walk_ops(f), {"anim": "walk", "frame": f, "beat": WALK_NAMES[k], "test_set": True})

# ------------------------------------------------------------------ RUN (8 f, 70 ms)
RUN_L = [(-0.36, 0.0, 0, 12), (-0.12, 0.0, 0, 0), (0.16, 0.0, 35, 0), (0.38, 0.14, 60, 0),
         (0.30, 0.34, 75, 0), (0.02, 0.36, 40, 0), (-0.28, 0.26, 5, 10), (-0.42, 0.10, 0, 18)]
RUN_COG = [-0.06, -0.22, -0.06, 0.10]      # contact, DOWN (squash), push, FLIGHT (stretch): 4 px
RUN_NAMES = ["contact", "down (squash)", "push-off", "flight (stretch)"]
RUN_SCALE = [(1, 1, 1), (1.03, 1.03, 0.95), (1, 1, 1), (0.98, 0.98, 1.04)]


def run_ops(f):
    c = math.cos(TAU * f / 8)
    cl = math.cos(TAU * (f - 0.7) / 8)
    k = f % 4
    L, R = RUN_L[f], RUN_L[(f + 4) % 8]
    czp = RUN_COG[(f - 1) % 4]
    return [["base", "rest"],
            ["move", "cog", [0, -0.09, RUN_COG[k]]],
            ["scale", "cog", list(RUN_SCALE[k])],
            ["rot", "hips", "Z", r1(-12 * c)],
            ["rot", "spine", "X", 20], ["rot", "chest", "X", 5],
            ["rot", "chest", "Z", r1(14 * c)],
            ["rot", "head", "X", r1(-12 + [0, 2, 0, -1][k])],
            ["rot", "head", "Z", r1(-5 * c)],
            ["feet", "L", [0.14, L[0], L[1]], 4, L[2], L[3]],
            ["feet", "R", [-0.14, R[0], R[1]], -4, R[2], R[3]],
            ["knee", "L", [0.05, -1, 0.1]], ["knee", "R", [-0.05, -1, 0.1]],
            ["rot", "upper_arm.R", "X", r1(-40 * cl)], ["rot", "upper_arm.R", "Y", 12],
            ["rot", "forearm.R", "X", -70],
            ["rot", "upper_arm.L", "X", r1(30 + 12 * cl)], ["rot", "upper_arm.L", "Y", -18],
            ["sword", r1(72 + 6 * math.cos(TAU * (f - 2) / 8)), r1(12 + 4 * math.sin(TAU * (f - 1) / 4))],
            ["scarf_run", r1(f / 8)],
            chain("skirt.tail", "X", r1(18 - 50 * czp), 3, 1.15),
            ["rot", "skirt.B", "X", 10],
            ["rot", "sleeve.L", "X", r1(28 + 8 * math.sin(TAU * (f - 1) / 4))],
            ["rot", "sleeve.R", "X", r1(28 + 8 * math.sin(TAU * (f - 1) / 4))],
            ["rot", "bun", "X", r1(-4 - 25 * (czp - RUN_COG[(f - 2) % 4]))],
            ["rot", "bow", "X", r1(-8 - 35 * (RUN_COG[(f - 2) % 4] - RUN_COG[(f - 3) % 4]))]]


for f in range(8):
    k = f % 4
    save(f"run_f{f}", run_ops(f), {"anim": "run", "frame": f, "ms": 70, "beat": RUN_NAMES[k] + (" (L lead)" if f < 4 else " (R lead)"),
                                   "cog_px": round(RUN_COG[k] / PXV, 1), "squash_stretch": RUN_SCALE[k],
                                   "smear": "swing-leg stretch smear + 1 px speed lines" if k == 3 else None,
                                   "expression": "focused (frown 0.5)"},
         dirs=("SE", "E"))

# ------------------------------------------------------------------ SLASH (attack1, 6 f)
FEET_SLASH = {"L": (0.34, -0.38), "R": (-0.32, 0.32)}
SLASH = [
    # f0 gather
    dict(cog=(-0.02, 0.04, -0.06), hipsZ=-8, spineX=-4, chestZ=-18, headZ=10, headX=2,
         hand=((-0.28, -0.20, 1.32), (-0.55, 0.40, 0.73), None, 0.5), L=(0.32, -0.34, -20, 0, 0), R=(-0.30, 0.30, 30, 0, 0),
         scarfZ=6, sleeveZ=8, tailZ=6, bunZ=2, expr={"expr_frown": 1}),
    # f1 COIL (k0)
    dict(cog=(-0.04, 0.08, -0.15), hipsZ=-18, spineX=-6, chestZ=-34, headZ=24, headX=6,
         hand=((-0.40, 0.0, 1.36), (-0.45, 0.70, 0.55), None, 0.5), L=(0.34, -0.38, -25, 8, 0), R=(-0.32, 0.30, 35, 0, 0),
         scarfZ=12, sleeveZ=16, tailZ=12, bunZ=4, expr={"expr_frown": 1}),
    # f2 SMEAR (k1): mid-swing, blade straight ahead, body half unwound, lunge starts
    dict(cog=(0.0, -0.06, -0.12), hipsZ=4, spineX=6, chestZ=2, headZ=-4, headX=4,
         hand=((0.0, -0.58, 1.12), (0.05, -1.0, 0.02), (0.0, 0.0, -1.0), 0.5), L=(0.38, -0.46, -30, 0, 0), R=(-0.32, 0.32, 30, 15, 0),
         scarfZ=-15, sleeveZ=-26, tailZ=-12, bunZ=-4, expr={"expr_frown": 1, "expr_wide": 0.3}),
    # f3 IMPACT (k2): hit-stop pose, blade at the far end of the arc, full lunge
    dict(cog=(0.04, -0.12, -0.18), hipsZ=14, spineX=8, chestZ=24, headZ=-14, headX=4,
         hand=((0.20, -0.60, 1.16), (0.86, -0.50, 0.04), (0.5, -1.0, 0.0), 0.5), L=(0.42, -0.46, -30, 0, 0), R=(-0.36, 0.36, 30, 22, 0),
         scarfZ=-10, sleeveZ=-20, tailZ=-14, bunZ=-6, expr={"expr_frown": 1}),
    # f4 FOLLOW-THROUGH (k3): blade carries past and drops, chest overshoots, cloth whips past
    dict(cog=(0.05, -0.10, -0.13), hipsZ=18, spineX=6, chestZ=36, headZ=-20, headX=2,
         hand=((0.34, -0.40, 1.04), (0.60, 0.50, -0.55), (0.0, 0.0, -1.0), 0.5), L=(0.42, -0.46, -30, 0, 0), R=(-0.36, 0.36, 30, 14, 0),
         scarfZ=10, sleeveZ=18, tailZ=10, bunZ=4, expr={"expr_frown": 0.6}),
    # f5 SETTLE: back to low guard on a different (lower) arc, 1 px overshoot down
    dict(cog=(0.02, -0.04, -0.09), hipsZ=6, spineX=4, chestZ=10, headZ=-6, headX=1,
         hand=((0.22, -0.40, 0.98), (0.55, -0.55, -0.55), None, 0.5), L=(0.38, -0.42, -25, 0, 0), R=(-0.34, 0.34, 30, 0, 0),
         scarfZ=4, sleeveZ=6, tailZ=4, bunZ=1, expr={"expr_frown": 0.4}),
]
SLASH_MS = [50, 90, 40, 60, 90, 120]
SLASH_BEAT = ["gather", "COIL (anticipation extreme)", "SMEAR (blade-arc)", "IMPACT (hit-stop)", "FOLLOW-THROUGH (overlap)", "settle"]


def slash_ops(k):
    s = SLASH[k]
    ops = [["base", "rest"], ["move", "cog", list(s["cog"])],
           ["rot", "hips", "Z", s["hipsZ"]], ["rot", "spine", "X", s["spineX"]], ["rot", "chest", "Z", s["chestZ"]],
           ["rot", "head", "Z", s["headZ"]], ["rot", "head", "X", s["headX"]]]
    for side in ("L", "R"):
        x, y, yaw, heel, toe = s[side]
        ops.append(["feet", side, [x, y, 0.0], yaw, heel, toe])
    ops += [["knee", "L", [0.8, -1.0, 0]], ["knee", "R", [-0.6, -0.6, 0]]]
    c, d, e, eo = s["hand"]
    ops.append(["two_hand", list(c), list(d), list(e) if e else None, eo])
    ops += [chain("scarf.L", "Z", s["scarfZ"], 5, 1.12), chain("scarf.R", "Z", s["scarfZ"], 5, 1.12),
            ["rot", "sleeve.L", "Z", s["sleeveZ"]], ["rot", "sleeve.R", "Z", s["sleeveZ"]],
            ["rot", "skirt.B", "Z", s["tailZ"]], chain("skirt.tail", "Z", s["tailZ"], 3, 1.0),
            ["rot", "bun", "Z", s["bunZ"]], ["rot", "bow", "Z", s["bunZ"] * 1.8],
            ["props", s["expr"]]]
    return ops


for f in range(6):
    save(f"slash_f{f}", slash_ops(f), {"anim": "attack1/slash", "frame": f, "ms": SLASH_MS[f], "beat": SLASH_BEAT[f],
                                       "smear": f == 2, "hitstop": f == 3}, dirs=("SE", "E", "NW"))
for k, f in enumerate([1, 2, 3, 4]):
    save(f"slash_SE_k{k}", slash_ops(f), {"anim": "slash", "frame": f, "beat": SLASH_BEAT[f], "test_set": True})

# ------------------------------------------------------------------ OVERHEAD SLASH (attack3, 9 f)
OH = [
    dict(n="dip", cog=(0, 0.02, -0.10), spineX=8, chestX=0, headX=4, hand=((0.14, -0.42, 1.00), (0.25, -0.75, 0.30), None, 0.5),
         L=(0.30, -0.30, -20, 0), R=(-0.28, 0.28, 25, 0), sc=(1.03, 1.03, 0.95), scarfX=0, tailX=0, expr={"expr_frown": 1}),
    dict(n="rise", cog=(0, 0.04, 0.0), spineX=-4, chestX=-2, headX=-4, hand=((0.24, -0.34, 1.45), (0.30, 0.0, 1.0), (0, -1, 0), 0.6),
         L=(0.30, -0.30, -20, 12), R=(-0.28, 0.28, 25, 25), sc=(1, 1, 1), scarfX=-8, tailX=-6, expr={"expr_frown": 1}),
    dict(n="APEX COIL", cog=(0, 0.06, 0.03), spineX=-10, chestX=-8, headX=-8, hand=((0.34, -0.40, 1.55), (0.55, 0.20, 0.81), (0, -1, 0), 0.6),
         L=(0.30, -0.30, -20, 18), R=(-0.28, 0.28, 25, 30), sc=(0.97, 0.97, 1.05), scarfX=-14, tailX=-8, expr={"expr_frown": 1, "expr_wide": 0.3}),
    dict(n="SMEAR 1 (arc over the top)", cog=(0, -0.04, -0.06), spineX=12, chestX=6, headX=2, hand=((0.16, -0.62, 1.42), (0.15, -0.95, 0.28), (0, 0, -1), 0.5),
         L=(0.30, -0.44, -25, 0), R=(-0.28, 0.36, 25, 15), sc=(1, 1, 1), scarfX=-20, tailX=-12, expr={"expr_frown": 1}),
    dict(n="SMEAR 2 / IMPACT (hit-stop)", cog=(0, -0.10, -0.26), spineX=22, chestX=10, headX=2, hand=((0.10, -0.66, 0.82), (0.08, -0.88, -0.47), (0, 0, -1), 0.6),
         L=(0.30, -0.50, -25, 0), R=(-0.28, 0.42, 25, 22), sc=(1.06, 1.06, 0.90), scarfX=-6, tailX=-4, expr={"expr_frown": 1}),
    dict(n="impact hold (cloth keeps falling)", cog=(0, -0.10, -0.27), spineX=22, chestX=10, headX=4, hand=((0.10, -0.66, 0.82), (0.08, -0.88, -0.47), (0, 0, -1), 0.6),
         L=(0.30, -0.50, -25, 0), R=(-0.28, 0.42, 25, 22), sc=(1.05, 1.05, 0.92), scarfX=18, tailX=14, expr={"expr_frown": 1}),
    dict(n="rebound (follow-through)", cog=(0, -0.08, -0.20), spineX=16, chestX=6, headX=2, hand=((0.10, -0.62, 0.88), (0.08, -0.92, -0.36), (0, 0, -1), 0.6),
         L=(0.30, -0.48, -25, 0), R=(-0.28, 0.40, 25, 15), sc=(1.02, 1.02, 0.97), scarfX=22, tailX=10, expr={"expr_frown": 0.8}),
    dict(n="recover", cog=(0, -0.04, -0.10), spineX=8, chestX=2, headX=0, hand=((0.20, -0.46, 0.98), (0.45, -0.60, -0.55), None, 0.5),
         L=(0.30, -0.40, -22, 0), R=(-0.28, 0.34, 25, 0), sc=(1, 1, 1), scarfX=6, tailX=-4, expr={"expr_frown": 0.5}),
    dict(n="settle", cog=(0, -0.02, -0.06), spineX=5, chestX=0, headX=-2, hand=((0.22, -0.40, 0.98), (0.55, -0.55, -0.55), None, 0.5),
         L=(0.30, -0.36, -20, 0), R=(-0.28, 0.30, 25, 0), sc=(1, 1, 1), scarfX=0, tailX=0, expr={"expr_frown": 0.3}),
]
OH_MS = [70, 70, 110, 40, 60, 90, 90, 90, 110]
for f, s in enumerate(OH):
    ops = [["base", "rest"], ["move", "cog", list(s["cog"])], ["scale", "cog", list(s["sc"])],
           ["rot", "spine", "X", s["spineX"]], ["rot", "chest", "X", s["chestX"]], ["rot", "chest", "Z", -10],
           ["rot", "head", "X", s["headX"]], ["rot", "head", "Z", 8]]
    for side in ("L", "R"):
        x, y, yaw, heel = s[side]
        ops.append(["feet", side, [x, y, 0.0], yaw, heel, 0])
    ops += [["knee", "L", [0.3, -1, 0]], ["knee", "R", [-0.3, -1, 0]]]
    c, d, e, eo = s["hand"]
    ops.append(["two_hand", list(c), list(d), list(e) if e else None, eo])
    ops += [chain("scarf.L", "X", s["scarfX"], 5, 1.1), chain("scarf.R", "X", s["scarfX"], 5, 1.1),
            ["rot", "skirt.B", "X", s["tailX"]], chain("skirt.tail", "X", s["tailX"], 3, 1.1),
            ["rot", "sleeve.L", "X", -s["scarfX"]], ["rot", "sleeve.R", "X", -s["scarfX"]],
            ["rot", "bun", "X", r1(s["scarfX"] * 0.25)], ["rot", "bow", "X", r1(s["scarfX"] * 0.45)],
            ["props", s["expr"]]]
    save(f"overhead_f{f}", ops, {"anim": "attack3/overhead_slash", "frame": f, "ms": OH_MS[f], "beat": s["n"],
                                 "squash_stretch": s["sc"], "smear": f in (3, 4), "hitstop": f == 4}, dirs=("SE", "E"))

# ------------------------------------------------------------------ JUMP (6 f)
JUMP_MS = [80, 60, 150, 80, 90, 110]
J = {}
J[0] = [["base", "rest"], ["move", "cog", [0, 0.03, -0.28]], ["scale", "cog", [1.06, 1.06, 0.90]],
        ["rot", "spine", "X", 13], ["rot", "chest", "X", 4], ["rot", "head", "X", -18],
        ["feet", "L", [0.18, -0.08, 0], 10, 0, 0], ["feet", "R", [-0.18, 0.08, 0], -10, 0, 0],
        ["knee", "L", [0.25, -1, 0]], ["knee", "R", [-0.25, -1, 0]],
        ["rot", "upper_arm.R", "X", 40], ["rot", "upper_arm.L", "X", 30], ["rot", "upper_arm.L", "Y", -15],
        ["sword", 45, 14],
        ["scarf_hang", 0.0, 0.0, 0.05], chain("skirt.tail", "X", -4, 3, 1.0),
        ["rot", "sleeve.L", "X", -12], ["rot", "sleeve.R", "X", -12], ["rot", "bun", "X", 4], ["rot", "bow", "X", 6],
        ["props", {"expr_frown": 0.6}]]
J[1] = [["base", "rest"], ["move", "cog", [0, 0.0, 0.06]], ["scale", "cog", [0.96, 0.96, 1.07]],
        ["rot", "spine", "X", -6], ["rot", "head", "X", -12],
        ["feet", "L", [0.10, 0.0, 0.10], 0, 55, 0], ["feet", "R", [-0.10, 0.06, 0.12], 0, 60, 0],
        ["knee", "L", [0.0, -1, 0]], ["knee", "R", [0.0, -1, 0]],
        ["rot", "upper_arm.R", "X", -70], ["rot", "upper_arm.R", "Y", 20],
        ["rot", "upper_arm.L", "X", -35], ["rot", "upper_arm.L", "Y", -35],
        ["sword", -35, -25],
        ["scarf_hang", 0.0, 0.0, 0.0], chain("scarf.L", "X", -8, 5, 1.0), chain("scarf.R", "X", -8, 5, 1.0),
        chain("skirt.tail", "X", -10, 3, 1.0), ["rot", "skirt.F", "X", 8],
        ["rot", "sleeve.L", "X", 30], ["rot", "sleeve.R", "X", 40], ["rot", "bun", "X", -5], ["rot", "bow", "X", -8],
        ["props", {"expr_wide": 0.6}]]
J[2] = [["base", "jump_apex"], ["props", {"expr_smile": 1}]]
J[3] = [["base", "rest"], ["move", "cog", [0, 0, 0.02]],
        ["rot", "spine", "X", 6], ["rot", "head", "X", -4],
        ["feet", "L", [0.12, -0.10, 0.05], 6, 30, 0], ["feet", "R", [-0.12, 0.10, 0.12], -6, 35, 0],
        ["knee", "L", [0.1, -1, 0]], ["knee", "R", [-0.1, -1, 0]],
        ["rot", "upper_arm.L", "Y", -50], ["rot", "upper_arm.R", "Y", 50], ["rot", "forearm.R", "Y", 20],
        ["sword", -10, -5],
        ["rot", "skirt.L", "Y", -30], ["rot", "skirt.R", "Y", 30], ["rot", "skirt.F", "X", -14],
        ["rot", "skirt.B", "X", 16], chain("skirt.tail", "X", 14, 3, 1.0),
        chain("scarf.L", "X", 18, 5, 0.9), chain("scarf.R", "X", 18, 5, 0.9),
        ["rot", "sleeve.L", "Y", -40], ["rot", "sleeve.R", "Y", 40], ["rot", "bun", "X", -6], ["rot", "bow", "X", -12],
        ["props", {"expr_wide": 0.5}]]
J[4] = [["base", "rest"], ["move", "cog", [0, -0.02, -0.31]], ["scale", "cog", [1.08, 1.08, 0.88]],
        ["rot", "spine", "X", 14], ["rot", "head", "X", -8],
        ["feet", "L", [0.22, -0.08, 0], 12, 0, 0], ["feet", "R", [-0.22, 0.08, 0], -12, 0, 0],
        ["knee", "L", [0.35, -1, 0]], ["knee", "R", [-0.35, -1, 0]],
        ["rot", "upper_arm.R", "X", -20], ["rot", "upper_arm.R", "Y", 35],
        ["rot", "upper_arm.L", "Y", -30], ["sword", 15, 20],
        ["rot", "skirt.L", "Y", -18], ["rot", "skirt.R", "Y", 18], ["rot", "skirt.B", "X", 10],
        chain("skirt.tail", "X", 8, 3, 1.0), chain("scarf.L", "X", 10, 5, 0.9), chain("scarf.R", "X", 10, 5, 0.9),
        ["rot", "sleeve.L", "Y", -20], ["rot", "sleeve.R", "Y", 20], ["rot", "bun", "X", 8], ["rot", "bow", "X", 14],
        ["props", {"expr_frown": 0.8}]]
J[5] = [["base", "rest"], ["move", "cog", [0, 0, -0.08]], ["scale", "cog", [0.99, 0.99, 1.02]],
        ["rot", "spine", "X", 6], ["rot", "head", "X", -6],
        ["feet", "L", [0.19, -0.04, 0], 8, 0, 0], ["feet", "R", [-0.19, 0.04, 0], -8, 0, 0],
        ["knee", "L", [0.15, -1, 0]], ["knee", "R", [-0.15, -1, 0]],
        ["rot", "upper_arm.R", "Y", 12], ["rot", "upper_arm.L", "Y", -12], ["sword", 10, 24],
        ["scarf_hang", 1.0, 0.0, 0.12], chain("skirt.tail", "X", -6, 3, 1.0),
        ["rot", "sleeve.L", "X", 8], ["rot", "sleeve.R", "X", 8], ["rot", "bun", "X", -4], ["rot", "bow", "X", -8],
        ["props", {"expr_smile": 0.4}]]
JN = ["crouch (squash)", "rise (stretch)", "apex (hang)", "fall (cloth lifts)", "land (squash)", "recover (overshoot)"]
for f in range(6):
    save(f"jump_f{f}", J[f], {"anim": "jump", "frame": f, "ms": JUMP_MS[f], "beat": JN[f],
                              "engine_z_px": [0, 10, 16, 8, 0, 0][f]}, dirs=("E", "SE"))
for tag, f in (("crouch", 0), ("apex", 2), ("land", 4)):
    save(f"jump_E_{tag}", J[f], {"anim": "jump", "frame": f, "beat": JN[f], "test_set": True}, dirs=("E",))

# ------------------------------------------------------------------ DASH (4 f)
D = {}
D[0] = [["base", "rest"], ["move", "cog", [0, 0.06, -0.16]], ["scale", "cog", [1.04, 1.04, 0.93]],
        ["rot", "spine", "X", -6], ["rot", "head", "X", 4],
        ["feet", "L", [0.16, -0.22, 0], 6, 0, 0], ["feet", "R", [-0.16, 0.26, 0], -6, 20, 0],
        ["knee", "L", [0.2, -1, 0]], ["knee", "R", [-0.2, -1, 0]],
        ["rot", "upper_arm.L", "X", 25], ["rot", "upper_arm.L", "Y", -15], ["sword", 70, 14],
        ["rot", "upper_arm.R", "X", -20], ["rot", "forearm.R", "X", -40],
        ["scarf_hang", 0.0, 0.0, 0.05], ["props", {"expr_frown": 1}]]
D[1] = [["base", "rest"], ["move", "cog", [0, -0.12, -0.12]], ["scale", "cog", [0.96, 1.10, 0.97]],
        ["rot", "spine", "X", 30], ["rot", "chest", "X", 6], ["rot", "head", "X", -22],
        ["feet", "L", [0.15, -0.50, 0.10], 0, 0, 20], ["feet", "R", [-0.12, 0.52, 0.24], 0, 70, 0],
        ["knee", "L", [0.05, -1, 0.2]], ["knee", "R", [-0.05, -1, -0.3]],
        ["rot", "upper_arm.R", "X", 55], ["rot", "forearm.R", "X", -20],
        ["rot", "upper_arm.L", "X", 45], ["rot", "upper_arm.L", "Y", -20], ["sword", 86, 4],
        ["scarf_run", 0.25], ["rot", "skirt.B", "X", 18], chain("skirt.tail", "X", 26, 3, 1.1),
        ["rot", "sleeve.L", "X", 45], ["rot", "sleeve.R", "X", 45], ["rot", "bun", "X", -6], ["rot", "bow", "X", -14],
        ["props", {"expr_frown": 1}]]
D[2] = [op for op in D[1] if op[0] != "scarf_run"] + [["scarf_run", 0.5]]
D[3] = [["base", "rest"], ["move", "cog", [0, 0.08, -0.22]], ["scale", "cog", [1.05, 0.96, 0.92]],
        ["rot", "spine", "X", -14], ["rot", "head", "X", 6],
        ["feet", "L", [0.18, -0.44, 0], 10, 0, 20], ["feet", "R", [-0.16, 0.30, 0], -10, 0, 0],
        ["knee", "L", [0.2, -1, 0]], ["knee", "R", [-0.2, -1, 0]],
        ["rot", "upper_arm.R", "X", -45], ["rot", "upper_arm.R", "Y", 25],
        ["rot", "upper_arm.L", "X", 15], ["rot", "upper_arm.L", "Y", -30], ["sword", 50, 10],
        chain("scarf.L", "X", -22, 5, 1.05), chain("scarf.R", "X", -22, 5, 1.05),
        ["rot", "skirt.F", "X", -16], chain("skirt.tail", "X", -14, 3, 1.0),
        ["rot", "sleeve.L", "X", -30], ["rot", "sleeve.R", "X", -30], ["rot", "bun", "X", 8], ["rot", "bow", "X", 16],
        ["props", {"expr_frown": 0.7}]]
DN = ["wind-up (1 f)", "travel A: stretch + afterimages", "travel B: afterimages fade", "brake (squash, cloth overshoots forward)"]
for f in range(4):
    save(f"dash_f{f}", D[f], {"anim": "dash", "frame": f, "ms": [50, 60, 60, 80][f], "beat": DN[f]}, dirs=("SE", "E"))

# ------------------------------------------------------------------ HURT (3 f)
H = {}
H[0] = [["base", "rest"], ["move", "cog", [0, 0.08, -0.04]],
        ["rot", "spine", "X", -18], ["rot", "chest", "X", -6], ["rot", "head", "X", -20], ["rot", "head", "Z", 6],
        ["feet", "L", [0.16, -0.10, 0], 6, 0, 18], ["feet", "R", [-0.16, 0.14, 0], -6, 0, 0],
        ["rot", "upper_arm.R", "X", -30], ["rot", "upper_arm.R", "Y", 35],
        ["rot", "upper_arm.L", "Y", -35], ["sword", 0, -10],
        chain("scarf.L", "X", -18, 5, 1.0), chain("scarf.R", "X", -18, 5, 1.0), chain("skirt.tail", "X", -10, 3, 1.0),
        ["rot", "sleeve.L", "X", -20], ["rot", "sleeve.R", "X", -20], ["rot", "bun", "X", 8], ["rot", "bow", "X", 14],
        ["props", {"expr_hurt": 1}]]
H[1] = [["base", "rest"], ["move", "cog", [0, 0.12, -0.10]], ["scale", "cog", [1.03, 1.03, 0.95]],
        ["rot", "spine", "X", -12], ["rot", "head", "X", -10], ["rot", "head", "Z", 10],
        ["feet", "L", [0.17, -0.06, 0], 6, 0, 10], ["feet", "R", [-0.17, 0.16, 0], -6, 0, 0],
        ["rot", "upper_arm.R", "X", -10], ["rot", "upper_arm.R", "Y", 25],
        ["rot", "upper_arm.L", "Y", -25], ["sword", 10, 4],
        chain("scarf.L", "X", -26, 5, 1.0), chain("scarf.R", "X", -26, 5, 1.0), chain("skirt.tail", "X", -16, 3, 1.0),
        ["rot", "sleeve.L", "X", -28], ["rot", "sleeve.R", "X", -28], ["rot", "bun", "X", 12], ["rot", "bow", "X", 20],
        ["props", {"expr_hurt": 1}]]
H[2] = [["base", "rest"], ["move", "cog", [0, 0.06, -0.12]],
        ["rot", "spine", "X", 8], ["rot", "head", "X", 8],
        ["feet", "L", [0.18, -0.06, 0], 8, 0, 0], ["feet", "R", [-0.18, 0.12, 0], -8, 0, 0],
        ["knee", "L", [0.15, -1, 0]], ["knee", "R", [-0.15, -1, 0]],
        ["rot", "upper_arm.R", "X", -18], ["rot", "upper_arm.L", "Y", -10], ["sword", 20, 22],
        chain("scarf.L", "X", 8, 5, 1.0), chain("scarf.R", "X", 8, 5, 1.0), chain("skirt.tail", "X", 6, 3, 1.0),
        ["rot", "sleeve.L", "X", 10], ["rot", "sleeve.R", "X", 10], ["rot", "bun", "X", -4], ["rot", "bow", "X", -8],
        ["props", {"expr_hurt": 0.5, "expr_frown": 0.5}]]
HN = ["flash + snap back (white silhouette)", "recoil extreme (shake during hit-stop)", "recover (hunch, cloth swings back)"]
for f in range(3):
    save(f"hurt_f{f}", H[f], {"anim": "hurt", "frame": f, "ms": [60, 100, 120][f], "beat": HN[f]}, dirs=("SE",))

SEQ = {"idle": 6, "walk": 8, "run": 8, "jump": 6, "slash": 6, "overhead": 9, "dash": 4, "hurt": 3}
os.makedirs(os.path.join(OUT, "ta"), exist_ok=True)
for a, n in SEQ.items():
    json.dump({"name": a, "frames": [{"file": f"{a}_f{i}.json"} for i in range(n)],
               "timing_ms": "see hybrid/ANIM_DIRECTION.md section 1"},
              open(os.path.join(OUT, "ta", f"anim_{a}.json"), "w"), indent=1)
print(len(written), "poses ->", OUT)


# ------------------------------------------------------------------ smear tip-track samples
# In-betweens of the swing keys (never art, never frames): the blade direction is interpolated on
# the SWING path (azimuth for the flat slash, pitch for the overhead), not by a straight lerp, so
# the guide's tip track is the real arc.  -> hybrid/anim/poses/samples/, read by smear_spec.py.
SAMP = os.path.join(OUT, "samples")
os.makedirs(SAMP, exist_ok=True)


def lerp(a, b, t):
    if isinstance(a, (list, tuple)):
        return [lerp(x, y, t) for x, y in zip(a, b)]
    if isinstance(a, dict):
        return {k: lerp(a[k], b.get(k, a[k]), t) for k in a}
    if a is None or isinstance(a, str):
        return a
    return a + (b - a) * t


def az_el(d):
    x, y, z = d
    h = math.hypot(x, y)
    return math.degrees(math.atan2(y, x)), math.degrees(math.atan2(z, h))


def from_az_el(az, el):
    a, e = math.radians(az), math.radians(el)
    return [math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)]


def slash_sample(k0, k1, t):
    A, B = SLASH[k0], SLASH[k1]
    s = {k: lerp(A[k], B[k], t) for k in A if k not in ("hand", "expr")}
    s["expr"] = A["expr"]
    (ca, da, ea, oa), (cb, db, eb, ob) = A["hand"], B["hand"]
    aa, ela = az_el(da)
    ab, elb = az_el(db)
    while ab < aa:          # the cut runs her right -> front -> left: azimuth INCREASES
        ab += 360
    d = from_az_el(aa + (ab - aa) * t, ela + (elb - ela) * t)
    s["hand"] = (lerp(ca, cb, t), d, eb if t > 0.5 else ea, oa)
    for side in ("L", "R"):
        s[side] = tuple(lerp(list(A[side]), list(B[side]), t))
    return s


n = 0
for k0, k1, steps in ((1, 2, 5), (2, 3, 4)):
    for i in range(steps):
        t = i / steps
        SLASH.append(slash_sample(k0, k1, t))
        ops = slash_ops(len(SLASH) - 1)
        SLASH.pop()
        json.dump({"format": "dirpose/1", "name": f"slashS_{n:02d}", "dirs": [], "ops": ops,
                   "intent": {"sample": True, "between": [k0, k1], "t": t}}, open(os.path.join(SAMP, f"slashS_{n:02d}.json"), "w"))
        n += 1
json.dump({"format": "dirpose/1", "name": f"slashS_{n:02d}", "dirs": [], "ops": slash_ops(3), "intent": {"sample": True, "between": [3, 3], "t": 0}},
          open(os.path.join(SAMP, f"slashS_{n:02d}.json"), "w"))


def pitch(d):       # angle in her Y-Z plane, 0 = forward (-Y), 90 = up
    x, y, z = d
    return math.degrees(math.atan2(z, -y)), x / (math.hypot(x, y, z) or 1)


n = 0
for k0, k1, steps in ((2, 3, 5), (3, 4, 4)):
    for i in range(steps):
        t = i / steps
        A, B = OH[k0], OH[k1]
        pa, xa = pitch(A["hand"][1])
        pb, xb = pitch(B["hand"][1])
        p = math.radians(pa + (pb - pa) * t)
        x = xa + (xb - xa) * t
        r = math.sqrt(max(0.0, 1 - x * x))
        d = [x, -r * math.cos(p), r * math.sin(p)]
        s = {k: lerp(A[k], B[k], t) for k in A if k not in ("hand", "expr", "n")}
        c = lerp(A["hand"][0], B["hand"][0], t)
        ops = [["base", "rest"], ["move", "cog", s["cog"]], ["scale", "cog", s["sc"]],
               ["rot", "spine", "X", s["spineX"]], ["rot", "chest", "X", s["chestX"]], ["rot", "chest", "Z", -10],
               ["rot", "head", "X", s["headX"]], ["rot", "head", "Z", 8]]
        for side in ("L", "R"):
            xx, yy, yaw, heel = s[side]
            ops.append(["feet", side, [xx, yy, 0.0], yaw, heel, 0])
        ops += [["knee", "L", [0.3, -1, 0]], ["knee", "R", [-0.3, -1, 0]],
                ["two_hand", c, d, list(B["hand"][2] or A["hand"][2] or [0, 0, -1]), 0.6]]
        json.dump({"format": "dirpose/1", "name": f"ohS_{n:02d}", "dirs": [], "ops": ops,
                   "intent": {"sample": True, "between": [k0, k1], "t": t}}, open(os.path.join(SAMP, f"ohS_{n:02d}.json"), "w"))
        n += 1
print("smear samples ->", SAMP)
