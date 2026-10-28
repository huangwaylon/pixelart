#!/usr/bin/env python3
"""mf.py: MASTERS-F toolkit (pk_palette char-maps, 64x64, soles row 61).
  mf.py png in.txt out.png [--s N]       render
  mf.py check V [file]                   material map (vs prop/blockout/V) -> prop verify + silhouette diff + lint_style
Master meta: '; crown R' (default 14) = first row of the head proper; hair-coloured px above it count as bun (B).
Face layer: mastersF/<V>_face.txt (same size, face pixels only; '.' elsewhere)."""
import sys, json, subprocess, numpy as np
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/'
sys.path.insert(0, R + 'prop/tools'); import verify
PAL = {k: v[0] for k, v in json.load(open(R + 'style/pk_palette.json'))['colors'].items()}
PAL['n'] = '#78b8f0'; PAL['k'] = '#f8a0a0'  # face2 repurposed slots (iris glow, blush); no sword
def load(p):
    rows, meta = [], {}
    for l in open(p):
        l = l.rstrip('\n')
        if l.startswith(';'):
            t = l[1:].split(); meta[t[0]] = t[1:] if t else None
        elif l.strip(): rows.append(l)
    w = max(map(len, rows)); return np.array([list(r.ljust(w, '.')) for r in rows]), meta
def png(g, out, s=1, bg=None):
    from PIL import Image
    im = Image.new('RGBA', (g.shape[1], g.shape[0]), bg or (0, 0, 0, 0)); px = im.load()
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            c = g[y, x]
            if c in PAL: h = PAL[c]; px[x, y] = (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255)
    im = im.resize((g.shape[1] * s, g.shape[0] * s), 0); im.save(out) if out else None; return im
CLS = dict(H='HhL', B='HhL', W='eERr', D='eERr', A='eERr', F='sSkr', N='sS', h='sS', L='sS', O='dhLs', T='dhL', e='iIWK')
def material(g, v, meta):
    B, _ = load(R + f'prop/blockout/{v}.txt'); crown = int((meta.get('crown') or [14])[0])
    chin = min(r for r in range(64) if 'N' in B[r])
    m = np.full(g.shape, '.', dtype='<U1'); K = []
    def nearest(r, x, codes):
        best = None
        for rr in range(max(0, r - 3), min(64, r + 4)):
            for xx in range(64):
                if B[rr, xx] in codes:
                    d = abs(rr - r) * 3 + abs(xx - x)
                    if best is None or d < best[0]: best = (d, B[rr, xx])
        return best[1] if best else codes[0]
    for r in range(64):
        for x in range(64):
            c = g[r, x]; b = B[r, x]
            if c == '.': continue
            if c == 'K': K.append((r, x)); continue
            if c in 'iInW' and r < chin: m[r, x] = 'e'; continue
            if b != '.' and c in CLS.get(b, '') and not (b in 'HB' and r >= crown) | (b == 'H' and r < crown):
                m[r, x] = b; continue
            hairnb = c == 'h' and any(g[rr, xx] in 'HL' for rr in range(max(0, r-1), min(64, r+2)) for xx in range(max(0, x-1), min(64, x+2)))
            if c in 'HL' or (c == 'h' and (r < chin + 2 or hairnb)): m[r, x] = 'B' if r < crown else 'H'
            elif c in 'eERr': m[r, x] = 'W' if r < chin else nearest(r, x, 'DA')
            elif c in 'sSk': m[r, x] = 'F' if r < chin else nearest(r, x, 'NhL')
            elif c in 'dh': m[r, x] = nearest(r, x, 'OT') if r >= chin else 'H'
            else: m[r, x] = b if b != '.' else 'D'
    for _ in range(4):  # outline pixels take the code of an opaque non-K neighbour (head: hair beats face)
        left = []
        for r, x in K:
            nb = [m[rr, xx] for rr, xx in ((r-1, x), (r+1, x), (r, x-1), (r, x+1), (r-1, x-1), (r-1, x+1), (r+1, x-1), (r+1, x+1))
                  if 0 <= rr < 64 and 0 <= xx < 64 and m[rr, xx] != '.']
            if not nb: left.append((r, x)); continue
            pref = [c for c in 'eHTLDAhONBWF' if c in nb]
            if B[r, x] != '.' and r >= chin: m[r, x] = B[r, x]
            else: m[r, x] = pref[0]
        K = left
    for r, x in K: m[r, x] = 'H'
    Bb, _ = load(R + f'prop/blockout/{v}_body.txt'); body = m.copy()  # arms removed; occluded body taken from blockout _body
    occ = np.isin(m, ['A', 'h']); occ[chin + 1:] |= m[chin + 1:] == 'H'  # arms and hair hanging over the body occlude it
    for r, x in zip(*np.where(occ)): body[r, x] = Bb[r, x] if Bb[r, x] in 'DOL' else '.'
    return m, body, B, chin
def check(v, f=None):
    f = f or R + f'mastersF/{v}.txt'; g, meta = load(f)
    assert g.shape == (64, 64), g.shape
    m, body, B, chin = material(g, v, meta)
    H, mm, w, rep, bad = verify.check(v, m, body)
    diff = [(r, x) for r in range(chin, 64) for x in range(64) if (g[r, x] != '.') != (B[r, x] != '.')]
    out = f"{v} verify {'PASS' if not bad else 'FAIL'} H{H} " + ' '.join(rep) + (('\n  FAILS: ' + '; '.join(bad)) if bad else '')
    out += f"\n  body silhouette diff vs blockout: {len(diff)} px" + (f" (rows {sorted(set(r for r,_ in diff))})" if diff else '')
    lint = subprocess.run([R + '../.venv/bin/python', R + 'anim_cut/tools/lint_style.py', f], capture_output=True, text=True).stdout.strip()
    out += '\n  lint: ' + (lint.replace('\n', '\n   ') or 'clean')
    np.savetxt(R + f'mastersF/work/{v}_mat.txt', m, fmt='%s', delimiter='')
    return out, not bad
if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'png': g, _ = load(a[1]); png(g, a[2], int(a[a.index('--s') + 1]) if '--s' in a else 1)
    elif a[0] == 'check':
        o, ok = check(a[1], a[2] if len(a) > 2 else None); print(o)
