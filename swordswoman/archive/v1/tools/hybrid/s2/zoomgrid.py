"""zoom with coordinate grid: zoomgrid.py in.png out.png x0,y0,x1,y1 [z]"""
import sys
from PIL import Image, ImageDraw
p, out = sys.argv[1], sys.argv[2]; x0, y0, x1, y1 = map(int, sys.argv[3].split(",")); z = int(sys.argv[4]) if len(sys.argv) > 4 else 10
im = Image.open(p).convert("RGBA").crop((x0, y0, x1, y1))
bg = Image.new("RGBA", im.size, (36, 32, 44, 255)); bg.alpha_composite(im)
c = bg.resize((im.width * z, im.height * z), Image.NEAREST).convert("RGB")
d = ImageDraw.Draw(c)
for x in range(x0, x1):
    col = (90, 90, 110) if x % 5 else (0, 200, 220)
    d.line([((x - x0) * z, 0), ((x - x0) * z, c.height)], fill=col if x % 5 == 0 else (52, 48, 62))
    if x % 5 == 0: d.text(((x - x0) * z + 1, 1), str(x), fill=(255, 255, 0))
for y in range(y0, y1):
    d.line([(0, (y - y0) * z), (c.width, (y - y0) * z)], fill=(0, 200, 220) if y % 5 == 0 else (52, 48, 62))
    if y % 5 == 0: d.text((1, (y - y0) * z + 1), str(y), fill=(255, 255, 0))
c.save(out)
