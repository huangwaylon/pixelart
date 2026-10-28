# Blender -b --factory-startup -P rest_dump.py -- PARTS OUT.json : dump rest armature (armature space) + mesh landmarks of the pose rig
import bpy, sys, os, json
a0 = sys.argv[sys.argv.index("--") + 1:]; pdir_, outp = a0[:2]
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rig_lib.py")
src = open(LIB).read(); src = src[:src.index('if os.environ.get("RIG_LIB") == "1"')]
sys.argv = [sys.argv[0], "--", pdir_, os.path.join(pdir_, "skel.txt"), os.path.join(os.path.dirname(LIB), "empty_keys.json"), "/tmp"]
exec(compile(src, "rig_lib.py", "exec"))
import numpy as np
B = {}
for b in arm.bones:
    B[b.name] = {"head": list(b.head_local), "tail": list(b.tail_local), "parent": b.parent.name if b.parent else None, "M": [list(r) for r in b.matrix_local.to_3x3()]}
L = {}
for o, bn in BIND.items():
    v = np.array([o.matrix_world @ x.co for x in o.data.vertices]); L[o.name] = {"bone": bn, "min": v.min(0).tolist(), "max": v.max(0).tolist()}
    if o.name.startswith("shin_"):
        L[o.name]["toe"] = v[v[:, 1].argmin()].tolist(); L[o.name]["heel"] = v[v[:, 1].argmax()].tolist(); L[o.name]["sole_z"] = float(v[:, 2].min())
for s in "RL":
    v = np.array([x.co[:] for x in parts["arm_" + s].data.vertices]); sh = np.array(arm.bones["upper_arm." + s].head_local); ax = np.array(arm.bones["hand." + s].head_local) - sh
    t = (v - sh) @ ax / (ax @ ax); L["arm_" + s]["t_range"] = [float(t.min()), float(t.max())]
    for q in (0.3, 0.5, 0.6):
        sel = np.abs(t - q) < 0.03; rr = np.linalg.norm((v[sel] - sh) - np.outer(t[sel], ax), axis=1); L["arm_" + s][f"radius_{q}"] = float(rr.max()) if sel.any() else None
json.dump({"bones": B, "parts": L}, open(outp, "w"), indent=1); print("REST OK")
