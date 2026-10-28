"""review grid: rows of sprites at zoom z on slate. grid.py out.png z crop(x0,y0,x1,y1) row1a,row1b,... row2a,... (rows separated as args)"""
import sys
from PIL import Image
out, z = sys.argv[1], int(sys.argv[2]); x0, y0, x1, y1 = map(int, sys.argv[3].split(","))
rows = [r.split(",") for r in sys.argv[4:]]
w, h = (x1 - x0) * z, (y1 - y0) * z
nc = max(len(r) for r in rows)
c = Image.new("RGB", (nc * w, len(rows) * h), (36, 32, 44))
for j, r in enumerate(rows):
    for i, f in enumerate(r):
        if not f: continue
        im = Image.open(f).convert("RGBA").crop((x0, y0, x1, y1)).resize((w, h), Image.NEAREST)
        c.paste(im, (i * w, j * h), im)
c.save(out)
