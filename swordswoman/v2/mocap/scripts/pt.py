# pt.py: POSE strand driver.  (.venv python)
#  pt.py render ACT[,ACT] VIEW[,VIEW] [OUT=out]      -> out/<act>_<view>/: frames (sequence w/ secondary), metrics.json, sheet.png, preview.gif, ones.png
#  pt.py sweep ACT FRAME VIEW VARS.json [TAG]          -> tmp/sweep/<tag>/: variants of one key, ranked strip (top3 strip too)
#  pt.py export                                         -> poses.json (action -> key -> view -> pose + ms)
import sys, os, json, subprocess, importlib, shutil
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import metrics as MX
PARTS = os.environ.get("PARTS", os.path.join(os.path.dirname(ROOT), "pose", "rig", "parts_E"))  # rig E = hy3d/rigs/E/parts (PROPORTIONS_E.json); placeholder = rig/parts_ph2
def src():
    import poses_src; importlib.reload(poses_src); return poses_src
def add(A, B):
    o = dict(A)
    for k, v in (B or {}).items():
        if k.startswith("+"):
            k = k[1:]; c = o.get(k, [0, 0, 0] if isinstance(v, list) else 0)
            o[k] = [c[i] + v[i] for i in range(len(v))] if isinstance(v, list) else c + v
        elif isinstance(v, dict) and isinstance(o.get(k), dict): o[k] = {**o[k], **v}
        else: o[k] = v
    return o
def resolve(S, act, i, view):
    fr = S.ACT[act]["frames"][i]
    p = add(add(dict(S.VIEW_DEFAULT.get(view, {})), S.ACT[act].get("base", {})), S.ACT[act].get(view, {}))
    p = add(p, fr.get("base", {}))
    for v in S.INHERIT.get(view, []) + [view]: p = add(p, fr.get(v, {}))
    xf = getattr(S, "VIEW_XFORM", {}).get(view)
    p = xf(p) if xf else p
    return add(p, fr.get(view + "_post", {}))
def run(jobs, out):
    os.makedirs(out, exist_ok=True); jp = os.path.join(out, "jobs.json"); json.dump({"jobs": jobs}, open(jp, "w"))
    r = subprocess.run([os.path.join(ROOT, "scripts", "rj.sh"), jp, out, PARTS], capture_output=True, text=True)
    if "ALLDONE" not in r.stdout: print(r.stdout[-800:], r.stderr[-800:]); raise SystemExit("render failed")
def game_gif(ds, ms, path, scale=6):  # deliverable: 1x matid through the game camera, 64 cell, NN x6 on #6e6e6e
    fr = []
    for d in ds:
        bg = np.array(MX.BG, np.uint8); mat = np.where(d.get("vis", d["alpha"])[..., None], d["matid"][..., :3], bg).astype(np.uint8)
        fr.append(Image.fromarray(mat).resize((64 * scale, 64 * scale), Image.NEAREST))
    fr[0].save(path, save_all=True, append_images=fr[1:], duration=ms, loop=0, disposal=1)
def onion(ds, names, path, scale=4):  # motion overlay for critics: each frame's 1x silhouette OUTLINE in its own colour on one 64 cell (shows bobs/arcs that a static sheet hides)
    cols = [(255, 80, 80), (255, 190, 60), (90, 220, 90), (60, 200, 255), (120, 120, 255), (230, 90, 230), (255, 255, 255), (40, 40, 40)]
    H, W = ds[0]["alpha"].shape; im = np.zeros((H, W, 3), np.uint8); im[:] = MX.BG
    for i, d in enumerate(ds):
        a = d["alpha"]; e = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1)); im[e] = cols[i % len(cols)]
    big = Image.fromarray(im).resize((W * scale, H * scale), Image.NEAREST); dr = ImageDraw.Draw(big)
    for i, n in enumerate(names): dr.text((4, 4 + 11 * i), f"{i} {n}", fill=cols[i % len(cols)])
    big.save(path)
