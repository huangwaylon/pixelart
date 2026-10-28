# frames_M.py (MOTION strand) .venv python -I
#   frames_M.py prev ACT[,ACT] VIEW[,VIEW] [TAG]  -> v2/motion/prev/<TAG>/<act>_<view>/ : game.gif (1x matid, 128 cell, x3), shade2x.gif (2x shaded),
#                                                    cmp.gif (old frames_H vs new, same clock), strip.png (1x + 2x frames), frames.json
#   frames_M.py final ACT[,ACT] VIEW[,VIEW]       -> v2/hy3d/frames_M/<act>_<dir>/s96/ (frames_H format + head_xf + secondary), g96-style gif in motion/gifs/
# env: PARTS (default rig H2 if READY in g96/NOTES.md else H), SECOND=0 (rigid A/B), SPRING / LAG json overrides (see mrender.py)
import sys, os, json, subprocess, time, math, shutil
import numpy as np
from PIL import Image, ImageDraw
R = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/"; PY = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python"; BL = "/Applications/Blender.app/Contents/MacOS/Blender"
CELL, PIV, SC, PPU = 192, (96, 152), 4, 52.608
ACT = R + "motion/work/act_M.json"; NOTES = R + "motion/NOTES.md"
def parts():
    if os.environ.get("PARTS"): return os.environ["PARTS"]
    h2 = R + "hy3d/rigs/H2/parts"
    return h2 if (os.path.isdir(h2) and "RIG H2 READY" in open(R + "g96/NOTES.md").read()) else R + "hy3d/rigs/H/parts"
TUNE = R + "motion/work/tune.json"
def post(act, name, v, p, last):
    """r2 post layer (tune.json <act>.post.{'*'|frame name|'name@VIEW'}): head_k scales head/neck rotation (less nod/drift),
    sq squash (+) / stretch (-) for weight, lift add, arm_in deg (arms closer to the body), rest_k blends the pose toward rest (settle),
    lean add (hips pitch fwd +), roll add (screen lean), off add [x, y]"""
    P = json.load(open(TUNE)).get(act, {}).get("post", {}) if os.path.exists(TUNE) else {}
    o = {}
    for k in ("*", name, f"{name}@{v}", f"*@{v}"): o.update(P.get(k, {}))
    if last and "rest_k" not in o and "last" in P: o.update(P["last"])
    if not o: return p
    p = json.loads(json.dumps(p)); hk = o.get("head_k", 1.0)
    hyz = o.get("hyz", 1.0)
    for b in ("head", "neck"):
        if b in p: p[b] = [p[b][0] * hk, p[b][1] * hk * hyz, p[b][2] * hk * hyz]
    if "hx_to" in o and "head" in p: p["head"][0] = o["hx_to"]
    if "hx" in o and "head" in p: p["head"][0] += o["hx"]
    if "kick" in o: p["_kick"] = o["kick"]  # [fwd, up] units/s impulse to the spring chains at this key (mrender)
    if "sq" in o: p["sq"] = p.get("sq", 0.0) + o["sq"]
    if "lift" in o: p["lift"] = p.get("lift", 0.0) + o["lift"]
    if "roll" in o: p["roll"] = p.get("roll", 0.0) + o["roll"]
    if "off" in o: q = p.get("off", [0, 0]); p["off"] = [q[0] + o["off"][0], q[1] + o["off"][1]]
    if "lean" in o: h = p.get("hips", [0, 0, 0]); p["hips"] = [h[0] + o["lean"], h[1], h[2]]
    a = o.get("arm_in", 0.0)
    if a:
        for s, sg in (("R", -1), ("L", float(os.environ.get("LSG", "1")))):
            k = "upper_arm." + s
            if k in p: p[k] = [p[k][0], p[k][1] + sg * a, p[k][2]]
    rk = o.get("rest_k", 0.0)
    if rk:
        for b, e in list(p.items()):
            if b.split(".")[0] in ("hips", "spine", "chest", "neck", "head", "upper_arm", "forearm", "hand", "thigh", "shin", "foot") and isinstance(e, list) and len(e) == 3:
                p[b] = [x * (1 - rk) for x in e]
    return p
