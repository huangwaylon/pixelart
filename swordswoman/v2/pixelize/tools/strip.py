"""strip.py out.png scale file1(.png) file2 ... : side-by-side NN-upscaled sprites (white bg)"""
import sys
from PIL import Image
out, s = sys.argv[1], int(sys.argv[2]); ims = [Image.open(p).convert('RGBA') for p in sys.argv[3:]]
bb = [i.getbbox() for i in ims]; y0 = min(b[1] for b in bb); y1 = max(b[3] for b in bb)
ims = [i.crop((b[0], y0, b[2], y1)) for i, b in zip(ims, bb)]
H = max(i.height for i in ims) * s; W = sum(i.width * s + 6 for i in ims)
c = Image.new('RGB', (W, H), 'white'); x = 0
for i in ims:
    j = i.resize((i.width * s, i.height * s), 0); c.paste(j, (x, H - j.height), j); x += j.width + 6
c.save(out)
