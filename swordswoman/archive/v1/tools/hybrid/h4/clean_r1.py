"""S3 r1 polish pass A: de-mush the pixelized BODY (head stamp, eyes and katana protected).
material majority filter -> small-island merge -> per-material tone smoothing (keeps Gemini's light pattern,
drops the noise) -> tone orphan merge -> interior-K speck removal -> closed sel-out outline."""
import sys, json; sys.path.insert(0, 'tools/hybrid/s3')
import numpy as np
from PIL import Image
from pol import C, INV, load, save, chars, put, find_head, ccl
MAT = {}
for ch, m in [('vrRC', 'red'), ('lL', 'lea'), ('msS', 'skin'), ('hHJ', 'hair'), ('pP', 'pink'), ('d', 'dark'),
              ('tTw', 'steel'), ('eE', 'eye'), ('K', 'K'), ('u', 'pur')]:
    for c in ch: MAT[c] = m
RAMP = {'red': 'vrRC', 'lea': 'lL', 'skin': 'msS', 'hair': 'hHJ', 'pink': 'pP', 'dark': 'd'}
DARKER = {'red': 'v', 'lea': 'K', 'skin': 'm', 'hair': 'h', 'pink': 'p', 'dark': 'K'}

def head_mask(a, d, guess):
    h = np.array(Image.open(f'hybrid/lock/pixel/head_{d}.png').convert('RGBA'))
    hx, hy = find_head(a, d, guess, r=7)
    M = np.zeros(a.shape[:2], bool)
    m = h[..., 3] > 0
    M[hy:hy + m.shape[0], hx:hx + m.shape[1]] = m
    return M, (hx, hy)

def gblur(v, w, s=1.0):
    k = np.exp(-np.arange(-2, 3) ** 2 / (2 * s * s)); k /= k.sum()
    def conv(z):
        z = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 0, z)
        return np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, z)
    return conv(v * w) / np.maximum(conv(w), 1e-6)

def clean(a, protect, passes=2, sigma=0.9, keep_steel=True):
    H, W = a.shape[:2]
    c = chars(a)
    mat = np.vectorize(lambda ch: MAT.get(ch, '.') if ch != '.' else '.')(c)
    fixed = protect | np.isin(mat, ['steel', 'eye', 'pur']) | (mat == '.')
    # 1 material majority (3x3), body only; K is its own class but thin K lines survive (needs >=5 of 9 to flip)
    for _ in range(passes):
        new = mat.copy()
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if fixed[y, x]: continue
                nb = mat[y-1:y+2, x-1:x+2].ravel()
                vals, cnt = np.unique([v for v in nb if v not in ('.',)], return_counts=True)
                if len(vals) == 0: continue
                best = vals[np.argmax(cnt)]
                if best != mat[y, x] and cnt.max() >= 5 and best not in ('steel', 'eye', 'pur'):
                    if mat[y, x] == 'K' and (np.sum(nb == '.') > 0): continue     # keep exterior outline
                    new[y, x] = best
        mat = new
    # 2 small islands (<=3 px) of a body material -> majority of the border
    for m in ['red', 'lea', 'skin', 'hair', 'pink', 'dark', 'K']:
        lab, sz = ccl(mat == m)
        for i in range(1, len(sz)):
            comp = lab == i
            if sz[i] > (2 if m in ('pink', 'K') else 3) or (comp & fixed).any(): continue
            ys, xs = np.nonzero(comp)
            border = []
            for y, x in zip(ys, xs):
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = mat[y + dy, x + dx]
                    if v != m and v not in ('.', 'steel', 'eye'): border.append(v)
            if border:
                b = max(set(border), key=border.count)
                mat[comp] = b
    # 3 tones: smooth the original tone index inside each material, re-quantize
    out = a.copy()
    for m, ramp in RAMP.items():
        reg = (mat == m) & ~protect
        if not reg.any(): continue
        idx = np.full((H, W), np.nan)
        for i, ch in enumerate(ramp):
            idx[c == ch] = i
        known = (mat == m) & ~np.isnan(idx)
        v = np.nan_to_num(idx)
        sm = gblur(v, known.astype(float), sigma)
        mid = (len(ramp) - 1) / 2
        sm = np.where(np.isnan(sm), mid, sm)
        t = np.clip(np.round(sm), 0, len(ramp) - 1).astype(int)
        for y, x in zip(*np.nonzero(reg)):
            put(out, x, y, ramp[t[y, x]])
    for y, x in zip(*np.nonzero((mat == 'K') & ~protect)):
        put(out, x, y, 'K')
    # 4 tone orphans (same material, no same-tone 4-neighbour) -> majority neighbour tone
    for _ in range(2):
        c2 = chars(out)
        for y in range(1, H - 1):
            for x in range(1, W - 1):
                if protect[y, x] or c2[y, x] == '.' or MAT.get(c2[y, x]) not in RAMP: continue
                n4 = [c2[y-1, x], c2[y+1, x], c2[y, x-1], c2[y, x+1]]
                if c2[y, x] in n4: continue
                same = [v for v in n4 if MAT.get(v) == MAT[c2[y, x]]]
                if len(same) >= 2:
                    put(out, x, y, max(set(same), key=same.count))
    # 5 interior K specks (K with no transparent 8-neighbour and K comp <=2) -> majority neighbour
    c2 = chars(out)
    lab, sz = ccl(c2 == 'K')
    for i in range(1, len(sz)):
        comp = lab == i
        if sz[i] > 2 or (comp & protect).any(): continue
        ys, xs = np.nonzero(comp)
        if any((c2[max(0,y-1):y+2, max(0,x-1):x+2] == '.').any() for y, x in zip(ys, xs)): continue
        for y, x in zip(ys, xs):
            nb = [v for v in c2[y-1:y+2, x-1:x+2].ravel() if v not in '.K']
            if nb: put(out, x, y, max(set(nb), key=nb.count))
    return out

def outline(a, protect):
    """closed exterior outline on body pixels: an edge pixel of a >=2 px thick part becomes K (bottom/right) or the
    material's dark tone (top/left, sel-out)."""
    c = chars(a); H, W = a.shape[:2]; out = a.copy()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            v = c[y, x]
            if protect[y, x] or v in '.KtTweEu' or MAT.get(v) == 'pink': continue
            for dy, dx in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                if c[y + dy, x + dx] == '.':
                    if c[y - dy, x - dx] in '.': break          # 1 px thin: keep colour
                    lit = dy == -1 or dx == -1
                    put(out, x, y, DARKER[MAT[v]] if lit else 'K')
                    break
    return out

if __name__ == '__main__':
    src, d, gx, gy, dst = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    a = load(src); M, _ = head_mask(a, d, (gx, gy))
    save(outline(clean(a, M), M), dst)
