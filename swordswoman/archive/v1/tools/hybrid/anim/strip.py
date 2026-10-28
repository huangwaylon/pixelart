"""strip.py out.png label1=img,img,... label2=...  -> rows of cropped guide renders (256 px cells),
grey bg, baseline line at the pivot row.  Crop: x 16..240, y 24..232."""
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]
rows = [a.split("=", 1) for a in sys.argv[2:]]
X0, X1, Y0, Y1 = 16, 240, 24, 232
w, h = X1 - X0, Y1 - Y0
cols = max(len(r[1].split(",")) for r in rows)
S = Image.new("RGBA", (90 + cols * w, len(rows) * h), (92, 88, 100, 255))
d = ImageDraw.Draw(S)
for ri, (lab, imgs) in enumerate(rows):
    y = ri * h
    d.text((4, y + h // 2), lab, fill=(255, 255, 255, 255))
    for ci, p in enumerate(imgs.split(",")):
        im = Image.open(p).convert("RGBA").crop((X0, Y0, X1, Y1))
        x = 90 + ci * w
        by = y + 208 - Y0
        d.line([(x, by), (x + w - 1, by)], fill=(125, 120, 135, 255))
        d.line([(x, y), (x, y + h)], fill=(70, 66, 78, 255))
        S.alpha_composite(im, (x, y))
        d.text((x + 3, y + 2), p.split("/")[-1][:-4], fill=(230, 230, 230, 255))
S.save(out)
print(out, S.size)