def render(act, v, out):
    A = json.load(open(ACT))[act]; jid = f"{act}_{v}"
    seq = [dict({"pose": post(act, f["name"], v, f[v], i == len(A["frames"]) - 1 and not A["loop"]), "ms": f["ms"], "name": f["name"], "smear": f.get("smear", 0), "arc": f.get("arc", 1)}, **({"travel": f["travel"]} if "travel" in f else {})) for i, f in enumerate(A["frames"])]
    os.makedirs(out, exist_ok=True); jp = out + "/jobs.json"
    json.dump({"jobs": [{"id": jid, "view": v, "loop": A["loop"], "travel": A.get("travel", 0.0), "seq": seq}]}, open(jp, "w"))
    env = dict(os.environ, CELL1=str(CELL), PIV1=f"{PIV[0]},{PIV[1]}", PPU_FIX=str(PPU), HEADS_SE="1.0", SOCKS="1", ELBOW="1")
    r = subprocess.run([BL, "-b", "--factory-startup", "-P", R + "motion/scripts/mrender.py", "--", parts(), jp, out], capture_output=True, text=True, env=env)
    if "ALLDONE" not in r.stdout: print(r.stdout[-1500:], r.stderr[-800:]); raise SystemExit("render failed")
    return A, json.load(open(out + f"/{jid}.json"))
def down(p):  # 4x -> 1x majority colour (as g96 frames_H.down)
    a = np.asarray(Image.open(p).convert("RGBA")); k = a.shape[0] // CELL
    b = a.reshape(CELL, k, CELL, k, 4).transpose(0, 2, 1, 3, 4).reshape(CELL, CELL, k * k, 4); cov = (b[..., 3] > 127).mean(-1) > 0.5
    key = (b[..., 0].astype(np.int64) << 16) | (b[..., 1].astype(np.int64) << 8) | b[..., 2]; key = np.where(b[..., 3] > 127, key, -1)
    m = np.zeros((CELL, CELL, 4), np.uint8)
    for y, x in zip(*np.nonzero(cov)):
        u, c = np.unique(key[y, x][key[y, x] >= 0], return_counts=True); q = int(u[c.argmax()]); m[y, x] = (q >> 16, (q >> 8) & 255, q & 255, 255)
    return Image.fromarray(m)
BG = (0x6e, 0x6e, 0x6e, 255)
def g1(im):  # 1x 192 -> in-game 128 crop on grey
    C = Image.new("RGBA", (128, 128), BG); C.alpha_composite(im.crop((32, 32, 160, 160))); return C
def s2(p):  # 4x shade -> 2x crop of the 128 cell (256 px)
    a = Image.open(p).convert("RGBA"); a = a.crop((32 * 4, 32 * 4, 160 * 4, 160 * 4)).resize((256, 256), Image.LANCZOS)
    C = Image.new("RGBA", (256, 256), BG); C.alpha_composite(a); return C
def save_gif(ims, ms, path): ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=1)
def clock(ms_a, ms_b, loop, cycles=2):
    """merged timeline for side-by-side: list of (dur, ia, ib)"""
    Ta, Tb = sum(ms_a), sum(ms_b); tot = (max(Ta, Tb) * cycles) if loop else max(Ta, Tb) + 400
    def idx(ms, t, L):
        if loop: t = t % L
        acc = 0
        for i, m in enumerate(ms):
            acc += m
            if t < acc: return i
        return len(ms) - 1
    ev = sorted(set([0, tot] + [sum(ms_a[:i]) + k * Ta for k in range(cycles + 1) for i in range(len(ms_a))] + [sum(ms_b[:i]) + k * Tb for k in range(cycles + 1) for i in range(len(ms_b))]))
    ev = [e for e in ev if e <= tot]; out = []
    for t0, t1 in zip(ev[:-1], ev[1:]):
        if t1 - t0 >= 10: out.append((t1 - t0, idx(ms_a, t0, Ta), idx(ms_b, t0, Tb)))
    return out
