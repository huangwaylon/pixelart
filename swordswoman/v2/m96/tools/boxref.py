"""boxref.py VIEW X0 Y0 X1 Y1 [SUB=1]: illustration box-averaged to sprite grid (SUB x finer), nearest palette char (no material constraint)"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m96 as M, pzlib as Z
from PIL import Image
v, x0, y0, x1, y1 = sys.argv[1], *map(int, sys.argv[2:6]); sub = int(sys.argv[6]) if len(sys.argv) > 6 else 1
g, meta = Z.read(M.ROOT + f'v2/m96/master0/EC0_{v}_96'); keys, rgb, _ = Z.load_pal(M.PAL)
x, m = Z.load(v, meta['src']); lo = Z.resize(x, meta['w'] * sub, meta['h'] * sub, Image.BOX)
lab = Z.rgb2lab(lo); pl = Z.rgb2lab(np.array(rgb, float)); idx = ((lab[:, :, None] - pl[None, None]) ** 2).sum(-1).argmin(-1)
ch = np.array(keys)[idx]; ch[(lo > 245).all(-1)] = '.'
print('    ' + ''.join(str(t % 10) for t in range(x0, x1) for _ in range(sub)))
for y in range((y0 - meta['oy']) * sub, (y1 - meta['oy']) * sub):
    print(f'{y // sub + meta["oy"]:3d} ' + ''.join(ch[y, (x0 - meta['ox']) * sub:(x1 - meta['ox']) * sub]))
