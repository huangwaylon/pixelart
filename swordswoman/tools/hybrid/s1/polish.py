"""S1 holistic polish (Claude pixel pass, scripted, exact pixels):
 1. baseline normalise (feet row -> 104, apex keeps guide lift)
 2. paste the LOCKED head stamp (byte-identical per direction) at the guide head position, refined on hair overlap
 3. remove leftover Gemini head pixels outside the stamp
 4. per-frame FX ops (smears, echoes, motion lines, dust) via tools/hybrid/draw.py
in : hybrid/S1_redraw/r1/sprite/<name>.png (pixelize output)  -> out: same path (pixelize copy kept as <name>_src.png? no: _pix.png in work/)
"""
import json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
B = R + '/hybrid/S1_redraw/r1'
PAL = json.load(open(R + '/docs/palette.json'))
HEX = {PAL['outline'].lower(): 'outline'}
for ramp, cs in PAL['ramps'].items():
    for i, c in enumerate(cs):
        HEX.setdefault(c.lower(), f'{ramp}_{i}')
FR = json.load(open(B + '/guide_in/frames.json'))
CFG = json.load(open(B + '/polish_cfg.json'))

def names(a):
    out = np.full(a.shape[:2], '', dtype=object)
    for y in range(a.shape[0]):
        for x in range(a.shape[1]):
            if a[y, x, 3] > 0:
                out[y, x] = HEX.get('#%02x%02x%02x' % tuple(a[y, x, :3]), '?')
    return out

def ramp_mask(nm, *ramps):
    return np.vectorize(lambda s: s.split('_')[0] in ramps if s else False, otypes=[bool])(nm)

def stamp_for(name):
    d = name.split('_')[1] if not name.startswith(('walk', 'slash', 'jump')) else name.split('_')[1]
    return d

EXPR = {
 ('SE', 'frown'): [(25, 12, 'outline'), (25, 18, 'outline'), (24, 13, 'outline'), (24, 17, 'outline')],
 ('E', 'frown'): [(25, 22, 'outline'), (24, 22, 'outline')],
 ('E', 'effort'): [(25, 19, 'outline'), (25, 20, 'outline'), (25, 21, 'outline'), (25, 22, 'outline'), (26, 19, 'skin_1'), (26, 20, 'skin_1'), (26, 21, 'outline'), (26, 22, 'skin_1'), (24, 18, 'skin_1'), (24, 19, 'skin_1'), (24, 20, 'skin_1'), (24, 21, 'skin_1')],
 ('E', 'smile'): [(24, 18, 'skin_1'), (24, 19, 'skin_1'), (24, 20, 'skin_1'), (24, 21, 'skin_1'), (25, 19, 'skin_1'), (25, 20, 'outline'), (25, 21, 'outline'), (25, 22, 'skin_1'), (26, 19, 'outline'), (26, 20, 'skin_1'), (26, 21, 'skin_1'), (26, 22, 'outline')],
}

def rgba(n):
    if n == 'outline': h = PAL['outline']
    else:
        r, i = n.rsplit('_', 1); h = PAL['ramps'][r][int(i)]
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255], np.uint8)

def line_px(x0, y0, x1, y1):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    return [(int(round(x0 + (x1 - x0) * t / max(n - 1, 1))), int(round(y0 + (y1 - y0) * t / max(n - 1, 1)))) for t in range(n)]