def label(im, txt):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 7 * len(txt) + 4, 12], fill=(30, 30, 30, 255)); d.text((2, 0), txt, fill=(255, 255, 255, 255)); return im
def prev(act, v, tag):
    od = R + f"motion/prev/{tag}/{act}_{v}"; raw = od + "/_raw"; shutil.rmtree(od, ignore_errors=True)
    A, meta = render(act, v, raw); jid = f"{act}_{v}"; n = len(meta["frames"]); ms = [f["ms"] for f in meta["frames"]]
    G = [g1(down(raw + f"/{jid}_f{i:02d}_guide.png")) for i in range(n)]; S = [s2(raw + f"/{jid}_f{i:02d}_shade.png") for i in range(n)]
    save_gif([g.convert("RGB").resize((384, 384), Image.NEAREST) for g in G], ms, od + "/game.gif")
    save_gif([s.convert("RGB") for s in S], ms, od + "/shade2x.gif")
    # strip: per frame 1x (x2 nearest) over 2x shade
    st = Image.new("RGBA", (256 * n, 512), BG)
    for i in range(n):
        st.alpha_composite(G[i].resize((256, 256), Image.NEAREST), (256 * i, 0)); st.alpha_composite(S[i], (256 * i, 256)); label(st, "")
        ImageDraw.Draw(st).text((256 * i + 4, 2), f"{i} {meta['frames'][i]['name']} {ms[i]}", fill=(255, 255, 255, 255))
    st.convert("RGB").save(od + "/strip.png")
    # compare vs old frames_H (game 1x) on the same clock
    oj = R + f"hy3d/frames_H/{jid}/s96/frames.json"
    if os.path.exists(oj):
        O = json.load(open(oj)); oms = [f["ms"] for f in O["frames"]]; OG = [g1(down(R + f"hy3d/frames_H/{jid}/s96/f{f['i']:02d}_matid.png")) for f in O["frames"]]
        ims, durs = [], []
        for d, ia, ib in clock(oms, ms, A["loop"]):
            c = Image.new("RGBA", (256, 128), BG); c.alpha_composite(OG[ia], (0, 0)); c.alpha_composite(G[ib], (128, 0))
            c = c.convert("RGB").resize((768, 384), Image.NEAREST); label(c, f"OLD {O['frames'][ia]['name']}"); ImageDraw.Draw(c).text((390, 0), f"NEW {meta['frames'][ib]['name']}", fill=(255, 255, 255))
            ims.append(c); durs.append(d)
        save_gif(ims, durs, od + "/cmp.gif")
    # critic sheet: rows OLD 1x (x2), NEW 1x (x2), NEW 2x shaded; tiles = crop x24..104 y12..126 of the 128 cell
    def tile1(im): return im.crop((24, 12, 104, 126)).resize((160, 228), Image.NEAREST)
    def tile2(im): return im.crop((48, 24, 208, 252))
    rows = []
    if os.path.exists(oj): rows.append(("OLD (frames_H) 1x", [tile1(g) for g in OG], [f"{f['name']} {f['ms']}" for f in O["frames"]]))
    rows.append(("NEW 1x", [tile1(g) for g in G], [f"{f['name']} {f['ms']}" for f in meta["frames"]])); rows.append(("NEW 2x shaded", [tile2(s_) for s_ in S], [""] * n))
    Wd = 160 * max(len(r[1]) for r in rows); cs = Image.new("RGB", (Wd, 248 * len(rows)), (110, 110, 110))
    for ri, (lab, ts, nm) in enumerate(rows):
        dr = ImageDraw.Draw(cs)
        for i, t in enumerate(ts): cs.paste(t.convert("RGB"), (160 * i, 248 * ri + 18)); dr.text((160 * i + 3, 248 * ri + 4), nm[i], fill=(255, 255, 255))
        dr.text((Wd - 140, 248 * ri + 4), lab, fill=(255, 255, 0))
    cs.save(od + "/crit.png")
    json.dump(meta, open(od + "/frames.json", "w"), indent=0); shutil.rmtree(raw)
    return od
def vs(act, v, ta, tb):
    """prev/<tb>/<act>_<v>/vs_<ta>.gif: game 1x of round ta (left) vs tb (right), same clock"""
    from PIL import ImageSequence
    def fr(t):
        g = Image.open(R + f"motion/prev/{t}/{act}_{v}/game.gif"); return [f.convert("RGB").copy() for f in ImageSequence.Iterator(g)], [f.info.get("duration", 100) for f in ImageSequence.Iterator(Image.open(R + f"motion/prev/{t}/{act}_{v}/game.gif"))]
    (A_, ma), (B_, mb) = fr(ta), fr(tb); ims, durs = [], []
    for d, ia, ib in clock(ma, mb, json.load(open(ACT))[act]["loop"]):
        c = Image.new("RGB", (768, 384)); c.paste(A_[ia], (0, 0)); c.paste(B_[ib], (384, 0)); label(c, ta); ImageDraw.Draw(c).text((390, 0), tb, fill=(255, 255, 255))
        ims.append(c); durs.append(d)
    save_gif(ims, durs, R + f"motion/prev/{tb}/{act}_{v}/vs_{ta}.gif")
if __name__ == "__main__":
    mode, acts, views = sys.argv[1], sys.argv[2].split(","), sys.argv[3].split(",")
    if mode == "vs":
        for a in acts:
            for v in views: vs(a, v, sys.argv[4], sys.argv[5])
    if mode == "prev":
        tag = sys.argv[4] if len(sys.argv) > 4 else "p"
        for a in acts:
            for v in views: t0 = time.time(); od = prev(a, v, tag); print("prev", od, f"{time.time() - t0:.0f}s", flush=True)
