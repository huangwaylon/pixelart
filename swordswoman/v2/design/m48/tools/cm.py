"""cm.py: char-map helpers for 48px masters (palette v2/pixel/palette.json, '.' = transparent).
  probe  in.png out.txt [--top 10 --foot 58 --cx 30 --bg white|alpha]   source image -> 64x64 palette-snapped char-map
  render in.txt out.png [--s 4] [--bg]                                  char-map -> png (1x transparent, or Sx on mid-grey with --bg)
  lint   in.txt...                                                      off-palette, orphans, metrics
"""
import sys, json, numpy as np
from PIL import Image
PJ = json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixel/palette.json'))['colors']
HEX = {k: v[0] for k, v in PJ.items()}
RGB = {k: tuple(int(h[j:j+2], 16) for j in (1, 3, 5)) for k, h in HEX.items()}
SNAP = [k for k in RGB if k not in 'uUpjk3']   # D-level: no blush/sheen; k/3 hand-placed only
GREY = (110, 110, 118)
def read(p):
    L = [l.rstrip('\n') for l in open(p) if l.strip()]
    L = [l for l in L if set(l) <= set(RGB) | {'.'} and len(l) >= 32]
    return [l.ljust(64, '.')[:64] for l in L[:64]] + ['.' * 64] * (64 - len(L[:64]))
def write(p, g): open(p, 'w').write('\n'.join(g) + '\n')
def to_img(g, s=1, bg=False):
    im = Image.new('RGBA', (64, 64), GREY + (255,) if bg else (0, 0, 0, 0)); px = im.load()
    for y, l in enumerate(g):
        for x, c in enumerate(l):
            if c in RGB: px[x, y] = RGB[c] + (255,)
    return im.resize((64 * s, 64 * s), Image.NEAREST)
def probe(src, top=10, foot=58, cx=30):
    im = Image.open(src).convert('RGBA'); a = np.array(im).astype(float)
    x = a[..., :3]; al = a[..., 3]
    m = ((x.min(-1) < 215) | (x.max(-1) - x.min(-1) > 30)) & (al > 128)
    ys, xs = np.where(m); x = x[ys.min():ys.max()+1, xs.min():xs.max()+1]; m = m[ys.min():ys.max()+1, xs.min():xs.max()+1]
    H, W = m.shape; h = foot - top + 1; w = max(1, round(W * h / H)); mf = m.astype(np.float32)
    num = np.stack([np.array(Image.fromarray((x[..., c] * mf).astype(np.float32), 'F').resize((w, h), Image.BOX)) for c in range(3)], -1)
    den = np.array(Image.fromarray(mf, 'F').resize((w, h), Image.BOX))
    sm = num / np.maximum(den, 1e-6)[..., None]; mm = den > 0.45
    pal = np.array([RGB[k] for k in SNAP], float)
    q = ((sm[:, :, None] - pal[None, None]) ** 2).sum(-1).argmin(-1)
    g = [['.'] * 64 for _ in range(64)]
    # centre of mass of lower half (legs) at cx
    lx = np.where(mm[h // 2:])[1].mean(); x0 = int(round(cx - lx))
    for yy in range(h):
        for xx in range(w):
            if mm[yy, xx] and 0 <= xx + x0 < 64: g[top + yy][xx + x0] = SNAP[q[yy, xx]]
    return [''.join(r) for r in g]
def metrics(g):
    A = np.array([list(l) for l in g]); ink = A != '.'
    rows = np.where(ink.any(1))[0]; hair = np.isin(A, list('Hh'))
    hr = np.where(hair.sum(1) >= 3)[0]
    bow = np.isin(A, list('Ee')) & (np.arange(64)[:, None] < (hr.min() + 3 if len(hr) else 30))
    br = np.where(bow.any(1))[0]
    # head width = widest hair+outline+skin row in head band
    head = ink[hr.min():hr.min() + 17] if len(hr) else ink[:0]
    hw = max((np.ptp(np.where(r)[0]) + 1) for r in head) if len(head) else 0
    skin = np.isin(A, list('123')); face = np.where(skin[:40].any(1))[0]
    return dict(top=int(rows.min()), bottom=int(rows.max()), bow_top=int(br.min()) if len(br) else -1,
                hair_top=int(hr.min()) if len(hr) else -1, hair_bot=int(hr.max()) if len(hr) else -1, head_w=int(hw),
                hair_rows_upto40=int((hair[:40].sum(1) >= 3).sum()))
def lint(g):
    A = np.array([list(l) for l in g]); P = np.pad(A, 1, constant_values='.'); orph = []
    bad = sorted({c for c in A.flat if c not in RGB and c != '.'})
    for y in range(64):
        for x in range(64):
            c = A[y, x]
            if c == '.' or c == '#': continue
            nb = [P[y, x+1], P[y+2, x+1], P[y+1, x], P[y+1, x+2]]
            if c not in nb and c not in 'wiI': orph.append((y, x, c))
    return bad, orph
if __name__ == '__main__':
    a = sys.argv[1:]; cmd = a.pop(0)
    def opt(k, d):
        if k in a: i = a.index(k); v = a[i+1]; del a[i:i+2]; return type(d)(v)
        return d
    if cmd == 'probe':
        top, foot, cx = opt('--top', 10), opt('--foot', 58), opt('--cx', 30)
        write(a[1], probe(a[0], top, foot, cx)); print('wrote', a[1])
    elif cmd == 'render':
        s = opt('--s', 1); bg = '--bg' in a
        to_img(read(a[0]), s, bg).save(a[1]); print('wrote', a[1])
    elif cmd == 'lint':
        for p in a:
            g = read(p); bad, orph = lint(g); print(p.split('/')[-1], metrics(g), 'offpal', bad, 'orphans', len(orph), orph[:8])
