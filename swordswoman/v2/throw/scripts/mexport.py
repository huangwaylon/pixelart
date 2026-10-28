# mexport.py : work/act.json -> ../poses_mocap.json (schema of v2/pose/poses.json + src/t/note/arc)
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = json.load(open(os.path.join(ROOT, "work", "act.json"))); VIEWS = ["S", "SE", "E", "NE", "N"]
LIC = {"bandai1": "Bandai Namco Research Motion Dataset-1, CC BY-NC 4.0", "bandai2": "Bandai Namco Research Motion Dataset-2, CC BY-NC 4.0",
       "cmu": "CMU Graphics Lab Motion Capture Database (free for any use)", "lafan1": "Ubisoft LaFAN1, CC BY-NC-ND 4.0 (reference only)"}
P = {"_doc": "MOCAP strand pose table: action -> keys (in order) -> view -> pose. Poses are rig_lib.pose() keys (per-bone Euler deg in armature axes, Q = D_parent^-1 D_child; upper_arm Y pre-compensated for the +12 ABD), retargeted from real motion capture (v2/mocap/scripts/retarget.py + actions.py) with a light per-view camera layer, plus forearm.* (elbow; needs ELBOW=1 rig), off [x,y] root offset, absz/lift for air keys, katana 0 (unarmed THROW; extra cheats arm_yaw/leg_gain are baked into the rotations). Render: v2/throw/scripts/pt.py (MOCAP=1 ELBOW=1 via rj.sh). W/SW/NW = mirrored E/SE/NE.",
     "rig": "v2/hy3d/rigs/F/parts posed by v2/throw/scripts/rig_lib.py (arms split at the elbow, ELBOW=1 MOCAP=1); unarmed (katana 0)",
     "camera": "ortho, 30 deg elevation, 48 px figure, 64x64 cell", "views": VIEWS, "mirrors": {"W": "E", "SW": "SE", "NW": "NE"}, "expressions": "v2/face/expr_map.json names", "licences": LIC}
for act in ["throw"]:
    a = A[act]; P[act] = {"loop": a["loop"], "src": a["src"], "note": a.get("note", ""), "keys": {}}
    for f in a["frames"]:
        P[act]["keys"][f["name"]] = {"ms": f["ms"], "smear": f["smear"], "arc": f.get("arc", 1), "expression": f.get("expr", "neutral"), "src": f["src"], "t": f["t"], "views": {v: f[v] for v in VIEWS}}
json.dump(P, open(os.path.join(ROOT, "poses_throw.json"), "w"), indent=1); print("poses_throw.json", [(k, len(P[k]["keys"])) for k in P if isinstance(P[k], dict) and "keys" in P[k]])
