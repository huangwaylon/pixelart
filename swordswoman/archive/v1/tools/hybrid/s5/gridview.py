"""gridview.py OUT.png IMG.png x0,y0,x1,y1 [zoom]: zoomed crop with a 1px grid, labels every 5 px."""
import sys
from PIL import Image, ImageDraw
out, f, box = sys.argv[1], sys.argv[2], [int(v) for v in sys.argv[3].split(",")]
z = int(sys.argv[4]) if len(sys.argv) > 4 else 12
im = Image.open(f).convert("RGBA")
bg = Image.new("RGBA", im.size, (90, 140, 90, 255)); bg.alpha_composite(im)
x0, y0, x1, y1 = box; c = bg.crop((x0, y0, x1, y1)).resize(((x1-x0)*z, (y1-y0)*z), Image.NEAREST)
W, H = c.size; S = Image.new("RGB", (W+30, H+16), (20, 20, 20)); S.paste(c, (30, 16)); d = ImageDraw.Draw(S)
for i in range(x1-x0+1):
    d.line([(30+i*z, 16), (30+i*z, 16+H)], fill=(60, 60, 60) if (x0+i) % 5 else (200, 200, 0))
    if (x0+i) % 5 == 0: d.text((31+i*z, 2), str(x0+i), fill=(255, 255, 0))
for j in range(y1-y0+1):
    d.line([(30, 16+j*z), (30+W, 16+j*z)], fill=(60, 60, 60) if (y0+j) % 5 else (200, 200, 0))
    if (y0+j) % 5 == 0: d.text((2, 17+j*z), str(y0+j), fill=(255, 255, 0))
S.save(out)
