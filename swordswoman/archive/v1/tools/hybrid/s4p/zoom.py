"""zoom.py IN.png OUT.png x0,y0,x1,y1 [z]  : zoomed crop with 1px grid + coordinate ticks every 4 px."""
import sys
from PIL import Image, ImageDraw
src, out, box = sys.argv[1], sys.argv[2], [int(v) for v in sys.argv[3].split(",")]
z = int(sys.argv[4]) if len(sys.argv) > 4 else 10
im = Image.open(src).convert("RGBA").crop(box)
w, h = im.size
bg = Image.new("RGBA", im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
M = 24
W = Image.new("RGB", (w * z + M, h * z + M), (30, 30, 36))
W.paste(bg.convert("RGB").resize((w * z, h * z), Image.NEAREST), (M, M))
d = ImageDraw.Draw(W)
for i in range(w + 1):
    x = M + i * z; c = (0, 0, 0) if (box[0] + i) % 4 else (255, 255, 0)
    d.line([(x, M), (x, M + h * z)], fill=c if (box[0]+i) % 4 == 0 else (90, 90, 90))
    if (box[0] + i) % 4 == 0 and i < w: d.text((x + 1, 2), str(box[0] + i), fill=(255, 255, 0))
for j in range(h + 1):
    y = M + j * z
    d.line([(M, y), (M + w * z, y)], fill=(255, 255, 0) if (box[1]+j) % 4 == 0 else (90, 90, 90))
    if (box[1] + j) % 4 == 0 and j < h: d.text((1, y + 1), str(box[1] + j), fill=(255, 255, 0))
W.save(out)
