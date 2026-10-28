"""crop.py OUT ZOOM x0,y0,x1,y1 files... : zoomed crops side by side with a 1px grid every 8 cells"""
import sys
from PIL import Image, ImageDraw
out, z = sys.argv[1], int(sys.argv[2]); x0, y0, x1, y1 = map(int, sys.argv[3].split(",")); fs = sys.argv[4:]
w, h = (x1-x0)*z, (y1-y0)*z
sh = Image.new("RGB", (len(fs)*(w+6), h+14), (20, 20, 20)); d = ImageDraw.Draw(sh)
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGBA"); bg = Image.new("RGBA", im.size, (60, 56, 70, 255)); bg.alpha_composite(im)
    t = bg.crop((x0, y0, x1, y1)).resize((w, h), Image.NEAREST)
    dd = ImageDraw.Draw(t)
    for gx in range(0, x1-x0, 4): dd.line([(gx*z, 0), (gx*z, h)], fill=(90, 90, 90) if (x0+gx) % 8 else (140, 140, 60))
    for gy in range(0, y1-y0, 4): dd.line([(0, gy*z), (w, gy*z)], fill=(90, 90, 90) if (y0+gy) % 8 else (140, 140, 60))
    sh.paste(t, (i*(w+6), 14)); d.text((i*(w+6), 0), f.split("/")[-1] + f" ({x0},{y0})", fill=(220, 220, 220))
sh.save(out)
