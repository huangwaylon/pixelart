"""Measure landmarks of a character blend (world units, rest/idle_S pose).  Usage:
Blender -b --factory-startup -P tools/hybrid/measure_rig.py -- [blend] [pose_action] [out.json]"""
import bpy, sys, json
from mathutils import Vector as V
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
blend = argv[0] if argv else ROOT + "/model/character.blend"
act = argv[1] if len(argv) > 1 else "pose_idle_S"
out = argv[2] if len(argv) > 2 else None
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene; rig = bpy.data.objects["rig"]
if act != "none" and act in bpy.data.actions:
    rig.animation_data.action = bpy.data.actions[act]
sc.frame_set(1); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def bb(names, mat=None):
    mn = V((1e9,) * 3); mx = V((-1e9,) * 3); n = 0
    for nm in names:
        o = bpy.data.objects.get(nm)
        if not o or o.type != "MESH": continue
        e = o.evaluated_get(dg); m = e.to_mesh()
        mi = None
        if mat:
            mi = {i for i, s in enumerate(e.material_slots) if s.material and mat in s.material.name.lower()}
            vs = {v for p in m.polygons if p.material_index in mi for v in p.vertices}
        else:
            vs = range(len(m.vertices))
        for i in vs:
            w = e.matrix_world @ m.vertices[i].co
            mn = V(map(min, mn, w)); mx = V(map(max, mx, w)); n += 1
        e.to_mesh_clear()
    return {"min": [round(c, 4) for c in mn], "max": [round(c, 4) for c in mx], "n": n}
R = {}
for k, names in {"hair": ["hair_cap", "bangs", "hair_strands"], "hair_bob": ["hair_bob"], "bangs": ["bangs"], "head": ["head"],
                 "bun": ["bun"], "bow": ["bow"], "collar": ["collar"], "corset": ["corset"],
                 "shorts": ["shorts"], "skirt_outer": ["skirt_outer"], "skirt_under": ["skirt_under"],
                 "legs": ["leg.L", "leg.R"], "shoes": ["shoe.L", "shoe.R"], "katana": ["katana"],
                 "sleeves": ["sleeve.L", "sleeve.R"], "arms": ["arm.L", "arm.R"], "hands": ["hand.L", "hand.R"],
                 "torso": ["body_torso"], "scarf": ["scarf.L", "scarf.R"]}.items():
    R[k] = bb(names)
fd = bpy.data.objects.get("face_decals")
if fd:
    R["face_decals_mats"] = sorted({s.material.name for s in fd.material_slots if s.material})
    for mname in R["face_decals_mats"]:
        R["fd_" + mname] = bb(["face_decals"], mname.lower())
R["iso_ortho"] = rig.get("iso_ortho")
R["bones"] = {b.name: [list(map(lambda c: round(c, 4), b.head)), list(map(lambda c: round(c, 4), b.tail))] for b in rig.data.bones}
for o in bpy.data.objects:
    if o.type == "MESH" and o.data.shape_keys:
        R.setdefault("shape_keys", {})[o.name] = [k.name for k in o.data.shape_keys.key_blocks]
R["drivers"] = [(o.name, d.data_path) for o in bpy.data.objects if o.animation_data for d in o.animation_data.drivers][:200]
R["constraints"] = {pb.name: [(c.type, c.name, getattr(c, "subtarget", "")) for c in pb.constraints] for pb in rig.pose.bones if pb.constraints}
R["obj_constraints"] = {o.name: [(c.type, c.name) for c in o.constraints] for o in bpy.data.objects if o.constraints}
R["parents"] = {o.name: [o.parent.name if o.parent else None, o.parent_type, o.parent_bone] for o in bpy.data.objects}
R["mods"] = {o.name: [(m.type, m.name) for m in o.modifiers] for o in bpy.data.objects if o.type == "MESH"}
s = json.dumps(R, indent=1)
if out: open(out, "w").write(s)
print("MEASURE_JSON_BEGIN"); print(s); print("MEASURE_JSON_END")
