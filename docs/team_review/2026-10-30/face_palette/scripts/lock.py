"""Before/after recolour to the proposed LOCKED 14-colour palette (K h H g L s S e E R Q O o W).
Key remap (pure palette lock, no re-shading): D->h, d->H (socks join the dark ramp), k->s, m->S, sock rim g->H;
skin interior h/R crumbs (isolated, 4-nbrs skin) -> s; face = proto (b') eyes+brows only. Then pxeval-style near-swap rate before/after."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
from proto import *
from audit import matmap, MN
from swaps import swaps
LOCK = ['K', 'h', 'H', 'g', 'L', 's', 'S', 'e', 'E', 'R', 'Q', 'O', 'o', 'W']
GLOBAL = {'D': 'h', 'd': 'H', 'k': 's', 'm': 'S'}
def keys_of(a):
    k = np.full(a.shape[:2], '', object); m = a[..., 3] > 0
    for c, rgb in HEX.items(): k[m & (a[..., :3] == rgb).all(-1)] = c
    return k
def to_img(k, a):
    out = a.copy()
    for c in LOCK: out[k == c, :3] = HEX[c]
    return out
def lock(a, mm=None):
    k = keys_of(a)
    if mm is not None:
        sock = mm == MN.index('socks'); k[sock & (k == 'g')] = 'H'
    for s_, t in GLOBAL.items(): k[k == s_] = t
    sk = (k == 's') | (k == 'S')
    nb = np.zeros(k.shape, int)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): nb += np.roll(np.roll(sk, dy, 0), dx, 1)
    k[np.isin(k, ['h', 'R', 'E', 'H']) & (nb == 4)] = 's'  # isolated dark crumbs inside skin
    return to_img(k, a)
if __name__ == '__main__':
    OUTD = OUT
    clips = [('walk', 'SE', 8, 2), ('run', 'SE', 8, 3), ('idle', 'S', 12, 0)]
    res = {}; tiles = []
    for act, v, n, show in clips:
        bef, aft = [], []
        for i in range(n):
            a = np.asarray(final(act, v, i)).copy()
            _, _, _, _, _, c, b2 = proto(act, v, i) if v in ('S', 'SE', 'E') else (None,) * 5 + (None, a)
            try: mm = matmap(act, v, i)
            except Exception: mm = None
            L = lock(b2, mm); bef.append(a); aft.append(L)
            if i == show: tiles.append((act, v, i, a, L, c))
        cb, ub = swaps(bef); ca, ua = swaps(aft)
        ncb = np.mean([len(set(map(tuple, f[f[..., 3] > 0][:, :3]))) for f in bef]); nca = np.mean([len(set(map(tuple, f[f[..., 3] > 0][:, :3]))) for f in aft])
        res[f'{act}_{v}'] = {'swap_before': sum(cb.values()) / ub, 'swap_after': sum(ca.values()) / ua, 'colours_before': ncb, 'colours_after': nca,
                             'top_after': dict(ca.most_common(6))}
        print(act, v, res[f'{act}_{v}'])
    json.dump(res, open(OUTD + 'lock_result.json', 'w'), indent=1)
    from PIL import ImageDraw
    W = 4 * 72 + 10; s = Image.new('RGBA', (W * 2 + 20, 400 * len(tiles) // 1), (96, 128, 96, 255))
    rows = []
    for act, v, i, a, L, c in tiles:
        r = Image.new('RGBA', (72 * 2 + 4 + 2 * 48 * 4 + 8, 200), (96, 128, 96, 255))
        r.alpha_composite(Image.fromarray(a).crop((28, 20, 100, 120)), (0, 50)); r.alpha_composite(Image.fromarray(L).crop((28, 20, 100, 120)), (74, 50))
        x0, y0 = int(c[0]) - 24, int(c[1]) - 10
        for k, im in enumerate((a, L)): r.alpha_composite(Image.fromarray(im).crop((x0, y0, x0 + 48, y0 + 50)).resize((192, 200), Image.NEAREST), (150 + k * 196, 0))
        ImageDraw.Draw(r).text((2, 2), f'{act} {v} f{i:02d}\nbefore | after', fill=(255, 255, 0, 255)); rows.append(r)
    s = Image.new('RGBA', (rows[0].width, 202 * len(rows)), (40, 40, 40, 255))
    for k, r in enumerate(rows): s.alpha_composite(r, (0, k * 202))
    s.save(OUTD + 'palette_before_after.png'); print('ok')
