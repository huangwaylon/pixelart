"""probe.py: board.py-style helpers. sprite(path,h=48)->PIL RGB (palette-locked, mode vote, 1px outline, bg=None->RGBA)"""
import json, numpy as np
from PIL import Image
P = json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/pk_palette.json'))['colors']
KEYS = [k for k in P if k not in 'nk']
pal = np.array([[int(P[k][0][j:j+2], 16) for j in (1, 3, 5)] for k in KEYS], float)
def sprite(p, h=48, F=4):
    x = np.array(Image.open(p).convert('RGB')).astype(float)
    m = (x.min(-1) < 215) | (x.max(-1) - x.min(-1) > 30)
    ys, xs = np.where(m); x = x[ys.min():ys.max()+1, xs.min():xs.max()+1]; m = m[ys.min():ys.max()+1, xs.min():xs.max()+1]
    H, W = m.shape; w = max(1, round(W * h / H))
    hi = np.array(Image.fromarray(x.astype(np.uint8)).resize((w*F, h*F), Image.BOX)).astype(float)
    hm = np.array(Image.fromarray(m.astype(np.uint8)*255).resize((w*F, h*F), Image.BOX)) > 127
    di = ((hi[:, :, None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1); di[~hm] = -1
    blk = di.reshape(h, F, w, F).transpose(0, 2, 1, 3).reshape(h, w, F*F)
    wt = np.ones(len(pal)); wt[KEYS.index('K')] = 0.5
    votes = np.stack([(blk == k).sum(-1) * wt[k] for k in range(len(pal))], -1)
    q = pal[votes.argmax(-1)]; mm = (blk >= 0).sum(-1) > F*F*0.4
    e = mm & ~(np.roll(mm,1,0) & np.roll(mm,-1,0) & np.roll(mm,1,1) & np.roll(mm,-1,1)); q[e] = pal[KEYS.index('K')]
    a = np.dstack([q, mm[..., None]*255]).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')