def redraw_katana(a, c, inside, name=''):
    """Find the pixelized blade (steel component), erase it, redraw a hand-pixel katana: 2 px blade
    (steel_2 edge + steel_0 spine), guard bar + small crescent hook, wrapped hilt behind the hand."""
    from scipy import ndimage
    nm = names(a)
    steel = ramp_mask(nm, 'steel') & ~inside
    lab, n = ndimage.label(steel, structure=np.ones((3, 3)))
    sz = ndimage.sum(steel, lab, range(1, n + 1))
    for i, z in enumerate(sz):
        if z < 4: steel[lab == i + 1] = False
    if 'hand' in c and 'tip' in c:
        H = np.array(c['hand'], float); P = np.array(c['tip'], float)
        comp = steel.copy()   # every elongated steel component outside the head stamp is old blade: clear it
    else:
        # all steel pixels in elongated components, merged
        pts = np.argwhere(steel)[:, ::-1].astype(float)
        if len(pts) < 8: return a
        body = (a[..., 3] > 0) & ~steel
        bc = np.argwhere(body)[:, ::-1].mean(0)
        rng = np.random.default_rng(0); bestn = -1
        for _ in range(400):
            i, j = rng.choice(len(pts), 2, replace=False)
            d = pts[j] - pts[i]; nd = np.linalg.norm(d)
            if nd < 6: continue
            nrm = np.array([-d[1], d[0]]) / nd
            inl = np.abs((pts - pts[i]) @ nrm) < 1.6
            if inl.sum() > bestn: bestn, best_i = inl.sum(), inl
        sel = pts[best_i]; m = sel.mean(0); _, _, vt = np.linalg.svd(sel - m); ax = vt[0]
        t = (pts - m) @ ax
        dist = np.abs((pts - m) @ np.array([-ax[1], ax[0]]))
        keep = dist < 2
        pts = pts[keep]; t = t[keep]
        e0 = pts[t.argmin()]; e1 = pts[t.argmax()]
        H, P = (e0, e1) if np.linalg.norm(e0 - bc) < np.linalg.norm(e1 - bc) else (e1, e0)
        comp = np.zeros_like(steel)
        for (x, y) in pts.astype(int): comp[y, x] = True
    a[comp] = 0
    print('  katana', name, 'hand', H.round(1).tolist(), 'tip', P.round(1).tolist())
    v = P - H; L = np.linalg.norm(v); u = v / L
    perp = np.array([-u[1], u[0]])
    if abs(u[0]) < abs(u[1]): off = (1, 0)   # mostly vertical blade: spine one px to the right
    else: off = (0, 1)                        # mostly horizontal: spine one px below
    G = H + u * c.get('grip', 3)              # guard position
    skin = ramp_mask(nm, 'skin')
    behind = c.get('behind', False)
    occ = (a[..., 3] > 0).copy()
    def put(x, y, n, over_skin=False):
        if behind and occ[y % 128, x % 128]: return
        if 0 <= x < 128 and 0 <= y < 128 and (over_skin or not skin[y, x]):
            a[y, x] = rgba(n)
    # blade
    for i, (x, y) in enumerate(line_px(G[0] + u[0] * 2, G[1] + u[1] * 2, P[0], P[1])):
        put(x, y, 'steel_2'); 
        if i < L - 4: put(x + off[0], y + off[1], 'steel_0')
    # guard bar (perpendicular, 2 px each side) + crescent hook bent toward the tip on the outer side
    for k in (-2, -1, 0, 1, 2):
        x, y = int(round(G[0] + perp[0] * k)), int(round(G[1] + perp[1] * k))
        put(x, y, 'steel_1' if abs(k) < 2 else 'outline', True)
    hx, hy = G + perp * 3 + u * 1
    put(int(round(hx)), int(round(hy)), 'steel_1', True)
    hx, hy = G + perp * 3 + u * 2
    put(int(round(hx)), int(round(hy)), 'outline', True)
    # hilt behind the hand (wrap R/d alternating, kashira steel)
    hl = c.get('hilt', 6)
    for i, (x, y) in enumerate(line_px(G[0] - u[0], G[1] - u[1], G[0] - u[0] * hl, G[1] - u[1] * hl)):
        put(x, y, 'red_2' if i % 2 else 'outline')
        put(x + off[0], y + off[1], 'outline' if i % 2 else 'red_1')
    kx, ky = G - u * (hl + 1)
    put(int(round(kx)), int(round(ky)), 'steel_1')
    return a

def flatten_small(a, inside, ramps=('red', 'skin', 'leather', 'hair'), maxn=2):
    """Merge tiny same-tone clusters (<= maxn px) inside a ramp into the dominant neighbouring tone of the same ramp
    (kills render-noise blotches; never touches the head stamp, outline or other ramps)."""
    from scipy import ndimage
    nm = names(a)
    for _ in range(2):
        for t in sorted(set(nm[(a[..., 3] > 0) & ~inside].tolist())):
            if not t or t.split('_')[0] not in ramps: continue
            m = (nm == t) & ~inside
            lab, n = ndimage.label(m)
            for i in range(1, n + 1):
                cm = lab == i
                if cm.sum() > maxn: continue
                ring = ndimage.binary_dilation(cm, np.ones((3, 3))) & ~cm
                nb = [x for x in nm[ring].tolist() if x and x.split('_')[0] == t.split('_')[0] and x != t]
                if len(nb) >= 3:
                    v = max(set(nb), key=nb.count)
                    a[cm] = rgba(v); nm[cm] = v
    return a

