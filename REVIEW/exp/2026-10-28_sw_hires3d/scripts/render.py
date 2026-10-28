# render.py [rest|walk|run|...] VIEW[,VIEW] : hi-res renders of rig H2 (+ motion-strand springs/tune) into big/<act>_<view>/
#   .venv python -I.  Jobs are built exactly like v2/motion/scripts/frames_M.py render() (same act_M.json keys + tune.json post layer);
#   rest = the G96 calibration pose (calib_state.json pose: abd/cheat/SE arm keys), 2 identical frames (springs settle at rest).
import sys, os, json, subprocess, time
EXP = "/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/"
R = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/"
import numpy, inspect, PIL.Image  # stdlib inspect first (motion/scripts/inspect.py shadows it)
sys.path.append(R + "motion/scripts")
import frames_M as FM  # read-only use: post(), ACT, CELL/PIV/PPU
BL = "/Applications/Blender.app/Contents/MacOS/Blender"
def rest_pose(v):
    st = json.load(open(R + "hy3d/rigs/H2/calib_state.json"))["pose"]; ab = st["abd"]
    p = {"upper_arm.R": [0, -ab, 0], "upper_arm.L": [0, ab, 0], "katana": 0}
    if v == "SE":
        p["cheat"] = -st.get("cheat", 0)
        p["upper_arm.R"] = [st.get("flex_se_r", 0), -(ab + st.get("abd_se_r", 0)), 0]; p["upper_arm.L"] = [st.get("flex_se", 0), ab + st.get("abd_se", 0), 0]
    return p
def jobs(act, v):
    if act == "rest":
        p = rest_pose(v); return {"id": f"rest_{v}", "view": v, "loop": False, "travel": 0.0,
                                  "seq": [{"pose": json.loads(json.dumps(p)), "ms": 200, "name": "rest"}, {"pose": json.loads(json.dumps(p)), "ms": 200, "name": "rest2"}]}
    A = json.load(open(FM.ACT))[act]
    seq = [dict({"pose": FM.post(act, f["name"], v, f[v], i == len(A["frames"]) - 1 and not A["loop"]), "ms": f["ms"], "name": f["name"], "smear": f.get("smear", 0), "arc": f.get("arc", 1)},
                **({"travel": f["travel"]} if "travel" in f else {})) for i, f in enumerate(A["frames"])]
    return {"id": f"{act}_{v}", "view": v, "loop": A["loop"], "travel": A.get("travel", 0.0), "seq": seq}
if __name__ == "__main__":
    act, views = sys.argv[1], sys.argv[2].split(",")
    for v in views:
        out = EXP + f"big/{act}_{v}"; os.makedirs(out, exist_ok=True); jp = out + "/jobs.json"
        json.dump({"jobs": [jobs(act, v)]}, open(jp, "w"))
        env = dict(os.environ, CELL1=str(FM.CELL), PIV1=f"{FM.PIV[0]},{FM.PIV[1]}", PPU_FIX=str(FM.PPU), HEADS_SE="1.0", SOCKS="1", ELBOW="1",
                   SCH=os.environ.get("SCH", "8"), KINDS=os.environ.get("KINDS", "guide,shade,lum,nrm,dep"))
        t0 = time.time()
        r = subprocess.run([BL, "-b", "--factory-startup", "-P", EXP + "scripts/hirender.py", "--", R + "hy3d/rigs/H2/parts", jp, out], capture_output=True, text=True, env=env)
        if "ALLDONE" not in r.stdout: print(r.stdout[-3000:], r.stderr[-1500:]); raise SystemExit("render failed")
        print("done", act, v, f"{time.time() - t0:.0f}s", flush=True)
