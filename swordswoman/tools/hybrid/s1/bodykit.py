"""S1 r1 polish: hand-drawn BODY cels composited under the locked head stamp and the hand katana / smear FX.

  .venv/bin/python tools/hybrid/s1/bodykit.py layers [names]   # split pre-polish sprites -> work/pol/<name>_{fx,stamp}.png + _ref.txt
  .venv/bin/python tools/hybrid/s1/bodykit.py compose [names]  # body src (tools/hybrid/s1/bodies/<name>.txt) + fx + stamp -> polished/

Body source format (hand-typed, STD pixgrid chars, '.' = transparent):
    origin: X Y              top-left of the grid in the 128 cell
    from: other_name [dx dy] (optional) start from another body's grid (then 'patch:' lines edit it)
    mirror                   (optional, with from:) mirror the grid horizontally about the stamp centre
    grid:
    ....KRRK....
    patch: X Y               (cell coords) rows follow; '_' keeps, other chars paint ('.' clears)
Layer order: body < fx_under < stamp < fx (katana / smear).  'under:' line lists boxes x0,y0,x1,y1 whose fx
pixels go UNDER the body (far-side blade, E/NE behind-the-body sword).
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid')
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/s1')
import pixgrid as PG  # noqa
import polish2 as P2  # noqa

R = P2.R; B = P2.B
W = B + '/work/pol'
SRC = R + '/tools/hybrid/s1/bodies'
OUT = B + '/polished'
NAMES = [f'turn_{d}' for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']] + [f'walk_SE_k{i}' for i in range(4)] + \
        [f'slash_SE_k{i}' for i in range(4)] + [f'jump_E_{k}' for k in ['crouch', 'apex', 'land']]
CH2N = {c: n for c, n in PG.STD.items()}
N2CH = {}
for c, n in PG.STD.items():
    N2CH.setdefault(n, c)


def layers(names):
    os.makedirs(W, exist_ok=True)
    info = {}
    for name in names:
        a = np.array(Image.open(f'{B}/sprite/{name}.png').convert('RGBA'))
        d = name.split('_')[1]
        inside, (x0, y0), _ = P2.find_stamp(a, d)
        st = np.array(Image.open(f'{R}/hybrid/lock/pixel/head_{d}.png').convert('RGBA'))
        stamp = np.zeros_like(a)
        sh_, sw = st.shape[:2]
        reg = a[y0:y0 + sh_, x0:x0 + sw]
        stamp[y0:y0 + sh_, x0:x0 + sw][st[..., 3] > 0] = reg[st[..., 3] > 0]   # keeps expression patches
        nm = P2.to_names(a)
        M = np.vectorize(P2.mat, otypes=[object])(nm)
        steel = M == 'steel'
        halo = ndimage.binary_dilation(steel, P2.N8, iterations=2)
        redm = M == 'red'
        lab, n = ndimage.label(redm, structure=P2.N4)
        sz = ndimage.sum(redm, lab, range(1, n + 1))
        small_red = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s <= 2])
        hilt = halo & (small_red | (nm == 'outline')) & ~inside
        # outline pixels only count as hilt if they touch steel or a small red (wrap) pixel
        hilt &= ndimage.binary_dilation(steel | small_red, P2.N8)
        pink = (M == 'pink') | ((nm == 'skin_2') & ndimage.binary_dilation(M == 'pink', P2.N8, iterations=1))
        fx = np.zeros_like(a)
        keep = (steel | hilt) & ~inside
        fx[keep] = a[keep]
        fxp = np.zeros_like(a)
        fxp[pink & ~inside] = a[pink & ~inside]
        Image.fromarray(stamp).save(f'{W}/{name}_stamp.png')
        Image.fromarray(fx).save(f'{W}/{name}_fx.png')
        Image.fromarray(fxp).save(f'{W}/{name}_pink.png')
        body = a.copy(); body[inside | keep] = 0
        Image.fromarray(body).save(f'{W}/{name}_ref.png')
        info[name] = {'stamp': [int(x0), int(y0)], 'size': [int(sw), int(sh_)]}
        print(name, info[name])
    old = json.load(open(W + '/layers.json')) if os.path.exists(W + '/layers.json') else {}
    old.update(info)
    json.dump(old, open(W + '/layers.json', 'w'), indent=1)


def parse(name, _depth=0):
    """-> (names array 128x128 '' = empty, opts)"""
    lines = open(f'{SRC}/{name}.txt').read().splitlines()
    nm = np.full((128, 128), '', dtype=object)
    opts = {'under': [], 'pink': False, 'drop_fx': [], 'kats': [], 'fx': True}
    top = np.full((128, 128), '', dtype=object)
    i = 0
    org = (0, 0)
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln or ln.lstrip().startswith('#'):
            i += 1; continue
        if ln.startswith('origin:'):
            org = tuple(map(int, ln.split()[1:3]))
        elif ln.startswith('from:'):
            parts = ln.split()
            nm, o2, top = parse(parts[1], _depth + 1)
            opts.update({k: v for k, v in o2.items() if k not in ('under', 'drop_fx', 'kats', 'ops', 'opsb', 'stamp_at', 'bow')})
            top = np.full_like(top, '') if len(parts) >= 4 else top
            if len(parts) >= 4:
                dx, dy = int(parts[2]), int(parts[3])
                nm = np.roll(np.roll(nm, dy, 0), dx, 1); top = np.roll(np.roll(top, dy, 0), dx, 1)
        elif ln.strip() == 'mirror':
            cx = opts.get('mirror_cx2', 127)   # mirror about x = cx2/2
            m2 = np.full_like(nm, '')
            relight = {'red_1': 'red_2', 'red_3': 'red_2', 'skin_0': 'skin_1'}   # light stays top-left: drop mirrored edge tones, autoshade re-applies
            for y, x in zip(*np.nonzero(nm != '')):
                xx = cx - x
                if 0 <= xx < 128: m2[y, xx] = relight.get(nm[y, x], nm[y, x])
            nm = m2
            top = np.full_like(top, '')
        elif ln.startswith('mirror_cx2:'):
            opts['mirror_cx2'] = int(ln.split()[1])
        elif ln.startswith('under:'):
            opts['under'].append(tuple(map(int, ln.split()[1].split(','))))
        elif ln.startswith('drop_fx:'):
            opts['drop_fx'].append(tuple(map(int, ln.split()[1].split(','))))
        elif ln.startswith('opb:'):
            opts.setdefault('opsb', []).append(ln[4:].strip())
        elif ln.startswith('op:'):
            opts.setdefault('ops', []).append(ln[3:].strip())
        elif ln.startswith('kat:'):
            p_ = ln.split(); opts['kats'].append((p_[1], int(p_[2]), int(p_[3]), 'm' in p_[4:], 'under' in p_[4:]))
        elif ln.startswith('fx:'):
            opts['fx'] = ln.split()[1] != 'none'
        elif ln.startswith('pink:'):
            opts['pink'] = ln.split()[1] == 'keep'
        elif ln.startswith('move:'):
            p_ = ln.split(); x0, y0, x1, y1 = map(int, p_[1].split(',')); dx, dy = map(int, p_[2].split(','))
            box = nm[y0:y1 + 1, x0:x1 + 1].copy(); nm[y0:y1 + 1, x0:x1 + 1] = ''
            for yy in range(box.shape[0]):
                for xx in range(box.shape[1]):
                    if box[yy, xx] and 0 <= y0 + yy + dy < 128 and 0 <= x0 + xx + dx < 128:
                        nm[y0 + yy + dy, x0 + xx + dx] = box[yy, xx]
        elif ln.startswith('shear:'):
            # shear: y0 y1 dx  -> rows y0..y1 shifted by round(dx * (y1 - y) / (y1 - y0)) (lean: top moves dx, bottom stays)
            p_ = ln.split(); y0, y1, dx = int(p_[1]), int(p_[2]), int(p_[3])
            for y in range(y0, y1 + 1):
                sx = int(round(dx * (y1 - y) / max(1, y1 - y0)))
                if sx: nm[y] = np.roll(nm[y], sx); 
        elif ln.startswith('clear:'):
            x0, y0, x1, y1 = map(int, ln.split()[1].split(','))
            nm[y0:y1 + 1, x0:x1 + 1] = ''
        elif ln.startswith('limb:'):
            # limb: TONECHAR W x0,y0 x1,y1 ... [behind]  -> W px wide polyline + its own 1 px outline
            p_ = ln.split()
            tone = CH2N[p_[1]]; w = int(p_[2]); behind = 'behind' in p_
            pts = [tuple(map(int, q.split(','))) for q in p_[3:] if ',' in q]
            px = []
            for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
                n = max(abs(bx - ax), abs(by - ay), 1)
                for t in range(n + 1):
                    px.append((int(round(ax + (bx - ax) * t / n)), int(round(ay + (by - ay) * t / n))))
            mask = np.zeros((128, 128), bool)
            for (x, y) in px:
                for k in range(w):
                    xx = x + k - (w - 1) // 2
                    if 0 <= xx < 128 and 0 <= y < 128: mask[y, xx] = True
            ring = ndimage.binary_dilation(mask, P2.N4) & ~mask
            if behind:
                mask &= (nm == ''); ring &= (nm == '')
            else:
                ring &= (nm == '')
            nm[mask] = tone; nm[ring] = 'outline'
        elif ln.startswith('sword:'):
            p_ = ln.split(); opts['sword'] = dict(hand=list(map(int, p_[1].split(','))), tip=list(map(int, p_[2].split(','))))
            for q in p_[3:]:
                k_, v_ = q.split('='); opts['sword'][k_] = int(v_) if k_ != 'behind' else bool(int(v_))
        elif ln.startswith('expr:'):
            opts['expr'] = ln.split()[1]
        elif ln.startswith('stamp:'):
            opts['stamp_at'] = tuple(map(int, ln.split()[1:3]))
        elif ln.startswith('bow:'):
            opts['bow'] = tuple(map(int, ln.split()[1:3]))
        elif ln.startswith('shade:'):
            opts['shade'] = ln.split()[1] != 'off'
        elif ln.startswith('halfgrid:'):
            i += 1; r = 0
            while i < len(lines) and lines[i] and not lines[i].split()[0].endswith(':'):
                row = lines[i].split('|')[0].rstrip()
                if row.startswith('#'):
                    i += 1; continue
                row = row + row[::-1]
                for c, ch in enumerate(row):
                    x, y = org[0] + c, org[1] + r
                    if 0 <= x < 128 and 0 <= y < 128 and ch not in '._ ':
                        nm[y, x] = CH2N[ch]
                r += 1; i += 1
            continue
        elif ln.startswith('grid:') or ln.startswith('patch:') or ln.startswith('top:'):
            tgt = nm
            if ln.startswith('patch:') or ln.startswith('top:'):
                org = tuple(map(int, ln.split()[1:3]))
                keep = True
                if ln.startswith('top:'): tgt = top
            else:
                keep = False
            i += 1
            r = 0
            while i < len(lines) and lines[i] and not lines[i].split()[0].endswith(':') and lines[i].strip() not in ('mirror',):
                row = lines[i].split('|')[0].rstrip()
                if row.startswith('#'):
                    i += 1; continue
                for c, ch in enumerate(row):
                    x, y = org[0] + c, org[1] + r
                    if not (0 <= x < 128 and 0 <= y < 128): continue
                    if ch == '_' or (ch == ' '):
                        continue
                    if ch == '.':
                        if keep: tgt[y, x] = ''
                        continue
                    tgt[y, x] = CH2N[ch]
                r += 1
                i += 1
            continue
        i += 1
    return nm, opts, top


BOWCEL = {'S': ('bow_S', 3, False), 'SE': ('bow_SE', 8, False), 'E': ('bow_E', 5, False), 'N': ('bow_N', 1, False),
          'SW': ('bow_SE', 5, True), 'W': ('bow_E', 9, True)}


def bow_lag(st, d, dx, dy):
    """secondary motion: offset the locked bow cel (dx, dy) against the head; uncovered old bow pixels become
    bun hair (hair_0) where they touch hair, else transparent.  Head canvas grows 2 px up so dy<0 is not clipped."""
    name, cx, mir = BOWCEL[d]
    c = np.array(Image.open(f'{R}/hybrid/lock/pixel/{name}.png').convert('RGBA'))
    if mir: c = c[:, ::-1]
    pad = 2
    H_, W_ = st.shape[:2]
    big = np.zeros((H_ + pad, W_, 4), np.uint8); big[pad:] = st
    ch, cw = c.shape[:2]
    cm = c[..., 3] > 0
    # remove the original bow (red / outline pixels of the cel) but keep its hair rows
    nmc = P2.to_names(c)
    bowpx = cm & np.vectorize(lambda t: P2.mat(t) in ('red', 'outline'), otypes=[bool])(nmc)
    reg = big[pad:pad + ch, cx:cx + cw]
    hairm = np.vectorize(lambda t: P2.mat(t) == 'hair', otypes=[bool])(P2.to_names(reg))
    for y, x in zip(*np.nonzero(bowpx)):
        nb = [hairm[yy, xx] for yy, xx in ((y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= yy < ch and 0 <= xx < cw]
        reg[y, x] = P2.rgba('hair_0') if (any(nb) and y >= 6) else 0
    oy, ox = pad + dy, cx + dx
    for y, x in zip(*np.nonzero(cm)):
        if nmc[y, x] and P2.mat(nmc[y, x]) == 'hair' and big[oy + y, ox + x, 3]:
            continue
        big[oy + y, ox + x] = c[y, x]
    return big


def autoshade(nm):
    """one light rule for every hand cel (key light top-left): base red_2 / skin_1 pixels on the right or bottom
    edge of their mass get the shadow tone; leather_1 top edge -> leather_2.  Hand-typed tones are kept."""
    nm = nm.copy()
    M = np.vectorize(P2.mat, otypes=[object])(nm)
    red = M == 'red'; skin = M == 'skin'; lea = (nm == 'leather_1') | (nm == 'leather_2')
    R2 = nm == 'red_2'
    edge_r = R2 & (~P2.sh(red, 0, 1) | ~P2.sh(red, 1, 0))
    nm[edge_r] = 'red_1'
    S1 = nm == 'skin_1'
    wide = S1 & P2.sh(skin, 0, -1)
    nm[wide & ~P2.sh(skin, 0, 1)] = 'skin_0'
    L1 = nm == 'leather_1'
    nm[L1 & ~P2.sh(lea, -1, 0) & ~P2.sh(M == 'steel', -1, 0)] = 'leather_2'
    return nm


def compose(names):
    os.makedirs(OUT, exist_ok=True)
    for name in names:
        if not os.path.exists(f'{SRC}/{name}.txt'):
            print('skip (no body src)', name); continue
        nm, opts, top = parse(name)
        if opts.get('shade', True):
            nm = autoshade(nm)
        body = P2.from_names(nm)
        for kn, kx, ky, km, ku in opts['kats']:
            k = np.array(Image.open(f'{R}/hybrid/lock/pixel/{kn}.png').convert('RGBA'))
            if km: k = k[:, ::-1]
            hh, ww = k.shape[:2]
            for yy in range(hh):
                for xx in range(ww):
                    if k[yy, xx, 3] and 0 <= ky + yy < 128 and 0 <= kx + xx < 128:
                        if ku and body[ky + yy, kx + xx, 3]: continue
                        body[ky + yy, kx + xx] = k[yy, xx]
        tp = P2.from_names(top); m = tp[..., 3] > 0; body[m] = tp[m]
        fx = np.array(Image.open(f'{W}/{name}_fx.png'))
        if not opts['fx']: fx[:] = 0
        if opts['pink']:
            pk = np.array(Image.open(f'{W}/{name}_pink.png'))
            m = pk[..., 3] > 0
            fx[m] = pk[m]
        for x0, y0, x1, y1 in opts['drop_fx']:
            fx[y0:y1 + 1, x0:x1 + 1] = 0
        stamp = np.array(Image.open(f'{W}/{name}_stamp.png'))
        d = name.split('_')[1]
        if 'stamp_at' in opts or 'bow' in opts:
            sx, sy = opts.get('stamp_at', tuple(json.load(open(W + '/layers.json'))[name]['stamp']))
            st = np.array(Image.open(f'{R}/hybrid/lock/pixel/head_{d}.png').convert('RGBA'))
            if 'expr' in opts:
                import polish as P1
                st = st.copy()
                for (r_, c_, t_) in P1.EXPR.get((d, opts['expr']), []):
                    st[r_, c_] = P2.rgba(t_)
            if 'bow' in opts:
                st = bow_lag(st, d, *opts['bow'])
            stamp = np.zeros_like(stamp)
            if 'bow' in opts: sy -= 2
            hh, ww = st.shape[:2]
            for yy in range(hh):
                for xx in range(ww):
                    if st[yy, xx, 3] and 0 <= sy + yy < 128 and 0 <= sx + xx < 128:
                        stamp[sy + yy, sx + xx] = st[yy, xx]
        under = np.zeros((128, 128), bool)
        for x0, y0, x1, y1 in opts['under']:
            under[y0:y1 + 1, x0:x1 + 1] = True
        out = np.zeros_like(body)
        fu = (fx[..., 3] > 0) & under
        out[fu] = fx[fu]
        m = body[..., 3] > 0; out[m] = body[m]
        m = stamp[..., 3] > 0; out[m] = stamp[m]
        fo = (fx[..., 3] > 0) & ~under
        out[fo] = fx[fo]
        if opts.get('sword'):
            import polish as P1
            inside = stamp[..., 3] > 0
            out = P1.redraw_katana(out, opts['sword'], inside, name)
        Image.fromarray(out).save(f'{OUT}/{name}.png')
        if opts.get('ops'):
            import subprocess
            r = subprocess.run([R + '/.venv/bin/python', R + '/tools/hybrid/draw.py', f'{OUT}/{name}.png', '--out', f'{OUT}/{name}.png'] + opts['ops'], capture_output=True, text=True)
            if r.returncode: print(name, 'draw FAIL', r.stderr[-800:])
            out = np.array(Image.open(f'{OUT}/{name}.png').convert('RGBA'))
        if opts.get('opsb'):
            import subprocess
            tmp = f'{W}/{name}_behind.png'
            Image.fromarray(np.zeros_like(out)).save(tmp)
            r = subprocess.run([R + '/.venv/bin/python', R + '/tools/hybrid/draw.py', tmp, '--out', tmp] + opts['opsb'], capture_output=True, text=True)
            if r.returncode: print(name, 'draw-behind FAIL', r.stderr[-800:])
            bh = np.array(Image.open(tmp).convert('RGBA'))
            m = (bh[..., 3] > 0) & (out[..., 3] == 0)
            out[m] = bh[m]
            Image.fromarray(out).save(f'{OUT}/{name}.png')
        Image.fromarray(out).resize((512, 512), Image.NEAREST).save(f'{OUT}/{name}_4x.png')
        hs = f'{B}/sprite/{name}_hires.png'
        if os.path.exists(hs) and not os.path.exists(f'{OUT}/{name}_hires.png'):
            Image.open(hs).save(f'{OUT}/{name}_hires.png')
        print('composed', name)


def grid_txt(name, x0, y0, x1, y1, which='ref'):
    a = np.array(Image.open(f'{W}/{name}_{which}.png').convert('RGBA'))
    nm = P2.to_names(a)
    rows = []
    for y in range(y0, y1 + 1):
        rows.append(''.join(N2CH.get(nm[y, x], '.') if nm[y, x] else '.' for x in range(x0, x1 + 1)))
    return rows


if __name__ == '__main__':
    cmd = sys.argv[1]; names = sys.argv[2:] or NAMES
    if cmd == 'layers': layers(names)
    elif cmd == 'compose': compose(names)
    elif cmd == 'ref':
        n = names[0]; x0, y0, x1, y1 = map(int, names[1:5]); which = names[5] if len(names) > 5 else 'ref'
        print('origin: %d %d' % (x0, y0))
        print('    ' + ''.join(str((x // 10) % 10) for x in range(x0, x1 + 1)))
        print('    ' + ''.join(str(x % 10) for x in range(x0, x1 + 1)))
        for j, r in enumerate(grid_txt(n, x0, y0, x1, y1, which)):
            print('%3d ' % (y0 + j) + r)
