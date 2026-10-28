# MOCAP strand pose table loader for pt.py (ACT built by actions.py -> ../work/act.json)
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ["S", "SE", "E", "NE", "N"]
DOC = "MOCAP strand pose table (v2/mocap): poses retargeted from real motion capture (scripts/actions.py, retarget.py) onto rig E with elbows (ELBOW=1) + light camera layer. Same keys as v2/pose/poses.json (per-bone Euler deg, rig_lib conventions) plus forearm.* (elbow), off [x,y] root offset, absz/lift for air frames. Render with v2/mocap/scripts (MOCAP=1 ELBOW=1)."
ACT = json.load(open(os.environ.get("ACT_JSON", os.path.join(ROOT, "work", "act.json"))))
VIEW_DEFAULT = {}; INHERIT = {}; VIEW_XFORM = {}
EXPR = {a: {f["name"]: f.get("expr", "neutral") for f in A["frames"]} for a, A in ACT.items()}
