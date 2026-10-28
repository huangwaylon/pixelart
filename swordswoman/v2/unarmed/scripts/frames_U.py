# frames_U.py [ACT[,ACT]] [VIEW[,VIEW]] : UNARMED re-render on rig G (copy of v2/rigcal/scripts/frames_G.py; one clip per Blender call via v2/throw/scripts/pt.py frames)
# motion: v2/unarmed/poses_unarmed.json; katana 0. out: $FR_OUT (default v2/hy3d/frames_G/)<act>_<dir>/s48/ (old clip moved to v2/hy3d/frames_G_armed_backup/ first, once), GIFs $GIF_OUT_U (default v2/unarmed/gifs/)
import sys, os, json, subprocess, time, shutil
R = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/"; PY = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python"
FR = os.environ.get("FR_OUT", R + "hy3d/frames_G/"); GIF = os.environ.get("GIF_OUT_U", R + "unarmed/gifs/"); NOTES = R + "unarmed/NOTES.md"; WK = R + "unarmed/work/"; BK = R + "hy3d/frames_G_armed_backup/"
ST = json.load(open(R + "hy3d/rigs/G/calib_state.json"))
ACTS = ["idle", "run", "jump", "dash", "hurt"]; VIEWS = ["S", "SE", "E", "NE", "N"]
def to_act(pj, acts):
    P = json.load(open(pj)); A = {}
    for a in acts:
        if a not in P: continue
        fr = []
        for name, k in P[a]["keys"].items():
            f = {"name": name, "ms": k["ms"], "smear": k["smear"], "arc": k.get("arc", 1), "expr": k.get("expression", "neutral"), "t": k.get("t"), "src": k.get("src")}
            for v in VIEWS: f[v] = dict(k["views"][v], katana=0)
            fr.append(f)
        A[a] = {"loop": P[a]["loop"], "frames": fr, "src": P[a].get("src"), "note": P[a].get("note", "")}
    return A
A = to_act(R + "unarmed/poses_unarmed.json", ["idle", "walk", "run", "jump", "dash", "hurt"])
aj = WK + "act_G.json"; json.dump(A, open(aj, "w"))
acts = sys.argv[1].split(",") if len(sys.argv) > 1 else ACTS; views = sys.argv[2].split(",") if len(sys.argv) > 2 else VIEWS
env = dict(os.environ, ACT_JSON=aj, PARTS=R + "hy3d/rigs/G/parts", FIG_EXCL="bow,bun", FIG_PX=ST["env"]["FIG_PX"], HEADS_SE="1.0", ELBOW="1")
env.pop("HIDE", None); env.pop("CHEAT", None)
os.makedirs(FR, exist_ok=True); os.makedirs(GIF, exist_ok=True)
for a in acts:
    for v in views:
        jid = f"{a}_{v}"; od = FR + jid + "/s48"
        if os.path.exists(FR + jid):
            if FR == R + "hy3d/frames_G/" and not os.path.exists(BK + jid): os.makedirs(BK, exist_ok=True); shutil.move(FR + jid, BK + jid)
            else: shutil.rmtree(FR + jid)
        t0 = time.time()
        r = subprocess.run([PY, "-I", R + "throw/scripts/pt.py", "frames", a, v, FR, GIF], cwd=R + "throw", env=env, capture_output=True, text=True)
        if r.returncode or not os.path.exists(od + "/frames.json"): print("FAIL", jid, r.stdout[-600:], r.stderr[-600:]); sys.exit(1)
        subprocess.run([PY, "-I", R + "hy3d/scripts/post.py", FR, jid], capture_output=True, text=True)
        fj = json.load(open(od + "/frames.json"))
        fj["rig"] = "v2/hy3d/rigs/G/parts (PROPORTIONS_G.json, RIG-CAL) posed by v2/throw/scripts/rig_lib.py (ELBOW=1, MOCAP=1); poses " + "v2/unarmed/poses_unarmed.json" + ", katana 0 (unarmed)"
        fj["fit"] = f"render_jobs FIG_EXCL=bow,bun FIG_PX={ST['env']['FIG_PX']}: measured (prop/tools/verify method) hair crown -> sole = 48 px in SE rest; HEADS_SE=1.0; CHEAT=0 (true SE/NE camera)"
        json.dump(fj, open(od + "/frames.json", "w"), indent=1)
        if a == "throw":
            e2 = dict(os.environ, FR_ROOT=FR, GIF_OUT=GIF)
            t = subprocess.run([PY, "-I", R + "throw/scripts/throwpost.py", v], cwd=R + "throw", env=e2, capture_output=True, text=True)
            if t.returncode: print("throwpost FAIL", jid, t.stderr[-600:]); sys.exit(1)
        msg = f"- frames {jid}: {len(fj['frames'])} frames ({time.time() - t0:.0f}s)"
        print(msg, flush=True)
