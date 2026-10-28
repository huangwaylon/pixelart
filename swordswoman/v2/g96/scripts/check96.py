# check96.py MEAS.json OUTDIR [VIEWS] [LABEL]: check sheets (master classes | rig classes | overlay, 2x, 790 px wide) + residuals.txt/json
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import meas96 as M
COL = {"H": (61, 50, 53), "F": (248, 218, 194), "N": (225, 180, 160), "e": (85, 128, 162), "D": (192, 59, 61), "O": (150, 140, 170), "T": (110, 70, 40),
       "X": (30, 30, 60), "B": (255, 120, 100), "K": (15, 10, 10), ".": (120, 120, 120)}
def panel(G, k=2):
    a = np.array([[COL.get(c, (255, 0, 255)) for c in r] for r in G], np.uint8); return Image.fromarray(a).resize((128 * k, 128 * k), Image.NEAREST)
def main():
    meas = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    views = sys.argv[3].split(",") if len(sys.argv) > 3 else [v for v in ["S", "SE", "E", "NE", "N"] if v in meas]
    label = sys.argv[4] if len(sys.argv) > 4 else "rig H"
    table = []
    for v in views:
        Gm, _ = M.master(v); mm, mw = M.master_meas(v); G = np.array([list(r) for r in meas[v]["codes"]]); rm = meas[v]["rows"]
        sh = int(mm["sole"] - rm["sole"]); G = np.roll(G, sh, 0)  # soles on the master sole line
        res = meas[v]["res"]; k = 2; W = 256
        img = Image.new("RGB", (790, W + 60), (40, 40, 44)); dr = ImageDraw.Draw(img); xs = [6, 6 + W + 8, 6 + 2 * (W + 8)]
        img.paste(panel(Gm), (xs[0], 22)); img.paste(panel(G), (xs[1], 22))
        a = np.isin(Gm, list(M.SIL)); b = np.isin(G, list(M.SIL)); ov = np.full((128, 128, 3), 110, np.uint8)
        ov[a & b] = (200, 200, 200); ov[b & ~a] = (230, 80, 70); ov[a & ~b] = (70, 140, 230)
        img.paste(Image.fromarray(ov).resize((W, W), Image.NEAREST), (xs[2], 22))
        for name, y in mm.items():
            if y is None or name == "sole": continue
            yy = 22 + y * k; dr.line([(xs[2], yy), (xs[2] + W - 30, yy)], fill=(80, 220, 120)); dr.text((xs[2] + 2, yy - 10), name, fill=(80, 220, 120))
            dr.line([(xs[0] + W - 12, yy), (xs[0] + W - 1, yy)], fill=(80, 220, 120))
        for name, y in rm.items():
            if y is None or name == "sole" or name.startswith("_"): continue
            yy = 22 + (y + sh) * k; dr.line([(xs[2] + W - 28, yy), (xs[2] + W - 1, yy)], fill=(255, 90, 80), width=2); dr.line([(xs[1], yy), (xs[1] + 10, yy)], fill=(255, 90, 80), width=2)
        dr.text((xs[0], 6), f"{v}: master EC0_{v}_96 (classes)", fill=(230, 230, 230)); dr.text((xs[1], 6), f"{label} calib pose", fill=(230, 230, 230))
        dr.text((xs[2], 6), "grey both, red rig only, blue master only", fill=(230, 230, 230))
        bad = {kk: x for kk, x in res.items() if x is not None and abs(x) > 1}
        txt = " ".join(f"{kk}{'?' if x is None else format(float(x), '+.0f')}" for kk, x in res.items())
        dr.text((6, W + 26), txt[:140], fill=(230, 230, 230)); dr.text((6, W + 38), txt[140:280], fill=(230, 230, 230))
        dr.text((6, W + 48), ("FAIL >1px: " + ", ".join(bad)) if bad else "all sections within +-1 px", fill=(255, 120, 110) if bad else (120, 230, 140))
        img.save(os.path.join(out, f"check_{v}.png")); table.append((v, res, bad))
    keys = []
    for _, res, _ in table:
        for kk in res:
            if kk not in keys: keys.append(kk)
    with open(os.path.join(out, "residuals.txt"), "w") as f:
        f.write(f"{label} - master (96 px, 128 cell; rows with soles aligned; widths px; g96/scripts/meas96.py). '!' |r|>1, '-' not checked, '?' not found\n")
        f.write("%-5s" % "view" + "".join("%9s" % kk for kk in keys) + "  fails\n")
        for v, res, bad in table:
            f.write("%-5s" % v + "".join("%9s" % ("-" if kk not in res else ("?" if res[kk] is None else ("%+.0f" % float(res[kk])) + ("!" if kk in bad else ""))) for kk in keys) + "  %d\n" % len(bad))
    json.dump({v: {"res": res, "rig_rows": meas[v]["rows"], "rig_widths": meas[v]["widths"], "master": M.master_meas(v)} for v, res, _ in table}, open(os.path.join(out, "residuals.json"), "w"), indent=0, default=float)
    print(open(os.path.join(out, "residuals.txt")).read())
main()
