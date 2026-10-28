"""Round 8 (TA): mesh + pose hash of a character.blend, for the two-build determinism check.
Run: Blender -b <file.blend> --factory-startup -P model/blend_hash.py
Prints  [hash] mesh=<12 hex> actions=<12 hex> n_actions=<n>  (evaluated rest meshes, rounded to
1e-5, and every Action's F-curve keyframes rounded to 1e-5)."""
import bpy, hashlib

hm = hashlib.sha1()
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    if ob.type != "MESH":
        continue
    hm.update(ob.name.encode())
    for v in ob.data.vertices:
        hm.update(("%.5f,%.5f,%.5f;" % tuple(round(c, 5) + 0.0 for c in v.co)).encode())
    for vg in ob.vertex_groups:
        hm.update(vg.name.encode())
ha = hashlib.sha1()
n = 0
for act in sorted(bpy.data.actions, key=lambda a: a.name):
    n += 1
    ha.update(act.name.encode())
    fcs = []
    try:
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    fcs.extend(cb.fcurves)
    except AttributeError:
        fcs = list(act.fcurves)
    for fc in sorted(fcs, key=lambda f: (f.data_path, f.array_index)):
        ha.update(f"{fc.data_path}[{fc.array_index}]".encode())
        for kp in fc.keyframe_points:
            ha.update(("%.1f:%.5f;" % (kp.co[0], round(kp.co[1], 5) + 0.0)).encode())
print(f"[hash] mesh={hm.hexdigest()[:12]} actions={ha.hexdigest()[:12]} n_actions={n}")
