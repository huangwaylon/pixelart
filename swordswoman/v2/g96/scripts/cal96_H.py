# cal96.py STATE.json OUTDIR [VIEWS] [--keep] : rig H calibration loop at 96 px (G96 strand)
# STATE = {"spec": repro spec, "env": {"FIG_PX": "48"}, "pose": {"abd": deg, "cheat": deg (SE legs-to-camera calib cheat)}}
# spec -> repro_h.py (from hy3d/partsAB4f + hy3d/best/skel.txt, as rig G) -> rigcal/scripts/render_cal.py (4x of the 96 cell, bow+bun visible,
# FIG_EXCL=bow,bun sets the scale) -> meas96.rig (2x2 majority -> 128 cell, 96 px figure) -> meas96.measure -> residuals vs the 96 px masters.
import sys, os, json, subprocess, shutil
R = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/"; HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); import meas96 as M
PY = "/Users/waylonhuang/Documents/other/pixelart/.models/hy_omni/venv/bin/python"; BL = "/Applications/Blender.app/Contents/MacOS/Blender"
def run(st, out, views, keep=False, parts_only=False):
    os.makedirs(out, exist_ok=True); pd = os.path.join(out, "parts"); sj = os.path.join(out, "spec.json"); json.dump(st["spec"], open(sj, "w"))
    r = subprocess.run([PY, "-I", os.path.join(HERE, "repro_h.py"), sj, R + "hy3d/partsAB4f", R + "hy3d/best/skel.txt", pd], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-1500:]); raise SystemExit("repro failed")
    if parts_only: return None
    ab = st["pose"]["abd"]; pose = {"upper_arm.R": [0, -ab, 0], "upper_arm.L": [0, ab, 0], "katana": 0}
    PV = {"SE": {"cheat": -st["pose"].get("cheat", 0)}, "NE": {"cheat": -st["pose"].get("cheat_ne", 0)}}
    rd = os.path.join(out, "r"); os.makedirs(rd, exist_ok=True)
    json.dump({"jobs": [{"id": v, "view": v, "pose": {**pose, **PV.get(v, {})}} for v in views]}, open(os.path.join(rd, "jobs.json"), "w"))
    env = dict(os.environ, MOCAP="1", ELBOW="1", SOCKS="1", RIG_LIB_PATH=R + "throw/scripts/rig_lib.py", FIG_EXCL="bow,bun", HIDE="", HEADS_SE="1.0", FIG_PX=str(st["env"].get("FIG_PX", "48")))
    if st["env"].get("PPU"): env["PPU_FIX"] = str(st["env"]["PPU"])
    b = subprocess.run([BL, "-b", "--factory-startup", "-P", os.path.join(HERE, "render_cal96.py"), "--", pd, pd + "/skel.txt", rd + "/jobs.json", rd], capture_output=True, text=True, env=env)
    if "ALLDONE" not in b.stdout: print(b.stdout[-1500:], b.stderr[-800:]); raise SystemExit("render failed")
    meas = {"_calib": [l for l in b.stdout.splitlines() if l.startswith("calib")][:1]}
    for v in views:
        G = M.rig(os.path.join(rd, v + "_matid.png")); pts = json.load(open(os.path.join(rd, v + ".json")))["frames"][0]["pts"]
        kn = (pts["knee.R"][1] + pts["knee.L"][1]) / 2 * 2 - 32  # 1x 96-cell px -> 2x, minus the 64-cell crop (16 px at 1x)
        m, w = M.measure(G, v, knee_px=round(kn, 2), part=M.LAST_PART)
        meas[v] = {"rows": m, "widths": w, "res": M.residuals(m, w, v), "codes": ["".join(x) for x in G]}
    json.dump(meas, open(os.path.join(out, "meas.json"), "w"), default=float)
    if not keep: shutil.rmtree(rd)
    return meas
def score(meas, views):
    fails, exc, bad = 0, 0.0, []
    for v in views:
        mm, _ = M.master_meas(v)
        for k, x in meas[v]["res"].items():
            if x is None:
                if k in mm and mm.get(k) is None: continue
                fails += 1; exc += 3; bad.append(f"{v}.{k}?"); continue
            if abs(x) > 1: fails += 1; exc += abs(x) - 1; bad.append(f"{v}.{k}{x:+.0f}")
    return 10 * fails + exc, fails, bad
if __name__ == "__main__":
    st = json.load(open(sys.argv[1])); out = sys.argv[2]
    views = (sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("-") else "S,SE,E,NE,N").split(",")
    meas = run(st, out, views, "--keep" in sys.argv)
    for v in views: print(v, {k: (None if x is None else float(x)) for k, x in meas[v]["res"].items()})
    print("score", score(meas, views))
