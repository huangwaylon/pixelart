# frames_H2.py [ACT[,ACT]] [VIEW[,VIEW]] : s96 frame guides on rig H2 (G96 strand, recal to the polished masters v2/m96/masters). One clip per Blender call (pt.run -> rj.sh -> render_jobs.py), skips clips done.
# motion: v2/unarmed/poses_unarmed.json (idle run jump dash hurt) + v2/mocap/poses_mocap.json (walk) + v2/throw/poses_throw.json (throw); katana 0.
# camera: 192 cell at 1x (4x renders = 768 px), pivot (96,152), PPU_FIX = 2 x hy3d/rigs/H2/calib_state.json env.PPU (96-cell calibration PPU) -> 96 px figure;
# the in-game 128 cell = crop x32..160 y32..160 (pivot 64,120).  out: v2/hy3d/frames_H2/<act>_<dir>/s96/ (fNN_matid/shade/sil.png, frames.json, keys.json,
# preview.gif, sheet.png, onion.png via hy3d/scripts/post.py) ; game-res GIFs v2/g96/gifs/<act>_<dir>.gif (128 cell, 3x).
import sys, os, json, subprocess, time, math, shutil
import numpy as np
from PIL import Image, ImageDraw
R = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/"; PY = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python"
FR = R + "hy3d/frames_H2/"; GIF = R + "g96/gifs_H2/"; NOTES = R + "g96/NOTES.md"; WK = R + "g96/work/"
CELL, PIV, SC = 192, (96, 152), 4; PPU = round(2 * float(json.load(open(R + "hy3d/rigs/H2/calib_state.json"))["env"]["PPU"]), 4)  # H2: 2x the 96-cell calibration PPU
ACTS = ["idle", "walk", "run", "jump", "dash", "hurt", "throw"]; VIEWS = ["S", "SE", "E", "NE", "N"]
SRC = {"idle": "unarmed/poses_unarmed.json", "run": "unarmed/poses_unarmed.json", "jump": "unarmed/poses_unarmed.json", "dash": "unarmed/poses_unarmed.json",
       "hurt": "unarmed/poses_unarmed.json", "walk": "mocap/poses_mocap.json", "throw": "throw/poses_throw.json"}
def to_act():
    A = {}
    for a, f in SRC.items():
        P = json.load(open(R + f)); fr = []
        for name, k in P[a]["keys"].items():
            x = {"name": name, "ms": k["ms"], "smear": k["smear"], "arc": k.get("arc", 1), "expr": k.get("expression", "neutral"), "t": k.get("t"), "src": k.get("src")}
            for v in VIEWS: x[v] = dict(k["views"][v], katana=0)
            fr.append(x)
        A[a] = {"loop": P[a]["loop"], "frames": fr, "src": P[a].get("src"), "note": P[a].get("note", "")}
    return A
