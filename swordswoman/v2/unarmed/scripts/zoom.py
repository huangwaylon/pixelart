# zoom.py ROOT VIEW OUT acts : rows of f*_shade.png cropped to the figure area (x 64..320, y 64..352) at 0.5 -> 128x144 cells
import sys, glob
from PIL import Image
root, view, out, acts = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(",")
rows = [sorted(glob.glob(f"{root}/{a}_{view}/s48/f*_shade.png")) for a in acts]
CW, CH = int(sys.argv[5]) if len(sys.argv) > 5 else 128, int(1.125 * (int(sys.argv[5]) if len(sys.argv) > 5 else 128)); W = CW * max(len(r) for r in rows); M = Image.new("RGB", (W, CH * len(rows)), (110, 110, 110))
for i, r in enumerate(rows):
    for j, p in enumerate(r):
        im = Image.open(p).convert("RGBA").crop((64, 64, 320, 352)).resize((CW, CH), Image.NEAREST); M.paste(im, (j * CW, i * CH), im)
M.save(out); print(out, M.size)