def gif(ds, ms, path, scale=6):
    fr = []
    for d in ds:
        al = d["alpha"]; bg = np.array(MX.BG, np.uint8)
        mat = np.where(d.get("vis", al)[..., None], d["matid"][..., :3], bg).astype(np.uint8)
        sil = np.where(al[..., None], np.array([20, 20, 24], np.uint8), bg).astype(np.uint8)
        im = np.concatenate([mat, sil], 1)
        fr.append(Image.fromarray(im).resize((128 * scale, 64 * scale), Image.NEAREST))
    fr[0].save(path, save_all=True, append_images=fr[1:], duration=ms, loop=0, disposal=1)
def render(acts, views, outroot):
    S = src(); jobs = []
    for act in acts:
        A = S.ACT[act]
        for v in views:
            seq = [{"pose": resolve(S, act, i, v), "ms": f["ms"], "name": f["name"], "smear": f.get("smear", 0), "arc": f.get("arc", 1), "cw": f.get("cw_" + v, f.get("cw", True) != (v == "N")), "plane": f.get("plane_" + v, f.get("plane", "s")), "drag": f.get("drag", 0.0)} for i, f in enumerate(A["frames"])]
            jobs.append({"id": f"{act}_{v}", "view": v, "seq": seq, "loop": A.get("loop", False)})
    raw = os.path.join(outroot, "_raw"); run(jobs, raw)
    res = {}
    for j in jobs:
        jid = j["id"]; od = os.path.join(outroot, jid); os.makedirs(od, exist_ok=True)
        meta = json.load(open(os.path.join(raw, jid + ".json"))); ds, ms, rows, tiles = [], [], [], []; prev = None
        n = len(meta["frames"])
        for fr in meta["frames"]:
            stem = os.path.join(raw, f"{jid}_f{fr['i']:02d}")
            m, d = MX.metrics(stem, fr, prev); prev = d["alpha"]; ds.append(d); ms.append(fr["ms"])
            m.update({"name": fr["name"], "ms": fr["ms"], "air": fr["air"]}); rows.append(m)
            tiles.append(MX.tile(d, f"{fr['i']} {fr['name']} {fr['ms']}ms", f"neg{m['neg']} bl{m.get('blade_len','-')} ov{m['blade_over_body']} hid{m['blade_hidden']} gap{m['ground_gap']} {m['shape']}{m['tilt']:+.0f} d{m.get('delta','-')}"))
        if j["loop"]: rows[0]["delta"] = round(float((ds[0]["alpha"] ^ ds[-1]["alpha"]).sum() / max(1, (ds[0]["alpha"] | ds[-1]["alpha"]).sum())), 3)
        for fr in meta["frames"]: shutil.copy(os.path.join(raw, f"{jid}_f{fr['i']:02d}_matid.png"), os.path.join(od, f"f{fr['i']:02d}_matid4x.png"))
        json.dump({"frames": rows, "pts": [f["pts"] for f in meta["frames"]]}, open(os.path.join(od, "metrics.json"), "w"), indent=0)
        MX.strip(tiles, os.path.join(od, "sheet.png"), cols=4); MX.strip([MX.small(d, f"{i} {r['name']}") for i, (d, r) in enumerate(zip(ds, rows))], os.path.join(od, "small.png"), cols=8)
        MX.ones_row(ds, os.path.join(od, "ones.png")); MX.ones_row(ds, os.path.join(od, "ones4.png"), scale=4)
        gif(ds, ms, os.path.join(od, "preview.gif")); game_gif(ds, ms, os.path.join(od, "game.gif")); onion(ds, [r["name"] for r in rows], os.path.join(od, "onion.png"))
        MX.crit_strip(ds, [f"{r['name']} {r['ms']}ms" for r in rows], os.path.join(od, "crit.png"), f"{jid}  (top: 1x matid + 1x silhouette true size; then 3x matid, 3x silhouette)")
        res[jid] = rows
        print(jid, " | ".join(f"{r['name']}:n{r['neg']} b{r.get('blade_len',0):.0f} o{r['blade_over_body']} g{r['ground_gap']} {r['shape']}{r['tilt']:+.0f} d{r.get('delta',0)}" for r in rows))
    shutil.rmtree(raw)
    return res
