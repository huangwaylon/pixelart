"""S1 r1 POLISH pass (Claude hand pixel artist; scripted exact pixels, every rule with a reason).

in : hybrid/S1_redraw/r1/sprite/<name>.png   (pre-polish set, never modified)
out: hybrid/S1_redraw/r1/polished/<name>.png (+ _4x, _hires copy of the source)

Stage A  RE-CEL (whole set, one rule set => same light / outline treatment in every frame):
  1. locate the locked head stamp (exact-match search) and protect it byte-for-byte
  2. protect katana (steel + hilt pixels next to steel), smears / ribbons (pink, ribbon skin_2)
  3. material specks (1-2 px islands of a material inside another) -> surrounding material
     (reason: render-noise, cleanup guide R4/R12)
  4. re-tone each material as flat 2-tone cels, key light top-left:
       red   : base red_2, shadow red_1 on the bottom 2 px / right 1 px of every mass and under the
               corset (cast), red_3 only on top-left corners of big masses, red_0 fold lines kept
       skin  : base skin_1, skin_0 on the right edge of limbs >= 2 px wide
       leather: leather_1, leather_2 top edge (palette note: corset top edge)
       dark  : dark_1 / outline kept, specks merged
  5. exterior outline: every body pixel touching transparency gets a 1 px outline (sel-out on the lit
     top/left uses the material's dark tone); fixes stick arms / open hems / weak outlines
  6. orphan merge
Stage B  per-frame hand ops (tools/hybrid/draw.py ops in polish2_ops.json, each with a reason)
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
from scipy import ndimage

R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
B = R + '/hybrid/S1_redraw/r1'
OUT = os.environ.get('P2OUT', B + '/polished')
PAL = json.load(open(R + '/docs/palette.json'))
NAME2HEX = {'outline': PAL['outline']}
for ramp, cs in PAL['ramps'].items():
    for i, c in enumerate(cs):
        NAME2HEX.setdefault(f'{ramp}_{i}', c)
HEX2NAME = {}
for n, h in NAME2HEX.items():
    HEX2NAME.setdefault(h.lower(), n)
# leather_0 / dark_0 == outline hex -> 'outline' (set first above)
HEX2NAME[PAL['outline'].lower()] = 'outline'
NAMES = sorted(set(HEX2NAME.values()))
N8 = np.ones((3, 3), bool)
N4 = ndimage.generate_binary_structure(2, 1)


def rgba(n):
    h = NAME2HEX[n]
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255], np.uint8)


def to_names(a):
    out = np.full(a.shape[:2], '', dtype=object)
    ys, xs = np.nonzero(a[..., 3] > 0)
    for y, x in zip(ys, xs):
        out[y, x] = HEX2NAME['#%02x%02x%02x' % tuple(a[y, x, :3])]
    return out


def from_names(nm):
    a = np.zeros(nm.shape + (4,), np.uint8)
    for y, x in zip(*np.nonzero(nm != '')):
        a[y, x] = rgba(nm[y, x])
    return a


def mat(n):
    if not n: return ''
    return 'outline' if n == 'outline' else n.rsplit('_', 1)[0]


def sh(m, dy, dx):
    """value of m at (y+dy, x+dx), False outside"""
    o = np.zeros_like(m)
    H, W = m.shape
    ys0, ys1 = max(0, -dy), min(H, H - dy)
    xs0, xs1 = max(0, -dx), min(W, W - dx)
    o[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return o


def find_stamp(a, d):
    st = np.array(Image.open(f'{R}/hybrid/lock/pixel/head_{d}.png').convert('RGBA'))
    sm = st[..., 3] > 0
    shh, sw = sm.shape
    best = (-1, 0, 0)
    for y0 in range(0, 128 - shh):
        for x0 in range(0, 128 - sw):
            win = a[y0:y0 + shh, x0:x0 + sw]
            eq = (np.all(win[..., :3] == st[..., :3], -1) & (win[..., 3] > 0) & sm).sum()
            if eq > best[0]: best = (eq, x0, y0)
    eq, x0, y0 = best
    inside = np.zeros((128, 128), bool)
    inside[y0:y0 + shh, x0:x0 + sw] = sm
    # pixels that differ from the stamp (expression patch) are still protected
    return inside, (x0, y0), eq / sm.sum()


def recel(a, d, cfg):
    nm = to_names(a)
    op = nm != ''
    inside, org, match = find_stamp(a, d)
    M = np.vectorize(mat, otypes=[object])(nm)
    steel = M == 'steel'
    pink = M == 'pink'
    # ribbon skin_2: skin_2 8-connected to pink (scarf lit edge per palette roles)
    s2 = nm == 'skin_2'
    lab, n = ndimage.label(s2 | pink, structure=N8)
    rib_ids = set(np.unique(lab[pink]).tolist()) - {0}
    ribbon = np.isin(lab, list(rib_ids)) & (s2 | pink)
    # hilt: small red/outline pixels hugging steel (the hand katana); protect a 2 px halo around steel
    # only for tiny red components (wrap diamonds), not dress masses
    halo = ndimage.binary_dilation(steel, N8, iterations=cfg.get('hilt_halo', 2))
    redm = M == 'red'
    lab, n = ndimage.label(redm, structure=N4)
    sz = ndimage.sum(redm, lab, range(1, n + 1))
    small_red = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s <= 3])
    hilt = halo & (small_red | (nm == 'outline')) & ~inside
    for bx0, by0, bx1, by1 in cfg.get('protect', []):
        hilt[by0:by1 + 1, bx0:bx1 + 1] |= op[by0:by1 + 1, bx0:bx1 + 1]
    prot = inside | steel | ribbon | hilt | (M == 'eye') | (M == 'purple')
    body = op & ~prot
    # --- 3. material specks
    for _ in range(2):
        for m in ('red', 'skin', 'leather', 'dark', 'hair'):
            mm = (M == m) & body
            lab, n = ndimage.label(mm, structure=N4)
            for i in range(1, n + 1):
                cm = lab == i
                if cm.sum() > 2: continue
                ring = ndimage.binary_dilation(cm, N4) & ~cm & body
                nb = [x for x in M[ring].tolist() if x and x != m]
                if len(nb) >= 3 and len(nb) >= ring.sum() * 0.75:
                    v = max(set(nb), key=nb.count)
                    if v == 'outline': continue
                    M[cm] = v
                    # tone placeholder; re-tone below sets it
                    nm[cm] = {'red': 'red_2', 'skin': 'skin_1', 'leather': 'leather_1', 'dark': 'dark_1',
                              'hair': 'hair_1', 'pink': 'pink_1'}.get(v, nm[cm][0])
    # interior outline specks (1-2 px dark dots inside a mass = render noise, R4)
    ol = (nm == 'outline') & body
    lab, n = ndimage.label(ol, structure=N8)
    for i in range(1, n + 1):
        cm = lab == i
        if cm.sum() > 2: continue
        ring = ndimage.binary_dilation(cm, N8) & ~cm
        nb = [x for x in M[ring].tolist()]
        if '' in nb or 'outline' in nb: continue
        v = max(set(nb), key=nb.count)
        M[cm] = v; nm[cm] = {'red': 'red_2', 'skin': 'skin_1', 'leather': 'leather_1', 'dark': 'dark_1', 'hair': 'hair_1'}.get(v, 'outline')
    # --- 4. re-tone
    R_ = (M == 'red') & body
    fold = (nm == 'red_0') & R_
    lab, n = ndimage.label(fold, structure=N8)
    keepfold = np.zeros_like(fold)
    for i in range(1, n + 1):
        cm = lab == i
        if cm.sum() >= 3: keepfold |= cm
    Rmass = R_ & ~keepfold
    leather = (M == 'leather') & body
    newn = nm.copy()
    newn[Rmass] = 'red_2'
    shadow = Rmass & (~sh(Rmass, 2, 0) | ~sh(Rmass, 1, 0) | ~sh(Rmass, 0, 1))
    under_corset = Rmass & (sh(leather, -1, 0) | sh(leather, -2, 0))
    newn[shadow | under_corset] = 'red_1'
    # deep underside: bottom row of skirt masses where below is transparent and above-left also red_1
    lab, n = ndimage.label(Rmass, structure=N4)
    sz = ndimage.sum(Rmass, lab, range(1, n + 1))
    big = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s >= 20])
    corner = Rmass & big & ~sh(Rmass, -1, 0) & ~sh(Rmass, 0, -1) & sh(Rmass, 1, 0) & sh(Rmass, 0, 1) & sh(Rmass, 1, 1)
    if cfg.get('red3', False): newn[corner & ~shadow] = 'red_3'
    newn[keepfold] = 'red_0'
    # skin
    S_ = (M == 'skin') & body
    newn[S_] = 'skin_1'
    wide = S_ & sh(S_, 0, -1)          # has skin on its left => limb >= 2 px wide here
    newn[wide & ~sh(S_, 0, 1)] = 'skin_0'
    # leather
    newn[leather & (nm != 'outline')] = 'leather_1'
    newn[leather & ~sh(leather, -1, 0) & sh(leather, 1, 0)] = 'leather_2'
    # hair strands outside the stamp: 2 tones only
    Hh = (M == 'hair') & body
    newn[Hh & (nm == 'hair_2')] = 'hair_1'
    nm = newn
    # --- 5. exterior outline
    op = nm != ''
    bodyop = op & ~ribbon & ~steel & ~(M == 'pink') & ~inside & (nm != 'outline')
    if cfg.get('outline', True):
        need = ~op & ndimage.binary_dilation(bodyop, N4)
        noline = np.zeros_like(need)
        for bx0, by0, bx1, by1 in cfg.get('no_outline', []):
            noline[by0:by1 + 1, bx0:bx1 + 1] = True
        need &= ~noline
        dark = {'red': 'red_0', 'skin': 'skin_0', 'hair': 'hair_0', 'leather': 'outline', 'dark': 'outline'}
        for y, x in zip(*np.nonzero(need)):
            # sel-out: lit side = pixel ABOVE or LEFT of a body pixel (light from top-left), and not the ground row
            src_below = y + 1 < 128 and bodyop[y + 1, x]
            src_right = x + 1 < 128 and bodyop[y, x + 1]
            if (src_below or src_right) and not (y + 1 < 128 and x - 1 >= 0 and bodyop[y, x - 1]) and y < 100:
                m = mat(nm[y + 1, x] if src_below else nm[y, x + 1])
                nm[y, x] = dark.get(m, 'outline') if cfg.get('selout', False) else 'outline'
            else:
                nm[y, x] = 'outline'
    # --- 6. orphans: single pixels whose 8 neighbours share no tone with them -> majority neighbour
    for _ in range(2):
        op = nm != ''
        for y, x in zip(*np.nonzero(op & ~prot)):
            t = nm[y, x]
            if t == 'outline': continue
            nb = [nm[yy, xx] for yy in range(y - 1, y + 2) for xx in range(x - 1, x + 2)
                  if (yy, xx) != (y, x) and 0 <= yy < 128 and 0 <= xx < 128]
            if t in nb: continue
            same_m = [v for v in nb if mat(v) == mat(t)]
            cand = [v for v in nb if v and v != 'outline' and not prot[y, x]]
            if same_m:
                nm[y, x] = max(set(same_m), key=same_m.count)
            elif cand and len([v for v in nb if v]) >= 6:
                nm[y, x] = max(set(cand), key=cand.count)
    return from_names(nm), org, match


def main(only):
    os.makedirs(OUT, exist_ok=True)
    ops_all = json.load(open(R + '/tools/hybrid/s1/polish2_ops.json')) if os.path.exists(R + '/tools/hybrid/s1/polish2_ops.json') else {}
    names = [f'turn_{d}' for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']] + [f'walk_SE_k{i}' for i in range(4)] + \
            [f'slash_SE_k{i}' for i in range(4)] + [f'jump_E_{k}' for k in ['crouch', 'apex', 'land']]
    for name in names:
        if only and name not in only: continue
        cfg = ops_all.get(name, {})
        src = cfg.get('src', f'{B}/sprite/{name}.png')
        a = np.array(Image.open(src).convert('RGBA'))
        d = name.split('_')[1]
        pre = cfg.get('pre_ops', [])
        out = f'{OUT}/{name}.png'
        if pre:
            Image.fromarray(a).save(out)
            r = subprocess.run([R + '/.venv/bin/python', R + '/tools/hybrid/draw.py', out, '--out', out] + [o for o in pre if not o.startswith('#')], capture_output=True, text=True)
            if r.returncode: print(name, 'pre FAIL', r.stderr[-600:])
            a = np.array(Image.open(out).convert('RGBA'))
        if cfg.get('recel', True):
            a, org, match = recel(a, d, cfg)
        else:
            org, match = None, None
        Image.fromarray(a).save(out)
        ops = [o for o in cfg.get('ops', []) if not o.lstrip().startswith('#')]
        if ops:
            r = subprocess.run([R + '/.venv/bin/python', R + '/tools/hybrid/draw.py', out, '--out', out] + ops, capture_output=True, text=True)
            if r.returncode: print(name, 'draw FAIL', r.stderr[-600:])
        im = Image.open(out)
        im.resize((512, 512), Image.NEAREST).save(f'{OUT}/{name}_4x.png')
        hs = f'{B}/sprite/{name}_hires.png'
        if os.path.exists(hs):
            Image.open(hs).save(f'{OUT}/{name}_hires.png')
        print(name, 'stamp', org, 'match %.2f' % match if match else '')


if __name__ == '__main__':
    main(sys.argv[1:])
