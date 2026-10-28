# post.py FRAMES_ROOT [act_dir ...] : silhouettes + preview GIFs + sheets for anim_parts.py output
#  per <action>_<dir>: fNN_<size>_sil.png (1-bit, 1x alpha box>50% upscaled 4x nearest), frames.json gets sil_px_1x,
#  preview_<size>.gif (shade on mid-grey, real ms), sheet_<size>.png (rows: shade | matid | 1x px x4 | sil; frame name + ms on top),
#  onion_<size>.png (all frame silhouettes over each other, colour = time; shows arcs/bounce)
import sys, os, json, glob
import numpy as np
from PIL import Image, ImageDraw
root = sys.argv[1]; only = sys.argv[2:]
G = (128, 128, 128)
def ongrey(im):
    bg = Image.new("RGBA", im.size, G + (255,)); bg.alpha_composite(im.convert("RGBA")); return bg.convert("RGB")
for d in sorted(glob.glob(os.path.join(root, "*_*", "s*"))):
    if not os.path.isdir(d) or (only and os.path.basename(os.path.dirname(d)) not in only): continue
    mj = os.path.join(d, "frames.json")
    if not os.path.exists(mj): continue
    meta = json.load(open(mj)); C1 = meta["cell_1x"]; n = len(meta["frames"])
    for sz in [meta["size"]]:
        shades, rows = [], {"shade": [], "matid": [], "px": [], "sil": []}; sils = []
        for i, fr in enumerate(meta["frames"]):
            m = Image.open(os.path.join(d, f"f{i:02d}_matid.png")).convert("RGBA"); al = np.asarray(m)[..., 3]; k = al.shape[0] // C1
            s1 = al.reshape(C1, k, C1, k).mean((1, 3)) > 127; sils.append(s1)
            Image.fromarray((np.kron(s1, np.ones((k, k))) * 255).astype(np.uint8), "L").convert("1").save(os.path.join(d, f"f{i:02d}_sil.png"))
            fr["sil_px_1x"] = int(s1.sum())
            sp = os.path.join(d, f"f{i:02d}_shade.png")
            sh = Image.open(sp).convert("RGBA") if os.path.exists(sp) else m
            shades.append(ongrey(sh)); rows["shade"].append(ongrey(sh)); rows["matid"].append(ongrey(m))
            rows["px"].append(ongrey(m.resize((C1, C1), Image.BOX)).resize(m.size, Image.NEAREST))
            rows["sil"].append(Image.fromarray(np.where(np.kron(s1, np.ones((k, k)))[..., None] > 0, 30, 128).repeat(3, 2).astype(np.uint8)))
        W = shades[0].width
        shades[0].save(os.path.join(d, "preview.gif"), save_all=True, append_images=shades[1:], duration=[f["ms"] for f in meta["frames"]],
                       loop=0, disposal=1)
        S = 192; sheet = Image.new("RGB", (60 + S * n, S * 4 + 18), (40, 40, 40)); dr = ImageDraw.Draw(sheet)
        for i, fr in enumerate(meta["frames"]): dr.text((62 + i * S, 3), f"{i} {fr['name']} {fr['ms']}ms", fill="white")
        for r, key in enumerate(("shade", "matid", "px", "sil")):
            dr.text((3, 18 + r * S + S // 2), key, fill="white")
            for i, im in enumerate(rows[key]): sheet.paste(im.resize((S, S), Image.LANCZOS if key in ("shade",) else Image.NEAREST), (60 + i * S, 18 + r * S))
        sheet.save(os.path.join(d, "sheet.png"))
        on = np.full((C1, C1, 3), 128.0); cols = [np.array(c) for c in ((230, 60, 60), (240, 160, 40), (230, 230, 60), (80, 200, 90), (60, 170, 230), (110, 90, 230), (220, 80, 220), (250, 250, 250))]
        for i, s1 in enumerate(sils):
            c = cols[int(i * (len(cols) - 1) / max(1, n - 1))]; edge = s1 & ~(np.roll(s1, 1, 0) & np.roll(s1, -1, 0) & np.roll(s1, 1, 1) & np.roll(s1, -1, 1))
            on[s1] = on[s1] * 0.8 + c * 0.2; on[edge] = c
        Image.fromarray(on.astype(np.uint8)).resize((C1 * 4, C1 * 4), Image.NEAREST).save(os.path.join(d, "onion.png"))
    json.dump(meta, open(mj, "w"), indent=1)
    print("post", d)