def sweep(act, fi, view, varp, tag):
    S = src(); fi = int(fi) if fi.isdigit() else [f["name"] for f in S.ACT[act]["frames"]].index(fi)
    V = json.load(open(varp)) if varp.endswith(".json") else eval(open(varp).read())
    base = resolve(S, act, fi, view); want_air = S.ACT[act]["frames"][fi].get("air", False)
    jobs = [{"id": f"v{k:02d}", "view": view, "pose": add(base, v)} for k, v in enumerate(V)]
    out = os.path.join(ROOT, "tmp", "sweep", tag); shutil.rmtree(out, ignore_errors=True); run(jobs, out)
    sc = []
    for k, j in enumerate(jobs):
        fr = json.load(open(os.path.join(out, j["id"] + ".json")))["frames"][0]; m, d = MX.metrics(os.path.join(out, j["id"]), fr)
        s = MX.score(m, want_air); sc.append((s, k, m, d))
    sc.sort(key=lambda t: -t[0])
    tiles = [MX.tile(d, f"v{k:02d} score {s}", f"neg{m['neg']} bl{m.get('blade_len',0)} ov{m['blade_over_body']} hid{m['blade_hidden']} gap{m['ground_gap']} {m['shape']}{m['tilt']:+.0f}") for s, k, m, d in sc]
    MX.strip(tiles, os.path.join(out, "ranked.png"), cols=4); MX.strip([MX.small(d, f"v{k:02d} {s}") for s, k, m, d in sc], os.path.join(out, "small.png"), cols=5); MX.strip(tiles[:3], os.path.join(out, "top3.png"), cols=3)
    json.dump([{"k": k, "score": s, "m": m, "var": V[k]} for s, k, m, d in sc], open(os.path.join(out, "ranked.json"), "w"), indent=0)
    for s, k, m, d in sc: print(f"v{k:02d} {s:6.2f} neg{m['neg']} bl{m.get('blade_len',0)} ov{m['blade_over_body']} hid{m['blade_hidden']} gap{m['ground_gap']} {m['shape']}{m['tilt']:+.0f} w{m['w']}  {json.dumps(V[k])[:110]}")
def export():
    S = src(); P = {"_doc": S.DOC, "rig": "v2/hy3d/rigs/E/parts (copy: v2/pose/rig/parts_E), posed by v2/pose/scripts/rig_lib.py", "camera": "ortho, 30 deg elevation, 48 px figure, 64x64 cell", "views": S.VIEWS, "mirrors": {"W": "E", "SW": "SE", "NW": "NE"}, "expressions": "v2/face/expr_map.json names"}
    for act, A in S.ACT.items():
        P[act] = {"loop": A.get("loop", False), "keys": {}}
        for i, f in enumerate(A["frames"]):
            P[act]["keys"][f["name"]] = {"ms": f["ms"], "smear": f.get("smear", 0), "expression": S.EXPR.get(act, {}).get(f["name"], f.get("expr", "neutral")), "views": {v: resolve(S, act, i, v) for v in S.VIEWS}}
    json.dump(P, open(os.path.join(ROOT, "poses.json"), "w"), indent=1); print("poses.json", len(S.ACT), "actions")
