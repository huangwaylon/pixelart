"""gv.py OUT.png sprite.png x0,y0,x1,y1 [z] : zoomed crop with 1px grid and coordinate labels every 4 px"""
import sys
from PIL import Image, ImageDraw
out, f, box = sys.argv[1], sys.argv[2], tuple(int(v) for v in sys.argv[3].split(','))
z = int(sys.argv[4]) if len(sys.argv) > 4 else 12
im = Image.open(f).convert('RGBA').crop(box)
bg = Image.new('RGBA', im.size, (84, 132, 66, 255)); bg.alpha_composite(im)
w, h = im.size; M = 22
W = Image.new('RGBA', (w * z + M, h * z + M), (30, 30, 36, 255)); W.paste(bg.resize((w * z, h * z), Image.NEAREST), (M, M))
d = ImageDraw.Draw(W)
for x in range(w + 1):
    d.line([(M + x * z, M), (M + x * z, M + h * z)], fill=(0, 0, 0, 255) if (box[0] + x) % 4 == 0 else (60, 60, 60, 255))
    if (box[0] + x) % 4 == 0 and x < w: d.text((M + x * z + 1, 4), str(box[0] + x), fill='yellow')
for y in range(h + 1):
    d.line([(M, M + y * z), (M + w * z, M + y * z)], fill=(0, 0, 0, 255) if (box[1] + y) % 4 == 0 else (60, 60, 60, 255))
    if (box[1] + y) % 4 == 0 and y < h: d.text((1, M + y * z + 1), str(box[1] + y), fill='yellow')
W.save(out)
