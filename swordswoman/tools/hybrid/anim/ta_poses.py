"""TA guide poses: the director's motion bible poses (tools/hybrid/anim/make_poses.py, read-only here)
re-executed into hybrid/guide/poses/src/, then PUSHED for energy and fixed for guide problems
(sword hidden, timid bounce), plus the smear-helper sweeps written into the TA anim JSONs.

  .venv/bin/python tools/hybrid/anim/ta_poses.py [--pass p2]
  Blender -b --factory-startup -P tools/hybrid/anim/pose_preview.py -- --poses hybrid/guide/poses/src --out hybrid/guide/poses/preview --no-render
  Blender -b --factory-startup -P tools/hybrid/anim/pose_preview.py -- --poses hybrid/guide/poses/src/samples --out hybrid/guide/poses/preview --no-render
  then tools/hybrid/render_guides.py --anim-json hybrid/guide/poses/src/ta/anim_<a>.json

The director's numbers are the baseline; every change is listed in PUSH_NOTES (returned to the
director so the bible can be updated if it is accepted).
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SRC = os.path.join(ROOT, "tools", "hybrid", "anim", "make_poses.py")
OUT = os.path.join(ROOT, "hybrid", "guide", "poses", "src")
os.makedirs(OUT, exist_ok=True)

code = open(SRC).read()
anchor = 'OUT = os.path.join(ROOT, "hybrid", "anim", "poses")'
assert anchor in code, "make_poses OUT line changed"
code = code.replace(anchor, f"OUT = {OUT!r}")
ns = {"__name__": "make_poses_ta", "__file__": SRC}
exec(compile(code, SRC, "exec"), ns)          # writes the director's poses (unchanged) into OUT

save, chain, r1 = ns["save"], ns["chain"], ns["r1"]
PUSH_NOTES = []
# round 1 = pass p1 (first push); round 2 = pass p2 (fixes from the p1 clay-GIF + Gemini Argon review,
# hybrid/guide/p1/argon_*.json)
ROUND = int(sys.argv[sys.argv.index("--round") + 1]) if "--round" in sys.argv else 2
SAMPLE_STEPS = 10 if ROUND >= 2 else 6

# ---------------------------------------------------------------- SLASH push
S = ns["SLASH"]
# f0 gather: sink earlier (anticipation starts in the legs)
S[0].update(cog=(-0.03, 0.05, -0.09), chestZ=-22)
# f1 COIL: deeper twist and crouch; blade raised BEHIND HER RIGHT SHOULDER and out to the side so it
# is not hidden by the head in S/SE/E (it was vertical in front of the face).
S[1].update(cog=(-0.06, 0.10, -0.21), hipsZ=-24, spineX=-4, chestZ=-44, headZ=30, headX=8,
            hand=((-0.46, 0.10, 1.26), (-0.62, 0.70, 0.30), None, 0.55),
            L=(0.36, -0.40, -25, 14, 0), R=(-0.34, 0.32, 38, 0, 0),
            scarfZ=18, sleeveZ=24, tailZ=18, bunZ=6)
# f2 SMEAR: lower, lunge further under way
S[2].update(cog=(0.01, -0.08, -0.17), L=(0.44, -0.50, -30, 0, 0), R=(-0.34, 0.36, 30, 20, 0),
            scarfZ=-20, sleeveZ=-32, tailZ=-16, bunZ=-6)
# f3 IMPACT: full lunge, wider, lower; blade fully out to her left
S[3].update(cog=(0.07, -0.16, -0.25), hipsZ=16, spineX=10, chestZ=28, headZ=-16,
            hand=((0.24, -0.62, 1.14), (0.90, -0.42, 0.02), (0.5, -1.0, 0.0), 0.55),
            L=(0.50, -0.54, -32, 0, 0), R=(-0.40, 0.42, 30, 28, 0),
            scarfZ=-14, sleeveZ=-24, tailZ=-18, bunZ=-8)
# f4 FOLLOW-THROUGH: blade carries well past to her left-BACK and drops; chest overshoots harder;
# the cloth whips past (overshoot)
S[4].update(cog=(0.06, -0.12, -0.18), hipsZ=20, chestZ=44, headZ=-22,
            hand=((0.38, -0.30, 1.00), (0.52, 0.66, -0.54), (0.0, 0.0, -1.0), 0.55),
            L=(0.48, -0.52, -30, 0, 0), R=(-0.40, 0.42, 30, 18, 0),
            scarfZ=18, sleeveZ=28, tailZ=16, bunZ=7)
# f5 SETTLE: 1 px overshoot down kept, lower arc
S[5].update(cog=(0.03, -0.05, -0.11))
if ROUND >= 2:
    # coil blade more LATERAL (her right) so it is not pointed at the camera in N / hidden in SW
    S[1].update(hand=((-0.48, 0.02, 1.28), (-0.90, -0.15, 0.40), None, 0.55))   # probe: >= 21 px on screen in all 8 dirs
    S[0].update(hand=((-0.30, -0.18, 1.30), (-0.75, -0.30, 0.59), None, 0.5))
    S[2].update(cog=(0.01, -0.09, -0.20))
    # follow-through blade kept higher (it read as a downward chop between the legs in SW)
    S[4].update(hand=((0.38, -0.30, 1.04), (0.62, 0.62, -0.30), (0.0, 0.0, -1.0), 0.55))
    PUSH_NOTES.append("p2 slash: coil blade lateral to her right, tip up 24 deg (-0.90,-0.15,0.40): measured >= 21 px screen length in all 8 dirs (was 2-12 px in SE); smear cog -4 px; "
                      "follow-through blade raised to waist height (0.62,0.62,-0.30); swing samples 6 -> 10 per segment (smooth arc)")
PUSH_NOTES.append("slash: coil cog -3.6 px (was -2.5), chest -44 (was -34), blade cocked back-RIGHT at shoulder height, tip slightly up, clear of the huge head in every view "
                  "(was vertical in front of the face); impact lunge wider (feet 0.90 apart, was 0.78), cog -4.2 px; "
                  "follow-through blade to her left-back and down, chest +44; ribbons/sleeves amplitudes +20-30 %")
SKIRT_SOFT = {2: 0.75, 3: 0.65, 4: 0.7 if ROUND < 2 else 0.5}          # lunge: skirt follows the thighs less (no flat 'disc')


def slash_ops(k):
    ops = ns["slash_ops"](k)
    if k in SKIRT_SOFT:
        ops.append(["props", {"skirt_follow": SKIRT_SOFT[k]}])
    return ops


for f in range(6):
    save(f"slash_f{f}", slash_ops(f), {"anim": "attack1/slash", "frame": f, "ms": ns["SLASH_MS"][f],
                                       "beat": ns["SLASH_BEAT"][f], "smear": f == 2, "hitstop": f == 3, "ta_push": True},
         dirs=("SE", "E", "NW"))
for k, f in enumerate([1, 2, 3, 4]):
    save(f"slash_SE_k{k}", slash_ops(f), {"anim": "slash", "frame": f, "beat": ns["SLASH_BEAT"][f], "test_set": True, "ta_push": True})

# swing-path samples (in-betweens on the azimuth arc; NEVER frames, only for the smear sweep)
SAMP = os.path.join(OUT, "samples")
os.makedirs(SAMP, exist_ok=True)
n = 0
for k0, k1, steps in ((1, 2, SAMPLE_STEPS), (2, 3, SAMPLE_STEPS)):
    for i in range(steps):
        t = i / steps
        S.append(ns["slash_sample"](k0, k1, t))
        ops = ns["slash_ops"](len(S) - 1)
        S.pop()
        json.dump({"format": "dirpose/1", "name": f"slashS_{n:02d}", "dirs": [], "ops": ops,
                   "intent": {"sample": True, "between": [k0, k1], "t": t}}, open(os.path.join(SAMP, f"slashS_{n:02d}.json"), "w"))
        n += 1
json.dump({"format": "dirpose/1", "name": f"slashS_{n:02d}", "dirs": [], "ops": ns["slash_ops"](3),
           "intent": {"sample": True, "between": [3, 3], "t": 0}}, open(os.path.join(SAMP, f"slashS_{n:02d}.json"), "w"))
# f3 -> f4 follow-through samples
for i in range(1, 5):
    t = i / 4
    S.append(ns["slash_sample"](3, 4, t))
    ops = ns["slash_ops"](len(S) - 1)
    S.pop()
    n += 1
    json.dump({"format": "dirpose/1", "name": f"slashS_{n:02d}", "dirs": [], "ops": ops,
               "intent": {"sample": True, "between": [3, 4], "t": t}}, open(os.path.join(SAMP, f"slashS_{n:02d}.json"), "w"))
N_SLASH_SAMPLES = n + 1          # round 1: 00..05 f1->f2, 06..11 f2->f3, 12 = f3, 13..16 f3->f4
IF3 = 2 * SAMPLE_STEPS             # index of the f3 (impact) sample

# ---------------------------------------------------------------- IDLE push (round 2: breath read at game scale)
if ROUND >= 2:
    I = ns["IDLE"]
    TAU = ns["TAU"]
    PXV = ns["PXV"]
    I["cog_z_px"][:] = [-3.0, -1.5, 0.0, 0.6, -1.0, -2.3]   # p2b: p2 first try (-1.8..0.4) measured only 1.2-2 px crown
    for k_, m in (("chest_x", 2.2), ("shoulder", 1.8), ("head_x", 1.4), ("bun_x", 1.8), ("skirt_tail_x", 1.8),
                  ("sleeve_x", 1.6), ("sword_z", 2.5), ("hips_y", 1.5)):
        I[k_][:] = [r1(v * m) for v in I[k_]]
    for f in range(6):
        ph = TAU * f / 6
        ops = [["base", "idle_{D}"],
               ["move", "cog", [0, 0, r1(I["cog_z_px"][f] * PXV)]],
               ["rot", "chest", "X", I["chest_x"][f]],
               ["rot", "shoulder.L", "Y", -I["shoulder"][f]], ["rot", "shoulder.R", "Y", I["shoulder"][f]],
               ["rot", "head", "X", I["head_x"][f]],
               ["rot", "hips", "Y", I["hips_y"][f]],
               ["rot", "bun", "X", I["bun_x"][f]],
               ["rot", "bow", "X", r1(I["bun_x"][(f - 1) % 6] * 1.5)],
               ["scarf_hang", r1(ph - 0.9), 0.0, 0.24],
               chain("skirt.tail", "X", I["skirt_tail_x"][f], 3, 1.1),
               ["rot", "sleeve.L", "X", I["sleeve_x"][f]], ["rot", "sleeve.R", "X", I["sleeve_x"][(f + 1) % 6]],
               ["rot", "sword", "Z", I["sword_z"][f]],
               ["rot", "sword", "X", r1(1.5 * I["sword_z"][(f + 1) % 6])]]      # tip: small lagging figure-8
        save(f"idle_f{f}", ops, {"anim": "idle", "frame": f, "ms": ns["IDLE_MS"][f], "ta_push": True,
                                 "beat": ["exhale settled (low hold)", "inhale rising", "inhale", "inhale top (hold)", "exhale", "exhale falling"][f]},
             dirs=("SE", "S", "NW"), no_dir_turn=True)
        if f == 1:
            save("turn", ops, {"anim": "idle", "frame": 1, "note": "STANDARD TEST SET turn_<DIR>.png: idle neutral key (TA p2 idle f1)"},
                 dirs=ns["ALL8"], no_dir_turn=True)
    PUSH_NOTES.append("p2 idle: cog -3.0..+0.6 px (3.6 px knee/hem travel); chest x2.2, shoulder x1.8, "
                      "head x1.4, bun/skirt tail x1.8, sleeves x1.6, sword tip x2.5 with a lagging figure-8; ribbon sway 0.16 -> 0.24; "
                      "turn = this idle f1")

# ---------------------------------------------------------------- WALK push (bounce 4 px -> 5 px, bigger arm swing)
ns["WALK_COG"][:] = [-0.06, -0.20, -0.06, 0.07] if ROUND < 2 else [-0.07, -0.25, -0.06, 0.10]
if ROUND >= 2:                                    # longer stride, higher foot lift (feet clear the hem)
    ns["WALK_L"][:] = [(round(y * 1.3, 3), round(z * 1.6, 3), h, t) for (y, z, h, t) in ns["WALK_L"]]
for f in range(8):
    ops = ns["walk_ops"](f)
    for o in ops:                                     # arm swing x1.35
        if o[0] == "rot" and o[1] in ("upper_arm.R",) and o[2] == "X":
            o[3] = r1(o[3] * 1.35)
        if o[0] == "rot" and o[1] == "upper_arm.L" and o[2] == "X" and ROUND >= 2:
            o[3] = r1(o[3] * 1.7)                   # sword arm counter-swing
        if o[0] == "sword":                   # low guard slightly FORWARD of the left hip (was hidden in E/W)
            o[1] = r1(o[1] - (27 if ROUND < 2 else 45))
            o[2] = 42 if ROUND < 2 else 34
    k = f % 4
    save(f"walk_f{f}", ops, {"anim": "walk", "frame": f, "ms": 100, "beat": ns["WALK_NAMES"][k], "ta_push": True})
    if f < 4:
        save(f"walk_SE_k{f}", ops, {"anim": "walk", "frame": f, "beat": ns["WALK_NAMES"][k], "test_set": True, "ta_push": True})
if ROUND >= 2:
    PUSH_NOTES.append("p2 walk: cog -1.2/-4.2/-1/+1.7 px (5.9 px range); stride x1.3, foot lift x1.6; sword-arm swing x1.7; "
                      "katana az -45 / de 34 (forward-out of the left hip, readable in E)")
PUSH_NOTES.append("walk: cog track -1/-3.4/-1/+1.2 px (5.6 px range, was 3.4); free-arm swing x1.35; katana az -27 / de 42 (forward of the left hip) so it is not hidden in E/W")

# ---------------------------------------------------------------- RUN push (6 px+ bounce, katana visible)
ns["RUN_COG"][:] = [-0.06, -0.26, -0.06, 0.13]
if ROUND >= 2:                                    # back heel kicks higher (clears the hem in N)
    ns["RUN_L"][:] = [(y, round(z * 1.35, 3), h, t) for (y, z, h, t) in ns["RUN_L"]]
ns["RUN_SCALE"][:] = [(1, 1, 1), (1.04, 1.04, 0.93), (1, 1, 1), (0.97, 0.97, 1.06)]
for f in range(8):
    ops = ns["run_ops"](f)
    for o in ops:
        if o[0] == "sword":                   # trail back-LEFT and a bit lower: breaks the silhouette in SE too
            o[1] = r1(o[1] + (20 if ROUND < 2 else 8))
            o[2] = r1(o[2] + (2 if ROUND < 2 else 33))   # p2: back-left-DOWN ~45 deg: probe >= 12 px in S, 18 SE, 32 E
        if ROUND >= 2 and o[0] == "rot" and o[1] in ("hips", "chest") and o[2] == "Z":
            o[3] = r1(o[3] * 1.4)               # more shoulder / hip twist (N readability)
    k = f % 4
    save(f"run_f{f}", ops, {"anim": "run", "frame": f, "ms": 70, "beat": ns["RUN_NAMES"][k],
                            "smear": "swing-leg stretch smear + speed lines" if k == 3 else None, "ta_push": True}, dirs=("SE", "E"))
if ROUND >= 2:
    PUSH_NOTES.append("p2 run: katana az ~80 / de ~45 (trails back-left and DOWN: screen length >= 12 px in every dir, 18 SE, 32 E; "
                      "separate from the ribbons in E); hips/chest twist x1.4; heel kick x1.35; swing-foot smear sweeps from 2 frames back")
PUSH_NOTES.append("run: cog -1/-4.4/-1/+2.2 px (6.6 px range, was 5.4); squash/stretch 0.93/1.06 (was 0.95/1.04); "
                  "katana az +20 (pure back trail) so the blade breaks the silhouette behind her in SE/E (was hidden behind her)")

# ---------------------------------------------------------------- JUMP push
J = ns["J"]


def set_op(ops, key, new):
    for i, o in enumerate(ops):
        if o[:len(key)] == key:
            ops[i] = new
            return
    ops.append(new)


set_op(J[0], ["move", "cog"], ["move", "cog", [0, 0.03, -0.36]])
set_op(J[0], ["scale", "cog"], ["scale", "cog", [1.10, 1.10, 0.82]])
set_op(J[0], ["sword"], ["sword", 15, 34])            # blade back-low at her LEFT side (was hidden behind her in SE)
set_op(J[1], ["move", "cog"], ["move", "cog", [0, 0.0, 0.09]])
set_op(J[1], ["scale", "cog"], ["scale", "cog", [0.95, 0.95, 1.09]])
set_op(J[4], ["move", "cog"], ["move", "cog", [0, -0.02, -0.40]])
set_op(J[4], ["scale", "cog"], ["scale", "cog", [1.12, 1.12, 0.80]])
J[4].append(["props", {"skirt_follow": 0.7}])
for f in range(6):
    save(f"jump_f{f}", J[f], {"anim": "jump", "frame": f, "ms": ns["JUMP_MS"][f], "beat": ns["JN"][f],
                              "engine_z_px": [0, 10, 16, 8, 0, 0][f], "ta_push": True}, dirs=("E", "SE"))
for tag, f in (("crouch", 0), ("apex", 2), ("land", 4)):
    save(f"jump_E_{tag}", J[f], {"anim": "jump", "frame": f, "beat": ns["JN"][f], "test_set": True, "ta_push": True}, dirs=("E",))
PUSH_NOTES.append("jump: crouch cog -6.1 px / squash 0.82 (was -4.7 / 0.90), rise stretch 1.09, land -6.8 px / 0.80; "
                  "crouch katana to her left-low so it shows in SE")

# ---------------------------------------------------------------- TA anim JSONs with smear helpers
TA = os.path.join(OUT, "ta")
os.makedirs(TA, exist_ok=True)
SM = "../samples/ta/slashS_{:02d}.json"
blade = lambda idx, **kw: dict({"kind": "blade", "path": [SM.format(i) for i in idx], "inner": 0.4, "outer": 1.0, "taper": 0.85}, **kw)
SMEARS = {  # noqa
    # k1 SMEAR: the full motion coil -> just short of the impact (bible 4.1), blade drawn at f2
    ("slash", 2): [blade(range(0, IF3 - 2)), {"kind": "trail", "from": "prev", "bone": "hand.L", "t": 1.0, "radius": 0.05, "steps": 6}],
    # k2 IMPACT: thin sliver, last ~35 % of the arc
    ("slash", 3): [blade(range(IF3 - 6, IF3 + 1), inner=0.6, taper=0.9)],
    # k3 FOLLOW: wisp at the tail of the carry-through
    ("slash", 4): [blade(range(IF3, IF3 + 5), inner=0.88, taper=0.95)],
    # run flight frames: stretched swing-leg smear (feet: f3 L lead, f7 R lead)
    ("run", 3): [{"kind": "trail", "from": "prev" if ROUND < 2 else "hybrid/guide/poses/src/ta/run_f1.json", "bone": "foot.L", "t": 1.0, "radius": 0.10 if ROUND < 2 else 0.15, "steps": 8}],
    ("run", 7): [{"kind": "trail", "from": "prev" if ROUND < 2 else "hybrid/guide/poses/src/ta/run_f5.json", "bone": "foot.R", "t": 1.0, "radius": 0.10 if ROUND < 2 else 0.15, "steps": 8}],
}
SEQ = ns["SEQ"]
for a, n_ in SEQ.items():
    frames = []
    for i in range(n_):
        fr = {"file": f"{a}_f{i}.json"}
        if (a, i) in SMEARS:
            fr["smears"] = SMEARS[(a, i)]
        frames.append(fr)
    json.dump({"name": a, "frames": frames, "timing_ms": "see hybrid/ANIM_DIRECTION.md section 1"},
              open(os.path.join(TA, f"anim_{a}.json"), "w"), indent=1)
# STANDARD TEST SET keys with smears (slash_SE k1 = f2, k2 = f3, k3 = f4)
json.dump({"name": "slash_SE_keys", "frames": [{"file": "slash_SE_k0.json"},
                                                {"file": "slash_SE_k1.json", "smears": SMEARS[("slash", 2)]},
                                                {"file": "slash_SE_k2.json", "smears": SMEARS[("slash", 3)]},
                                                {"file": "slash_SE_k3.json", "smears": SMEARS[("slash", 4)]}]},
          open(os.path.join(TA, "anim_slash_SE_keys.json"), "w"), indent=1)
json.dump({"name": "walk_SE_keys", "frames": [{"file": f"walk_SE_k{i}.json"} for i in range(4)]},
          open(os.path.join(TA, "anim_walk_SE_keys.json"), "w"), indent=1)
json.dump({"name": "jump_E_keys", "frames": [{"file": f"jump_E_{t}.json"} for t in ("crouch", "apex", "land")]},
          open(os.path.join(TA, "anim_jump_E_keys.json"), "w"), indent=1)
json.dump({"notes": PUSH_NOTES, "slash_samples": N_SLASH_SAMPLES}, open(os.path.join(OUT, "PUSH_NOTES.json"), "w"), indent=1)
print("TA poses ->", OUT)
for s in PUSH_NOTES:
    print(" -", s)
