# uexport.py : ../work/act.json -> ../poses_unarmed.json (schema of v2/mocap/poses_mocap.json)
import json, os
U = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); V2 = os.path.dirname(U)
A = json.load(open(os.path.join(U, "work", "act.json"))); VIEWS = ["S", "SE", "E", "NE", "N"]
M = json.load(open(os.path.join(V2, "mocap", "poses_mocap.json")))
P = {k: M[k] for k in ("_doc", "rig", "camera", "views", "mirrors", "expressions", "licences")}
P["_doc"] = "UNARMED strand pose table (v2/unarmed): same schema as v2/mocap/poses_mocap.json (rig_lib.pose keys per bone, forearm.* elbows, off, absz/lift). idle/run/dash/jump/hurt re-picked or arm-layered for an unarmed girl (scripts/uactions.py); walk = mocap strand keys unchanged. katana key kept for schema compatibility (render with katana 0)."
P["rig"] = "v2/hy3d/rigs/G/parts posed by v2/throw/scripts/rig_lib.py (ELBOW=1, MOCAP=1); render v2/unarmed/scripts/frames_U.py"
P["unarmed_changed"] = ["idle", "run", "dash", "jump", "hurt"]
for act in ["idle", "walk", "run", "jump", "dash", "hurt"]:
    a = A[act]; P[act] = {"loop": a["loop"], "src": a["src"], "note": a.get("note", ""), "keys": {}}
    for f in a["frames"]:
        P[act]["keys"][f["name"]] = {"ms": f["ms"], "smear": f["smear"], "arc": f.get("arc", 1), "expression": f.get("expr", "neutral"), "src": f["src"], "t": f["t"], "views": {v: f[v] for v in VIEWS}}
json.dump(P, open(os.path.join(U, "poses_unarmed.json"), "w"), indent=1); print("poses_unarmed.json", [(k, len(P[k]["keys"])) for k in P if isinstance(P[k], dict) and "keys" in P[k]])
