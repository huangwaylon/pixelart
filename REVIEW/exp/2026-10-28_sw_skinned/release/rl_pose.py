# rl_pose.py (I, round 5 gates) -- measured posture per frame, in the character's own sagittal plane (world, yaw 0: front +Y, up +Z).
#   <blender> -b rig/rig.blend -P release/rl_pose.py -- out.json motion1.json [motion2.json ...]
# Poses are applied exactly as R's render/render_motion.py apply() does (root.loc absolute world, pose rotation_quaternion, loc, scale).
# Per frame:  torso_pitch = angle of pelvis.head -> neck.head from vertical, + = FORWARD (toward her front);
#             head_pitch  = angle of the head bone axis (head -> tail) from vertical in the sagittal plane, + = chin DOWN / forward tip,
#                           - = chin up / tipped back (rest head bone is vertical);
#             neck_pitch  = neck bone axis vs vertical (+ forward);
#             head_fwd_mm = (head centre - neck base) . front, mm (+ = skull ahead of the neck base).
import bpy, sys, json, math
from mathutils import Vector, Quaternion
argv = sys.argv[sys.argv.index("--") + 1:]
OUT, MOTS = argv[0], argv[1:]
ao = bpy.data.objects["rig"]; pbs = ao.pose.bones
ao.rotation_mode = "XYZ"; ao.rotation_euler = (0, 0, 0)
for p in pbs: p.rotation_mode = "QUATERNION"
REST = {p.name: ao.data.bones[p.name].matrix_local.copy() for p in pbs}


def apply(fr):
    for p in pbs: p.rotation_quaternion = (1, 0, 0, 0); p.location = (0, 0, 0); p.scale = (1, 1, 1)
    loc = Vector(fr.get("root", {}).get("loc", [0, 0, 0]))
    R3 = REST["root"].to_3x3(); pbs["root"].location = R3.transposed() @ (loc - REST["root"].translation)
    for n, v in fr.get("bones", {}).items():
        if n not in pbs: continue
        if "rot" in v: pbs[n].rotation_quaternion = Quaternion(v["rot"])
        if "loc" in v and n != "root": pbs[n].location = Vector(v["loc"])
    for n, s in (fr.get("scale") or {}).items():
        if n in pbs: pbs[n].scale = Vector(s)
    bpy.context.view_layer.update()


W = lambda n, at: ao.matrix_world @ getattr(pbs[n], at)
F, U = Vector((0, 1, 0)), Vector((0, 0, 1))
sag = lambda v: math.degrees(math.atan2(v.dot(F), v.dot(U)))
res = {}
for mp in MOTS:
    M = json.load(open(mp)); rows = []
    for i, fr in enumerate(M["frames"]):
        apply(fr)
        pel, nk, hh, ht = W("pelvis", "head"), W("neck", "head"), W("head", "head"), W("head", "tail")
        rows.append({"i": i, "key": fr.get("key"), "torso_pitch": round(sag(nk - pel), 2), "neck_pitch": round(sag(hh - nk), 2),
                     "head_pitch": round(sag(ht - hh), 2), "head_fwd_mm": round(((hh + ht) / 2 - nk).dot(F) * 1000, 1)})
    res[mp] = rows
json.dump(res, open(OUT, "w"), indent=0)
print("POSE_DONE", len(res), flush=True)
