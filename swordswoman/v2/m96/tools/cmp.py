"""cmp.py X0 Y0 X1 Y1 OUT.png S REFHI STEM [STEM...]: ref_hi | stems crops (S x) in a row"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m96 as M, pzlib as Z
from PIL import Image
x0, y0, x1, y1 = map(int, sys.argv[1:5]); out = sys.argv[5]; s = int(sys.argv[6]); ims = []
r = Image.open(sys.argv[7]).convert('RGB'); h = (y1 - y0) * s; ims.append(r.resize((round(r.width * h / r.height), h)))
keys, rgb, _ = Z.load_pal(M.PAL)
for st in sys.argv[8:]:
    g, _ = Z.read(st); im = Z.render(g, keys, rgb).crop((x0, y0, x1, y1)); bg = Image.new('RGB', im.size, (200, 200, 200)); bg.paste(im, (0, 0), im)
    ims.append(bg.resize((im.width * s, im.height * s), Image.NEAREST))
W = sum(i.width + 6 for i in ims); S = Image.new('RGB', (W, h), 'white'); x = 0
for i in ims: S.paste(i, (x, 0)); x += i.width + 6
S.save(out); print(out, S.size)