AIRW = ("apex", "rise", "fall", "air", "launch", "hang")
def frames(act, v, froot, gifroot):  # FAN-OUT: per-frame guides for anim_cut/tools/ff_redraw.py (hy3d frames format, s48)
    S = src(); A = S.ACT[act]; jid = f"{act}_{v}"; od = os.path.join(froot, jid, "s48"); os.makedirs(od, exist_ok=True)
    seq = [{"pose": resolve(S, act, i, v), "ms": f["ms"], "name": f["name"], "smear": f.get("smear", 0), "arc": f.get("arc", 1), "cw": f.get("cw_" + v, f.get("cw", True) != (v == "N")), "plane": f.get("plane_" + v, f.get("plane", "s")), "drag": f.get("drag", 0.0)} for i, f in enumerate(A["frames"])]
    raw = os.path.join(od, "_raw"); os.environ["GUIDES"] = "1"; run([{"id": jid, "view": v, "seq": seq, "loop": A.get("loop", False)}], raw)
    meta = json.load(open(os.path.join(raw, jid + ".json"))); rows, names, ds, prev = [], [], [], None
    for fr in meta["frames"]:
        i = fr["i"]; stem = os.path.join(raw, f"{jid}_f{i:02d}")
        shutil.copy(stem + "_guide.png", os.path.join(od, f"f{i:02d}_matid.png")); shutil.copy(stem + "_shade.png", os.path.join(od, f"f{i:02d}_shade.png"))
        m, d = MX.metrics(stem, fr, prev); prev = d["alpha"]; ds.append(d)
        P = fr["pts"]; sm = bool(seq[i]["smear"] and seq[i]["arc"] and (A.get("loop", False) or i > 0))
        rows.append({"i": i, "name": fr["name"], "ms": fr["ms"], "air": fr["air"], "smear": sm, "katana": "blade_tip" in P, "pivot": list(meta["pivot_1x"]),
                     "head_centre": P["head"], "head_top": P["head_top"], "hip": P["hips"], "blade_pommel": P.get("blade_pommel"), "blade_tip": P.get("blade_tip"),
                     "expression": S.EXPR.get(act, {}).get(fr["name"], "neutral"), "pts": P})
        names.append(fr["name"] + ("_air" if fr["air"] and not any(a in fr["name"] for a in AIRW) else ""))
    ms = [r["ms"] for r in rows]
    json.dump({"action": act, "dir": v, "size": "s48", "fig_px": 48, "loop": A.get("loop", False), "cell_1x": meta["cell_1x"], "scale": 4, "pivot_1x": list(meta["pivot_1x"]),
               "px_per_unit_1x": round(meta["ppu"], 4), "elev_deg": 30, "rig": "v2/hy3d/rigs/E/parts posed by v2/mocap/scripts/rig_lib.py (ELBOW=1, MOCAP=1; pose table v2/mocap/poses_mocap.json, mocap-retargeted)",
               "ids": ["skin", "hair", "dress", "obi", "boots", "eyes", "bow", "sleeve", "blade", "hilt", "smear"],
               "note": "px coords are 1x cell pixels (x right, y down); renders are 4x (fNN_matid/shade.png); fNN_sil.png = 1-bit 1x silhouette at 4x. ff_redraw.py prep --gpivot 48 76 --gscale 4. In-game 64 cell = crop x16..80 y16..80 (pivot 32,60).",
               "frames": rows}, open(os.path.join(od, "frames.json"), "w"), indent=1)
    json.dump({"action": act, "dir": v, "keys": names, "ms": ms}, open(os.path.join(od, "keys.json"), "w"), indent=1)
    os.makedirs(gifroot, exist_ok=True); game_gif(ds, ms, os.path.join(gifroot, jid + ".gif"))
    shutil.rmtree(raw); print("frames", jid, len(rows))
if __name__ == "__main__":
    c = sys.argv[1]
    if c == "render": render(sys.argv[2].split(","), sys.argv[3].split(","), os.path.join(ROOT, sys.argv[4] if len(sys.argv) > 4 else "out"))
    elif c == "frames": frames(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif c == "sweep": sweep(*sys.argv[2:6], sys.argv[6] if len(sys.argv) > 6 else "s")
    elif c == "export": export()
