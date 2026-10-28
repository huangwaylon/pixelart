# cmp.py VIEW ACT[,ACT..] NEWROOT OUT.png [scale=2] : OLD (v2/pose/final_gifs) vs NEW (NEWROOT/<act>_<view>/game.gif) frame rows, NN scale of the 64 game cell
import sys, os
from PIL import Image, ImageDraw, ImageSequence
V, acts, newroot, outp = sys.argv[1], sys.argv[2].split(","), sys.argv[3], sys.argv[4]; S = int(sys.argv[5]) if len(sys.argv) > 5 else 2
OLD = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pose/final_gifs"
def frames(p):
    im = Image.open(p); out = []
    for f in ImageSequence.Iterator(im):
        ms = f.info.get("duration", 0); g = f.convert("RGB"); k = g.width // 64
        out.append((g.resize((64, 64), Image.NEAREST).resize((64 * S, 64 * S), Image.NEAREST), ms))
    return out
rows = []
for a in acts:
    for tag, p in ((() if os.environ.get("NEWONLY") else (("OLD", os.path.join(OLD, f"{a}_{V}.gif")),)) + (("NEW", os.path.join(newroot, f"{a}_{V}", "game.gif")),)):
        if os.path.exists(p): rows.append((f"{a} {tag}", frames(p)))
n = max(len(r[1]) for r in rows); cw = 64 * S; lw = 70
C = Image.new("RGB", (lw + n * (cw + 2), len(rows) * (cw + 14)), (60, 60, 60)); d = ImageDraw.Draw(C)
for i, (lab, fr) in enumerate(rows):
    y = i * (cw + 14); d.text((4, y + cw // 2), lab, fill=(255, 255, 0) if "NEW" in lab else (200, 200, 200))
    for j, (im, ms) in enumerate(fr):
        C.paste(im, (lw + j * (cw + 2), y + 12)); d.text((lw + j * (cw + 2) + 2, y), f"{j} {ms}ms", fill=(230, 230, 230))
C.save(outp); print(outp, C.size)
