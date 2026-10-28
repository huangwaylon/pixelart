# frames_G.py [ACT[,ACT]] [VIEW[,VIEW]] : render frame guides on rig G (one clip per Blender call via v2/throw/scripts/pt.py frames), skip clips done
# motion sources: v2/mocap/poses_mocap.json (idle walk run jump dash hurt) + v2/throw/poses_throw.json (throw); katana 0 everywhere (unarmed)
# out: v2/hy3d/frames_G/<act>_<dir>/s48/ (frames_mocap format) + post.py sil/preview/sheet; throw + throwpost.py ball block; GIFs v2/rigcal/gifs/
import sys, os, json, subprocess, time
R = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/"; PY = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python"
FR = R + "hy3d/frames_G/"; GIF = R + "rigcal/gifs/"; NOTES = R + "rigcal/NOTES.md"; WK = R + "rigcal/work/"
ST = json.load(open(R + "hy3d/rigs/G/calib_state.json"))
ACTS = ["idle", "walk", "run", "jump", "dash", "hurt", "throw"]; VIEWS = ["S", "SE", "E", "NE", "N"]
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
A = to_act(R + "mocap/poses_mocap.json", ACTS); A.update(to_act(R + "throw/poses_throw.json", ["throw"]))
aj = WK + "act_G.json"; json.dump(A, open(aj, "w"))
acts = sys.argv[1].split(",") if len(sys.argv) > 1 else ACTS; views = sys.argv[2].split(",") if len(sys.argv) > 2 else VIEWS
env = dict(os.environ, ACT_JSON=aj, PARTS=R + "hy3d/rigs/G/parts", FIG_EXCL="bow,bun", FIG_PX=ST["env"]["FIG_PX"], HEADS_SE="1.0", ELBOW="1")
env.pop("HIDE", None); env.pop("CHEAT", None)
os.makedirs(FR, exist_ok=True); os.makedirs(GIF, exist_ok=True)
for a in acts:
    for v in views:
        jid = f"{a}_{v}"; od = FR + jid + "/s48"
        if os.path.exists(od + "/frames.json") and os.path.exists(od + "/preview.gif") and (a != "throw" or "ball" in json.load(open(od + "/frames.json"))):
            print("skip", jid); continue
        t0 = time.time()
        r = subprocess.run([PY, "-I", R + "throw/scripts/pt.py", "frames", a, v, FR, GIF], cwd=R + "throw", env=env, capture_output=True, text=True)
        if r.returncode or not os.path.exists(od + "/frames.json"): print("FAIL", jid, r.stdout[-600:], r.stderr[-600:]); sys.exit(1)
        subprocess.run([PY, "-I", R + "hy3d/scripts/post.py", FR, jid], capture_output=True, text=True)
        fj = json.load(open(od + "/frames.json"))
        fj["rig"] = "v2/hy3d/rigs/G/parts (PROPORTIONS_G.json, RIG-CAL) posed by v2/throw/scripts/rig_lib.py (ELBOW=1, MOCAP=1); poses " + ("v2/throw/poses_throw.json" if a == "throw" else "v2/mocap/poses_mocap.json") + ", katana 0 (unarmed)"
        fj["fit"] = f"render_jobs FIG_EXCL=bow,bun FIG_PX={ST['env']['FIG_PX']}: measured (prop/tools/verify method) hair crown -> sole = 48 px in SE rest; HEADS_SE=1.0; CHEAT=0 (true SE/NE camera)"
        json.dump(fj, open(od + "/frames.json", "w"), indent=1)
        if a == "throw":
            e2 = dict(os.environ, FR_ROOT=FR, GIF_OUT=GIF)
            t = subprocess.run([PY, "-I", R + "throw/scripts/throwpost.py", v], cwd=R + "throw", env=e2, capture_output=True, text=True)
            if t.returncode: print("throwpost FAIL", jid, t.stderr[-600:]); sys.exit(1)
        msg = f"- frames {jid}: {len(fj['frames'])} frames ({time.time() - t0:.0f}s)"
        open(NOTES, "a").write(msg + "\n"); print(msg, flush=True)