aj = WK + "act_H2.json"; json.dump(to_act(), open(aj, "w"))
os.environ.update(ACT_JSON=aj, PARTS=R + "hy3d/rigs/H2/parts", FIG_EXCL="bow,bun", HEADS_SE="1.0", ELBOW="1", SOCKS="1", CELL1=str(CELL), PIV1=f"{PIV[0]},{PIV[1]}", PPU_FIX=str(PPU), GUIDES="1")
os.environ.pop("HIDE", None); os.environ.pop("CHEAT", None)
sys.path.insert(0, R + "throw/scripts"); os.chdir(R + "throw"); import pt
LAND_U = 3.0; BCHEAT = {"S": 35, "N": 30, "NE": 0, "SE": 0, "E": 0}  # as throw/scripts/throwpost.py
def ball(J):  # throwpost.py ball block, in 192-cell 1x px (all px distances x2 vs s48)
    fr = J["frames"]; ri = [f["name"] for f in fr].index("release"); si = ri - 1; v = J["dir"]; ppu = J["px_per_unit_1x"]; up = 0.25 * ppu * math.cos(math.radians(30))
    P = [f["pts"] for f in fr]; rel = P[ri]["hand_tip.R"]; ah = np.subtract(P[ri]["throw_ahead"], P[ri]["throw_hips"])
    sg = 1 if rel[0] >= P[ri]["chest"][0] else -1; ca = math.radians(BCHEAT[v]) * sg
    if abs(ah[1]) > abs(ah[0]) and ca:
        c_ = [np.array([ah[0] * math.cos(a) - ah[1] * math.sin(a), ah[0] * math.sin(a) + ah[1] * math.cos(a)]) for a in (ca, -ca)]; ah = max(c_, key=lambda c: c[0] * sg)
    vel = ah / np.linalg.norm(ah); gdir = ah + np.array([0, up]); pv = np.array(J["pivot_1x"], float); land = pv + LAND_U * gdir
    dv = land - pv; n_ = np.linalg.norm(dv); land = pv + dv * max(1.0, 36.0 / max(n_, 1e-6))
    land[0] = min(max(land[0], 20), CELL - 20); land[1] = min(max(land[1], 32 + 16), 32 + 160 - 6)
    hv = np.subtract(rel, P[si]["hand_tip.R"]) / (fr[si]["ms"] / 1000.0); flip = rel[0] < P[si]["hand_tip.R"][0]
    for i, f in enumerate(fr):
        f["ball"] = {"state": "held" if i < ri else "release" if i == ri else "flying", "pos_px": [round(x, 2) for x in P[i]["hand_tip.R"]] if i <= ri else None}
    J["ball"] = {"release_frame": ri, "spawn_px": [round(x, 2) for x in rel], "vel_dir_px": [round(float(x), 3) for x in vel], "hand_vel_px_s": [round(float(x), 1) for x in hv],
                 "ground_dir_px_per_unit": [round(float(x), 2) for x in gdir], "preview_land_px": [round(float(x), 1) for x in land], "trail_flip_x": bool(flip), "orb_px": 14,
                 "flight_cheat_deg": BCHEAT[v] * sg,
                 "note": "1x 192-cell px (x right, y down; pivot 96,152; in-game 128 cell = crop x32..160 y32..160 -> subtract 32). Same rules as the s48 throw block (throwpost.py), px x2: orb sits in hand.R (pos_px = hand_tip.R) while held; spawned at spawn_px on the release key, flies along vel_dir_px; landing = game code (preview lands LAND_U=3 units ahead, >= 36 px from the feet)."}
def down(p):  # 4x -> 1x majority (as throwpost.down1x), returns RGBA 192x192
    a = np.asarray(Image.open(p).convert("RGBA")); k = a.shape[0] // CELL
    b = a.reshape(CELL, k, CELL, k, 4).transpose(0, 2, 1, 3, 4).reshape(CELL, CELL, k * k, 4); cov = (b[..., 3] > 127).mean(-1) > 0.5
    key = (b[..., 0].astype(np.int64) << 16) | (b[..., 1].astype(np.int64) << 8) | b[..., 2]; key = np.where(b[..., 3] > 127, key, -1)
    m = np.zeros((CELL, CELL, 4), np.uint8)
    for y, x in zip(*np.nonzero(cov)):
        u, c = np.unique(key[y, x][key[y, x] >= 0], return_counts=True); q = int(u[c.argmax()]); m[y, x] = (q >> 16, (q >> 8) & 255, q & 255, 255)
    return Image.fromarray(m)
def game_gif(od, J, path):
    ims = []
    for f in J["frames"]:
        C = Image.new("RGBA", (128, 128), (0x6e, 0x6e, 0x6e, 255)); C.alpha_composite(down(od + f"/f{f['i']:02d}_matid.png").crop((32, 32, 160, 160)))
        b = f.get("ball")
        if b and b.get("pos_px"):
            x, y = b["pos_px"][0] - 32, b["pos_px"][1] - 32; ImageDraw.Draw(C).ellipse([x - 4, y - 4, x + 4, y + 4], fill=(120, 200, 255, 255), outline=(20, 20, 40, 255))
        ims.append(C.convert("RGB").resize((384, 384), Image.NEAREST))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=[f["ms"] for f in J["frames"]], loop=0, disposal=1)
