# check.py STATE.json OUTDIR : final measurement of rig G (same loop as cal.py) for S, SE, E, NE, N (+ SE_true = SE without the calib leg cheat)
# -> OUTDIR/check_<V>.png (blockout | rig | overlay with section lines, 800 x ~330), OUTDIR/residuals.txt + residuals.json
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import cal
st = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
sj = os.path.join(out, "_spec.json"); json.dump(st["spec"], open(sj, "w"))
ab = st["pose"]["abd"]; pose = {"upper_arm.R": [0, -ab, 0], "upper_arm.L": [0, ab, 0]}
V = ["S", "SE", "E", "NE", "N"]
m = cal.run(sj, os.path.join(out, "_m"), V, pose, xenv=dict(st["env"], POSEV=json.dumps({"SE": {"cheat": -st["pose"]["cheat"]}})))
mt = cal.run(sj, os.path.join(out, "_t"), ["SE"], pose, xenv=dict(st["env"], POSEV="{}"))
m["SE_true"] = mt["SE"]; os.remove(sj)
for d in ("_m", "_t"):
    import shutil; shutil.rmtree(os.path.join(out, d), ignore_errors=True)
COL = {"H": (61, 50, 53), "F": (248, 218, 194), "e": (85, 128, 162), "N": (230, 190, 165), "D": (192, 59, 61), "O": (69, 56, 73), "A": (142, 34, 44), "h": (240, 200, 175),
       "L": (250, 225, 205), "T": (42, 34, 42), "W": (232, 96, 79), "B": (90, 70, 75), ".": (110, 110, 110)}
def panel(codes, k=4):
    a = np.array([[COL.get(c, (200, 0, 200)) for c in r] for r in codes], np.uint8); return Image.fromarray(a).resize((64 * k, 64 * k), Image.NEAREST)
rows_all, table = {}, []
font_h = 11
for v in V + ["SE_true"]:
    bv = "SE" if v == "SE_true" else v
    bl = [l.rstrip("\n") for l in open(cal.R + f"prop/blockout/{bv}.txt")][:64]; rg = m[v]["codes"]
    bm, bw = cal.blk(bv); mm, mw = m[v]["rows"], m[v]["widths"]
    res = cal.residuals({bv: {"rows": mm, "widths": mw}}, [bv])[bv]; rows_all[v] = {"rig_rows": mm, "rig_widths": mw, "blk_rows": bm, "blk_widths": bw, "res": res}
    k = 4; W = 64 * k; img = Image.new("RGB", (800, W + 74), (40, 40, 44)); dr = ImageDraw.Draw(img)
    x0s = [8, 8 + W + 8, 8 + 2 * (W + 8)]
    img.paste(panel(bl), (x0s[0], 30)); img.paste(panel(rg), (x0s[1], 30))
    ov = np.full((64, 64, 3), 110, np.uint8); b_ = np.array([[c != "." for c in r] for r in bl]); r_ = np.array([[c != "." for c in r] for r in rg])
    ov[b_] = (175, 175, 175); ov[r_ & ~b_] = (230, 80, 70); ov[b_ & ~r_] = (70, 140, 230); ov[b_ & r_] = (200, 200, 200)
    img.paste(Image.fromarray(ov).resize((W, W), Image.NEAREST), (x0s[2], 30))
    for name, y in bm.items():
        if y is None or name in ("crotch",): continue
        yy = 30 + y * k; dr.line([(x0s[2], yy), (x0s[2] + W - 1, yy)], fill=(80, 220, 120)); dr.text((x0s[2] + 2, yy - 10 if name != "crown" else yy), name, fill=(80, 220, 120))
    for name, y in mm.items():
        if y is None or name in ("crotch",) or name.startswith("_"): continue
        yy = 30 + y * k; dr.line([(x0s[2] + W - 28, yy), (x0s[2] + W - 1, yy)], fill=(255, 90, 80), width=2)
        dr.line([(x0s[1], yy), (x0s[1] + 10, yy)], fill=(255, 90, 80), width=2)
    for x0 in x0s[:2]:
        for name, y in bm.items():
            if y is not None and name not in ("crotch",): dr.line([(x0 + W - 10, 30 + y * k), (x0 + W - 1, 30 + y * k)], fill=(80, 220, 120))
    dr.text((x0s[0], 8), f"{v}: blockout {bv}", fill=(230, 230, 230)); dr.text((x0s[1], 8), "rig G (calib pose" + (", true SE camera" if v == "SE_true" else (", SE leg cheat -45" if v == "SE" else "")) + ")", fill=(230, 230, 230))
    dr.text((x0s[2], 8), "overlay: grey both, red rig only, blue blk only", fill=(230, 230, 230))
    bad = {kk: x for kk, x in res.items() if kk not in ("crown", "sole") and (x is None or abs(x) > 1)}
    txt = "rig - blockout (px): " + " ".join(f"{kk}{'' if x is None else format(float(x), '+.0f')}" for kk, x in res.items())
    dr.text((8, W + 36), txt[:150], fill=(230, 230, 230)); dr.text((8, W + 50), txt[150:300], fill=(230, 230, 230))
    dr.text((8, W + 62) if len(txt) <= 300 else (8, W + 62), ("FAIL >1px: " + ", ".join(bad)) if bad else "all sections within +-1 px", fill=(255, 120, 110) if bad else (120, 230, 140))
    img.save(os.path.join(out, f"check_{v}.png"))
    table.append((v, res, bad))
keys = []
for v, res, _ in table:
    for kk in res:
        if kk not in keys: keys.append(kk)
with open(os.path.join(out, "residuals.txt"), "w") as f:
    f.write("rig G - blockout (1x px, prop/tools/verify section method; rows absolute in the 64 cell, sole line 62; widths px). '!' = |r|>1, '-' = not checked in that view, '?' = not found\n")
    f.write("calib: pose {} + upper_arm abd %s, FIG_EXCL=bow,bun FIG_PX=%s (measured crown->sole 48 in SE), HIDE=bow,bun for the crown, HEADS_SE=1.0, SE calib pose legs cheat -%s (SE_true = no cheat)\n" % (ab, st["env"]["FIG_PX"], st["pose"]["cheat"]))
    f.write("%-8s" % "view" + "".join("%8s" % kk for kk in keys) + "  fails\n")
    for v, res, bad in table:
        f.write("%-8s" % v + "".join("%8s" % ("-" if kk not in res else ("?" if res[kk] is None else ("%+.0f" % float(res[kk])) + ("!" if kk in bad else ""))) for kk in keys) + "  %d\n" % len(bad))
json.dump(rows_all, open(os.path.join(out, "residuals.json"), "w"), indent=0, default=float)
print(open(os.path.join(out, "residuals.txt")).read())