def derive(dv):
    """Claude squash/stretch key built from another frame's pixel body (keeps cross-frame identity):
    take the source frame (baseline-normalised, its dx), drop its steel, resample the body
    nearest-neighbour by (sx, sy) about the feet pivot, then the head stamp is pasted on top later."""
    src = dv['from']; sc = CFG.get(src, {})
    a = np.array(Image.open(f'{B}/work/pix/{src}.png').convert('RGBA'))
    a[a[..., 3] < 128] = 0; a[..., 3][a[..., 3] > 0] = 255
    nm = names(a); steel = ramp_mask(nm, 'steel'); body = (a[..., 3] > 0) & ~steel
    dy = sc.get('baseline', 104) - np.nonzero(body.any(1))[0].max()
    a = np.roll(a, dy, axis=0); a = np.roll(a, sc.get('dx', 0), axis=1)
    a[ramp_mask(names(a), 'steel')] = 0
    sx, sy = dv.get('sx', 1.0), dv.get('sy', 1.0); px, py = dv.get('px', 64), 104
    out = np.zeros_like(a)
    for y in range(128):
        for x in range(128):
            sxp = int(round(px + (x - px) / sx)); syp = int(round(py + (y - py) / sy))
            if 0 <= sxp < 128 and 0 <= syp < 128: out[y, x] = a[syp, sxp]
    return out