def clip(a, v):
    S = pt.src(); A = S.ACT[a]; jid = f"{a}_{v}"; od = FR + jid + "/s96"; os.makedirs(od, exist_ok=True)
    seq = [{"pose": pt.resolve(S, a, i, v), "ms": f["ms"], "name": f["name"], "smear": f.get("smear", 0), "arc": f.get("arc", 1), "cw": f.get("cw_" + v, f.get("cw", True) != (v == "N")),
            "plane": f.get("plane_" + v, f.get("plane", "s")), "drag": f.get("drag", 0.0)} for i, f in enumerate(A["frames"])]
    raw = od + "/_raw"; pt.run([{"id": jid, "view": v, "seq": seq, "loop": A.get("loop", False)}], raw)
    meta = json.load(open(os.path.join(raw, jid + ".json"))); rows, names = [], []
    assert meta["cell_1x"] == CELL and abs(meta["ppu"] - PPU) < 1e-3, (meta["cell_1x"], meta["ppu"])
    for fr in meta["frames"]:
        i = fr["i"]; stem = os.path.join(raw, f"{jid}_f{i:02d}")
        shutil.copy(stem + "_guide.png", od + f"/f{i:02d}_matid.png"); shutil.copy(stem + "_shade.png", od + f"/f{i:02d}_shade.png")
        P = fr["pts"]; sm = bool(seq[i]["smear"] and seq[i]["arc"] and (A.get("loop", False) or i > 0))
        rows.append({"i": i, "name": fr["name"], "ms": fr["ms"], "air": fr["air"], "smear": sm, "katana": False, "pivot": list(meta["pivot_1x"]),
                     "head_centre": P["head"], "head_top": P["head_top"], "hip": P["hips"], "blade_pommel": None, "blade_tip": None,
                     "expression": S.EXPR.get(a, {}).get(fr["name"], "neutral"), "pts": P})
        names.append(fr["name"] + ("_air" if fr["air"] and not any(w in fr["name"] for w in pt.AIRW) else ""))
    J = {"action": a, "dir": v, "size": "s96", "fig_px": 96, "loop": A.get("loop", False), "cell_1x": CELL, "scale": SC, "pivot_1x": list(meta["pivot_1x"]),
         "px_per_unit_1x": round(meta["ppu"], 4), "elev_deg": 30,
         "rig": "v2/hy3d/rigs/H2/parts (PROPORTIONS_H2.json, G96 calibration to the polished 96 px masters v2/m96/masters) posed by v2/throw/scripts/rig_lib.py (ELBOW=1, MOCAP=1, SOCKS=1); poses " + SRC[a] + ", katana 0 (unarmed)",
         "ids": ["skin", "hair", "dress", "obi", "boots", "eyes", "bow", "sleeve", "sock"],
         "fit": "render_jobs.py CELL1=192 PIV1=96,152 PPU_FIX=" + str(PPU) + " (rig H2 calibration PPU at the 96 cell x2): 96 px figure (hair crown -> sole ~93-95 px, as the masters); HEADS_SE=1.0; CHEAT=0 (true SE/NE camera)",
         "note": "px coords are 1x pixels of the 192 cell (x right, y down); renders are 4x (768 px fNN_matid/shade.png); fNN_sil.png = 1-bit 1x silhouette at 4x. ff_redraw.py prep --cell 128 128 --pivot <master feet x> 124 --gpivot 96 152 --gscale 4. In-game 128 cell = crop x32..160 y32..160 (pivot 64,120). Sock matid = sRGB ~(38,42,71).",
         "frames": rows}
    if a == "throw": ball(J)
    json.dump(J, open(od + "/frames.json", "w"), indent=1)
    json.dump({"action": a, "dir": v, "keys": names, "ms": [r["ms"] for r in rows]}, open(od + "/keys.json", "w"), indent=1)
    shutil.rmtree(raw)
    subprocess.run([PY, "-I", R + "hy3d/scripts/post.py", FR, jid], capture_output=True, text=True)
    J = json.load(open(od + "/frames.json")); game_gif(od, J, GIF + jid + ".gif")
    return len(rows)
if __name__ == "__main__":
    acts = sys.argv[1].split(",") if len(sys.argv) > 1 else ACTS; views = sys.argv[2].split(",") if len(sys.argv) > 2 else VIEWS
    os.makedirs(FR, exist_ok=True); os.makedirs(GIF, exist_ok=True)
    for a in acts:
        for v in views:
            jid = f"{a}_{v}"; od = FR + jid + "/s96"
            if os.path.exists(od + "/frames.json") and os.path.exists(GIF + jid + ".gif") and (a != "throw" or "ball" in json.load(open(od + "/frames.json"))):
                print("skip", jid); continue
            t0 = time.time(); n = clip(a, v); msg = f"- frames {jid}: {n} frames ({time.time() - t0:.0f}s)"
            open(NOTES, "a").write(msg + "\n"); print(msg, flush=True)
