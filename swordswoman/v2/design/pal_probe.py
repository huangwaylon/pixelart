"""Palette-locked readability probe: pal_probe.py out.png img... [--h 40,48] [--s 4] [--pal palette.json] [--ol] [--mode]
Crop subject (non-white), box-downsample to N px tall, snap to v2/pixel/palette.json (excluding VFX), add 1px dark outline where missing, show at S x on mid-grey."""
import sys, json, numpy as np
from PIL import Image, ImageDraw
a = sys.argv[1:]; hs = [40, 48]; S = 4; OL = '--ol' in a; KAT = '--kat' in a
if OL: a.remove('--ol')
if KAT: a.remove('--kat')
MODE = '--mode' in a
if MODE: a.remove('--mode')
if '--h' in a: i = a.index('--h'); hs = [int(v) for v in a[i+1].split(',')]; del a[i:i+2]
if '--s' in a: i = a.index('--s'); S = int(a[i+1]); del a[i:i+2]
PAL = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixel/palette.json'
if '--pal' in a: i = a.index('--pal'); PAL = a[i+1]; del a[i:i+2]
P = json.load(open(PAL))['colors']
out, imgs = a[0], a[1:]
pal = np.array([[int(v[0][j:j+2], 16) for j in (1, 3, 5)] for k, v in P.items() if k not in 'uU'], float)
def lab(c):  # cheap perceptual-ish: weighted RGB
    return c
BG = (110, 110, 118)
def C(k): return np.array([int(P[k][0][j:j+2], 16) for j in (1, 3, 5)], float)
def blade(x):  # source blade mask: light low-sat elongated blob in lower 60%
    from scipy import ndimage as nd
    v = x.max(-1); s = v - x.min(-1); m = (s < 28) & (v > 120) & (v < 246); m[:int(len(m) * 0.4)] = 0
    m = nd.binary_opening(m, np.ones((5, 5))); lab, n = nd.label(m)
    return lab == (nd.sum(m, lab, range(1, n + 1)).argmax() + 1)
def draw_blade(q, bm, k, mm):
    """Katana rule (r3G): 2px steel (w top px, n lower px) + 1px dark (#) underside edge, one clean stack per column (no irregular stair-steps); tip 1px n + #."""
    ys, xs = np.where(bm); c = np.array([xs.mean(), ys.mean()]); pts = np.stack([xs, ys], 1) - c
    d = np.linalg.svd(pts, full_matrices=False)[2][0]; t = pts @ d
    A = (c + d * t.min() + 0.5) * k - 0.5; B = (c + d * t.max() + 0.5) * k - 0.5
    if A[1] > B[1]: A, B = B, A  # A = hilt end (upper), B = tip
    h, w = q.shape[:2]; old = np.array(Image.fromarray(bm.astype(np.float32), 'F').resize((w, h), Image.BOX)) > 0.2
    q[old] = BG; mm[old] = False
    # clean raster: step along the major axis, one stack per step = w, n (2px steel) then # (dark edge, underside)
    dx, dy = B - A; steps = int(round(max(abs(dx), abs(dy))))
    if abs(dx) >= abs(dy):  # shallow: vertical stacks per column
        for t in range(steps + 1):
            px = int(round(A[0] + dx * t / steps)); py = int(round(A[1] + dy * t / steps))
            stack = [('w', 0), ('n', 1), ('#', 2)] if t < steps - 1 else [('n', 0), ('#', 1)]
            for c, o in stack:
                if 0 <= py + o < h and 0 <= px < w and not (c == '#' and mm[py + o, px]): q[py + o, px] = C(c)
    else:  # steep: horizontal stacks per row, dark edge on the side away from the body centre
        sgn = 1 if dx * dy > 0 else -1
        for t in range(steps + 1):
            px = int(round(A[0] + dx * t / steps)); py = int(round(A[1] + dy * t / steps))
            stack = [('w', 0), ('n', -sgn), ('#', -2 * sgn)] if t < steps - 1 else [('n', 0), ('#', -sgn)]
            for c, o in stack:
                if 0 <= py < h and 0 <= px + o < w and not (c == '#' and mm[py, px + o]): q[py, px + o] = C(c)
def proc(p, h):
    im = Image.open(p).convert('RGB'); x = np.array(im).astype(float)
    bm = blade(x) if KAT and '_k' in p.split('/')[-1] else None
    m = (x.min(-1) < 215) | (x.max(-1) - x.min(-1) > 30)
    ys, xs = np.where(m); y0, x0 = ys.min(), xs.min()
    if bm is not None: bm = bm[ys.min():ys.max()+1, xs.min():xs.max()+1]
    x = x[ys.min():ys.max()+1, xs.min():xs.max()+1]; m = m[ys.min():ys.max()+1, xs.min():xs.max()+1]
    H, W = m.shape; w = max(1, round(W * h / H))
    mf = m.astype(np.float32)
    num = np.stack([np.array(Image.fromarray((x[..., c] * mf).astype(np.float32), 'F').resize((w, h), Image.BOX)) for c in range(3)], -1)
    den = np.array(Image.fromarray(mf, 'F').resize((w, h), Image.BOX))
    sm = num / np.maximum(den, 1e-6)[..., None]; mm = den > 0.45
    d = ((lab(sm)[:, :, None, :] - lab(pal)[None, None]) ** 2).sum(-1); q = pal[d.argmin(-1)]
    if MODE:  # majority vote of palette-snapped sub-samples (4x4 per cell); darkest colour down-weighted so thin limbs keep their fill
        F = 4; hi = np.array(Image.fromarray(x.astype(np.uint8)).resize((w * F, h * F), Image.BOX)).astype(float)
        hm = np.array(Image.fromarray(m.astype(np.uint8) * 255).resize((w * F, h * F), Image.BOX)) > 127
        di = ((hi[:, :, None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1); di[~hm] = -1
        blk = di.reshape(h, F, w, F).transpose(0, 2, 1, 3).reshape(h, w, F * F)
        wt = np.ones(len(pal)); wt[np.argmin(pal.sum(1))] = 0.45
        votes = np.stack([(blk == k).sum(-1) * wt[k] for k in range(len(pal))], -1)
        q = pal[votes.argmax(-1)]
    if OL:  # outer silhouette outline: boundary pixels of mask -> darkest
        e = mm & ~(np.roll(mm,1,0) & np.roll(mm,-1,0) & np.roll(mm,1,1) & np.roll(mm,-1,1))
        q[e] = pal[0]
    q[~mm] = BG
    if bm is not None: draw_blade(q, bm, h / H, mm)
    return Image.fromarray(q.astype(np.uint8)).resize((w * S, h * S), Image.NEAREST)
cols = [[proc(p, h) for h in hs] for p in imgs]
W = sum(max(c.width for c in col) + 16 for col in cols) + 16; Ht = sum(max(h * S for _ in [0]) + 24 for h in hs) + 8
sh = Image.new('RGB', (W, Ht), BG); dr = ImageDraw.Draw(sh); x = 16
for p, col in zip(imgs, cols):
    y = 8; dr.text((x, 0), p.split('/')[-1][:14], fill='white')
    for h, t in zip(hs, col): y += 14; sh.paste(t, (x, y + h * S - t.height)); y += h * S + 10
    x += max(c.width for c in col) + 16
sh.save(out); print(out, sh.size)
