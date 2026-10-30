import sys, numpy as np, cv2
sys.path.insert(0, '..'); sys.path.insert(0, '.')
from build_gold import render, N
from PIL import Image
f, x0, y0, x1, y1, s = sys.argv[1], *map(int, sys.argv[2:7])
g = np.array([list(l.rstrip('\n')) for l in open(f) if l.strip('\n')])
a = render(g, 1, (110, 110, 110))[y0:y1, x0:x1]
im = Image.fromarray(a).resize(((x1 - x0) * s, (y1 - y0) * s), Image.NEAREST).convert('RGB')
from PIL import ImageDraw
d = ImageDraw.Draw(im)
for x in range(x0, x1):
    if x % 5 == 0: d.text(((x - x0) * s + 1, 0), str(x), fill=(255, 255, 0))
for y in range(y0, y1):
    if y % 5 == 0: d.text((0, (y - y0) * s + 1), str(y), fill=(0, 255, 255))
im.save(sys.argv[7])