def main(only):
    for name, pre in FR.items():
        if only and name not in only: continue
        c = CFG.get(name, {})
        src = f'{B}/work/pix/{name}.png'
        os.makedirs(B + '/work/pix', exist_ok=True)
        if not os.path.exists(src): shutil.copy(f'{B}/sprite/{name}.png', src)
        a = np.array(Image.open(src).convert('RGBA'))
        a[a[..., 3] < 128] = 0; a[..., 3][a[..., 3] > 0] = 255
        nm = names(a)
        steel = ramp_mask(nm, 'steel')
        body = (a[..., 3] > 0) & ~steel
        ys = np.nonzero(body.any(1))[0]
        target = c.get('baseline', 104)
        dy = target - ys.max()
        a = np.roll(a, dy, axis=0)
        if dy > 0: a[:dy] = 0
        elif dy < 0: a[dy:] = 0
        dx = c.get('dx', 0)
        if dx: a = np.roll(a, dx, axis=1)
        if 'derive' in c:
            a = derive(c['derive'])
        nm = names(a)
        # --- head stamp
        d = name.split('_')[1]
        st = np.array(Image.open(f'{R}/hybrid/lock/pixel/head_{d}.png').convert('RGBA'))
        meta = json.load(open(R + '/hybrid/lock/pixel/stamps.json'))['stamps'][f'head_{d}']
        hair = ramp_mask(nm, 'hair')
        from scipy import ndimage
        hl, hn = ndimage.label(hair, structure=np.ones((3, 3)))
        hs = ndimage.sum(hair, hl, range(1, hn + 1))
        blob = hl == (int(np.argmax(hs)) + 1)
        by, bx = np.nonzero(blob)
        face = ramp_mask(nm, 'skin', 'eye') & (np.arange(128)[:, None] >= by.min()) & (np.arange(128)[:, None] <= by.max() + 2) \
            & (np.arange(128)[None, :] >= bx.min() - 3) & (np.arange(128)[None, :] <= bx.max() + 3)
        uy, ux = np.nonzero(blob | face)
        hcx = (ux.min() + ux.max()) / 2.0
        hbot = by.max() + (0 if d in ('N', 'NE', 'NW') else 1)
        mode = c.get('head_mode', 'guide')
        if mode == 'guide':
            J = json.load(open(pre + '_joints.json'))['joints']
            hcx = J['head']['cell'][0]; hbot = J['chin']['cell'][1] if d not in ('N', 'NE', 'NW') else J['neck']['cell'][1] - 1
        gx = int(round(hcx - meta['cx'])) + (dx if mode == 'guide' else 0); gy = int(round(hbot - meta['bottom']))
        smask = st[..., 3] > 0
        sh, sw = smask.shape
        best = None
        for oy in range(-2, 3):
            for ox in range(-2, 3):
                x0, y0 = gx + ox, gy + oy
                win = hair[y0:y0 + sh, x0:x0 + sw]; op = (a[y0:y0 + sh, x0:x0 + sw, 3] > 0)
                if win.shape != smask.shape: continue
                sc = (win & smask).sum() - 0.6 * (smask & ~op).sum() - 1.0 * (oy * oy + ox * ox)
                if best is None or sc > best[0]: best = (sc, x0, y0)
        _, x0, y0 = best
        x0 += c.get('hx', 0); y0 += c.get('hy', 0)
        if 'head_y' in c: y0 = c['head_y']
        if 'head_x' in c: x0 = c['head_x']
        # leftovers: hair / eye / face-skin pixels above the stamp chin outside the stamp, and bow-red above the skull
        yy, xx = np.mgrid[0:128, 0:128]
        inside = np.zeros((128, 128), bool); inside[y0:y0 + sh, x0:x0 + sw] = smask
        near = (xx >= x0 - 6) & (xx < x0 + sw + 6) & (yy < y0 + sh - 2)
        nm = names(a)
        kill = near & ~inside & (ramp_mask(nm, 'hair', 'eye') | (ramp_mask(nm, 'red') & (yy < y0 + 12)) | ((nm == 'outline') & (yy < y0 + 20)))
        for k in c.get('keep_boxes', []):
            kill[k[1]:k[3] + 1, k[0]:k[2] + 1] = False
        a[kill] = 0
        # paste stamp (opaque pixels only) + expression patch (stamp-local)
        st = st.copy()
        for (r_, c_, t_) in EXPR.get((d, c.get('expr', 'calm')), []):
            st[r_, c_] = rgba(t_)
        reg = a[y0:y0 + sh, x0:x0 + sw]; reg[smask] = st[smask]
        for bx0, by0, bx1, by1 in c.get('erase_steel', []):
            nm2 = names(a); m2 = ramp_mask(nm2, 'steel'); box = np.zeros_like(m2); box[by0:by1 + 1, bx0:bx1 + 1] = True
            a[m2 & box] = 0
        # remove isolated leftover specks (components < 4 px not touching the body) -- simple 8-neighbour pass
        op = a[..., 3] > 0
        from scipy import ndimage
        lab, n = ndimage.label(op, structure=np.ones((3, 3)))
        sizes = ndimage.sum(op, lab, range(1, n + 1))
        for i, s in enumerate(sizes):
            if s < c.get('speck', 6): a[lab == i + 1] = 0
        a = flatten_small(a, inside)
        if c.get('sword', True):
            a = redraw_katana(a, c, inside, name)
        out = f'{B}/sprite/{name}.png'
        Image.fromarray(a).save(out)
        ops = c.get('ops', [])
        if ops:
            r = subprocess.run([R + '/.venv/bin/python', R + '/tools/hybrid/draw.py', out, '--out', out] + ops, capture_output=True, text=True)
            if r.returncode: print(name, 'draw FAIL', r.stderr[-400:])
        if c.get('bstamps'):
            import sys as _s; _s.path.insert(0, R + '/tools/hybrid'); import pixgrid as PG
            a = np.array(Image.open(out).convert('RGBA'))
            for bx, by, pat in c['bstamps']:
                for j, row in enumerate(pat.split('/')):
                    for i, ch in enumerate(row):
                        if ch in '_.': continue
                        if a[by + j, bx + i, 3] == 0: a[by + j, bx + i] = rgba(PG.STD[ch] if PG.STD[ch] != 'outline' else 'outline')
            Image.fromarray(a).save(out)
        print(name, 'dy', dy, 'stamp', d, (x0, y0))

if __name__ == '__main__':
    main(sys.argv[1:])
