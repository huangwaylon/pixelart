#!/usr/bin/env python3
"""post.py: continuity pass + FX + outputs for the animate pilot.
  post.py clean S ACT        continuity pass on work/S/ACT_SE/fNN.txt -> cNN.txt (+ report)
  post.py out   S ACT        FX composite -> gifs/ACT_SE_S.gif, strips/ACT_SE_S{,_body}.png
  post.py sheet ACT          A vs B comparison sheet -> gifs/ACT_SE_AvsB.png
  post.py colors S ACT       clip colour-consistency / flicker report -> <workdir>/colors.txt + colors.json (exit 1 if flags)
  options: --sole Y (master sole row, 61) --cell W H (64 64) --fx-pivot-y Y (manifest feet pivot, 62) --fx-dy N (override)
  colour options: --palette P.json (locked palette; enables 'colors' and runs it at the end of 'clean'; default for
    'colors' = v2/style/pk_palette.json) --master M.txt (MAT ramp-swap lint in clean) --stamp S.txt (fallback stamp when
    frames.json has none) --dir WORKDIR (any frame dir with frames.json, e.g. an ff_redraw dir; default work/S/ACT_SE)
    --pre c|f (frame prefix for colors, default c then f) --head-px N (3) --hist T (0.2) --region-px N (4) --shape T (0.25)
  colors: head stamp window aligned on each frame's head anchor (stamp face match): per-frame drift vs its expression stamp,
    consecutive recolours beyond the expression delta (stamp_i vs stamp_j); obi / bootL / bootR regions (material comps,
    boots = bottom 10 rows above the lowest row): histogram L1 + per-pixel change (bbox-aligned) unless the region's size
    changes >shape (pose reason); new colours in a region; transient colours (only in one frame); off-palette pixels.
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
V2 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2'
sys.path.insert(0, V2 + '/anim_cut/tools'); sys.path.insert(0, V2 + '/fx/tools')
import lint_style as LS, fxlib as FX
AN = V2 + '/animate'; W = AN + '/work'
RGB = {k: tuple(int(v[0][j:j + 2], 16) for j in (1, 3, 5)) for k, v in LS.PAL.items()}
BG = (0x6e, 0x6e, 0x6e); PAD = 8
MF = json.load(open(V2 + '/fx/manifest.json'))['effects']
# Ground rows. FX manifest: 64x64 C_r3 cell, nominal 'feet pivot (32,62)' = the ground line one row BELOW the soles;
# its ground effects use ground_y / cell_offset y = 61 = the C_r3 back-shoe sole row. Harness/master: SOLE = lowest
# feet row (pivot y, 61). FX_DY = SOLE - (FXPIV_Y - 1) is added to every manifest cell_offset / ground anchor, so with the
# defaults (62, 61) FX_DY = 0 (the old behaviour). New masters (v2/prop/): --sole Y --cell W H [--fx-pivot-y Y] [--fx-dy N].
FXPIV_Y = 62  # fx manifest nominal feet pivot row
CW, CH = 64, 64  # master cell
SOLE = 61  # master/harness sole row
FX_DY = None  # None = SOLE - (FXPIV_Y - 1)


def fx_dy(): return SOLE - (FXPIV_Y - 1) if FX_DY is None else FX_DY
def fx_dx(): return CW // 2 - 32  # manifest cell is 64 wide, feet centre x 32
def fx_anchor(name):
    """manifest cell_offset of an effect moved into our cell (x: feet centre, y: sole row)."""
    x, y = MF[name]['cell_offset']; return (x + fx_dx(), y + fx_dy())
def ground_y(): return FXPIV_Y - 1 + fx_dy()  # row where ground effects' pivots go (= SOLE by default)


WDIR = None  # --dir override
PALP = None; MASTER = None; STAMP = None; COLOPT = {}


def wdir(S, act): return WDIR or '%s/%s/%s_SE' % (W, S, act)
def arr(g): return np.array([list(r) for r in g])
def grid(a): return [''.join(r) for r in a]
def fj_of(S, act): return json.load(open(wdir(S, act) + '/frames.json'))


def load(S, act, pre='f'):
    fj = fj_of(S, act); out = []
    for f in fj['frames']:
        p = '%s/%s%02d.txt' % (wdir(S, act), pre, f['i'])
        if not os.path.exists(p): p = '%s/f%02d.txt' % (wdir(S, act), f['i'])
        g, meta = LS.read(p); g = [r[:CW].ljust(CW, '.') for r in g[:CH]] + ['.' * CW] * max(0, CH - len(g))
        out.append((g, meta))
    return fj, out


def write(p, g, meta):
    open(p, 'w').write(''.join('; %s\n' % m for m in meta) + '\n'.join(g) + '\n')


# ---------------- continuity ----------------
def restamp(a, st):
    """re-paste the expression stamp exactly at its matched offset (kills head boiling)."""
    face, _ = LS.stamp_info(st)
    if face: m, n, ox, oy = LS.find_stamp(grid(a), st, face)
    else:  # closed-eye stamp (joy/blink): match all its pixels (used to crash)
        import colorcheck as CC; m, n, ox, oy = CC.anchor(grid(a), st)
    if m < n * 0.8: return 0, (ox, oy)
    c = 0
    for y, r in enumerate(st):
        for x, ch in enumerate(r):
            if ch == '.': continue
            X, Y = x + ox, y + oy
            if 0 <= X < CW and 0 <= Y < CH and a[Y, X] != ch and a[Y, X] not in 'nkEeRr':  # never paint over blade/sleeves
                a[Y, X] = ch; c += 1
    return c, (ox, oy)


def deboil(fr, loop):
    """one-frame blips: pixel differs from both neighbours while the neighbours agree on a 5x5 window."""
    n = len(fr); out = [f.copy() for f in fr]; c = 0
    for i in range(n):
        if not loop and i in (0, n - 1): continue
        a, b = fr[(i - 1) % n], fr[(i + 1) % n]; cur = fr[i]
        same = (a == b)
        diff = np.argwhere((cur != a) & same)
        for y, x in diff:
            y0, y1, x0, x1 = max(0, y - 2), min(CH, y + 3), max(0, x - 2), min(CW, x + 3)
            if same[y0:y1, x0:x1].all() and (cur[y0:y1, x0:x1] != a[y0:y1, x0:x1]).sum() <= 3:
                out[i][y, x] = a[y, x]; c += 1
    return out, c


def clean(S, act):
    fj, fr = load(S, act); loop = act != 'slash'; rep = []
    A = [arr(g) for g, _ in fr]; offs = []
    for i, f in enumerate(fj['frames']):
        st = LS.read(f['stamp'])[0]; c, o = restamp(A[i], st); offs.append(o); rep.append('f%02d restamp %d px at %s' % (i, c, o))
    # head x/y jitter of 1px between frames whose guide head didn't move -> snap
    B, c = deboil(A, loop); rep.append('deboil %d px' % c)
    nfix = 0
    for i, f in enumerate(fj['frames']):
        meta = fr[i][1]; st = LS.read(f['stamp'])[0]
        g0 = grid(A[i]); g1 = grid(B[i])
        pk = dict(palette=PALP, master=LS.read(MASTER)[0] if MASTER else None) if PALP else {}
        l0 = LS.lint(g0, meta, st, tuple(fj['pivot']), **pk); l1 = LS.lint(g1, meta, st, tuple(fj['pivot']), **pk)
        g = g1 if len(l1) <= len(l0) else g0
        lf = l1 if g is g1 else l0
        write('%s/c%02d.txt' % (wdir(S, act), i), g, ['%s' % m if isinstance(m, str) else m for m in meta_lines(meta)])
        if lf: nfix += 1; rep.append('f%02d lint: %s' % (i, '; '.join(x[:70] for x in lf)))
    # diff report
    for i in range(len(B)):
        j = (i + 1) % len(B)
        if not loop and j == 0: break
        rep.append('d%02d-%02d %d px changed' % (i, j, (B[i] != B[j]).sum()))
    open(wdir(S, act) + '/clean.txt', 'w').write('\n'.join(rep) + '\n'); print('\n'.join(rep))
    if PALP: colors(S, act, 'c')


# ---------------- colour consistency ----------------
def colors(S, act, pre=None):
    """per-clip colour report (colorcheck.clip_report) on cNN (else fNN) frames -> colors.txt / colors.json."""
    import colorcheck as CC
    pal = CC.load(PALP or LS.PAL_PATH); fj = fj_of(S, act); d = wdir(S, act)
    pre = pre or ('c' if all(os.path.exists('%s/c%02d.txt' % (d, f['i'])) for f in fj['frames']) else 'f')
    _, fr = load(S, act, pre); G = [g for g, _ in fr]
    sts = [(f.get('stamp') or STAMP) for f in fj['frames']]
    sts = [LS.read(p)[0] for p in sts] if all(sts) else None
    loop = fj.get('loop', act != 'slash')
    txt, data = CC.clip_report(G, pal, sts, [f['key'] for f in fj['frames']], loop, name='%s %s (%sNN)' % (os.path.basename(d), S, pre), **COLOPT)
    if MASTER and sts:  # expression stamps: master face colours only
        mg = LS.read(MASTER)[0]; extra = []
        for p in sorted({f.get('stamp') or STAMP for f in fj['frames']}):
            for x in CC.stamp_check(p, mg, pal): extra.append('stamp %s %s' % (os.path.basename(p), x))
        if extra:
            data['flags'] += extra; txt += 'STAMP FLAGS (%d):\n' % len(extra) + ''.join('- %s\n' % x for x in extra)
    open(d + '/colors.txt', 'w').write(txt); json.dump(data, open(d + '/colors.json', 'w'), indent=1, default=str)
    print(txt, end=''); print('->', d + '/colors.txt')
    return data


def meta_lines(meta):
    if isinstance(meta, dict):
        o = []
        for k, v in meta.items():
            if v is True: o.append(k)
            elif isinstance(v, (list, tuple)): o.append('%s %s' % (k, ' '.join(map(str, v))))
            else: o.append('%s %s' % (k, v))
        return o
    return list(meta or [])


# ---------------- FX ----------------
def body_rgba(g):
    im = Image.new('RGBA', (CW + 2 * PAD, CH + 2 * PAD), (0, 0, 0, 0)); px = im.load()
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c in RGB: px[x + PAD, y + PAD] = RGB[c] + (255,)
    return im


def fxim(name, k):
    return Image.open('%s/fx/%s' % (V2, MF[name]['frames'][k])).convert('RGBA')


def put(canvas, name, k, cell_xy, behind=False):
    """place fx frame k so its pivot sits at cell coords cell_xy."""
    e = MF[name]; im = fxim(name, k); px, py = e['pivot']
    pos = (int(round(cell_xy[0] - px)) + PAD, int(round(cell_xy[1] - py)) + PAD)
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0)); layer.alpha_composite(im, pos) if pos[0] >= 0 and pos[1] >= 0 else layer.paste(im, pos, im)
    if behind:
        out = layer.copy(); out.alpha_composite(canvas); return out
    canvas.alpha_composite(layer); return canvas


def blade(g):
    a = arr(g); n = np.argwhere((a == 'n')); k = np.argwhere(a == 'k')
    if not len(n): return None, None
    hand = k.mean(0) if len(k) else n.mean(0)
    d = ((n - hand) ** 2).sum(1); tip = n[d.argmax()]
    return (float(hand[1]), float(hand[0])), (float(tip[1]), float(tip[0]))


def slash_plan(fr, keys):
    iw, ism, iim = keys.index('windup'), keys.index('smear'), keys.index('impact')
    _, t0 = blade(fr[iw]); h1, t1 = blade(fr[ism]); h2, t2 = blade(fr[iim])
    t0 = t0 or (20, 20); t1 = t1 or t2 or (50, 40); t2 = t2 or t1
    v = np.subtract(t2, t0); best = None
    for name in ('slash_h', 'slash_diag', 'slash_over'):
        e = MF[name]; av = np.subtract(e['arc_end'], e['arc_start'])
        cos = v.dot(av) / (np.linalg.norm(v) * np.linalg.norm(av) + 1e-6)
        # pivot so arc_start ~ windup tip, arc_end ~ impact tip (least squares translate)
        p = np.mean([np.subtract(t0, e['arc_start']), np.subtract(t2, e['arc_end'])], 0)
        err = np.linalg.norm(np.add(p, e['arc_start']) - t0) + np.linalg.norm(np.add(p, e['arc_end']) - t2)
        sc = cos - err / 80.0
        if best is None or sc > best[0]: best = (sc, name, p, cos, err)
    # hit point: impact blade tip pushed 2px along the swing, clamped in cell
    hp = np.clip(np.add(t2, v / (np.linalg.norm(v) + 1e-6) * 2), 6, min(CW, CH) - 7)
    return {'smear': best[1], 'pivot': best[2].round().tolist(), 'cos': round(float(best[3]), 2), 'err': round(float(best[4]), 1),
            'hit': hp.round().tolist(), 'tips': [t0, t1, t2]}


def soles(g, y=None):
    y = SOLE if y is None else y
    xs = [x for x, c in enumerate(g[y]) if c != '.']
    if not xs: return None
    runs, cur = [], [xs[0]]
    for x in xs[1:]:
        if x == cur[-1] + 1: cur.append(x)
        else: runs.append(cur); cur = [x]
    runs.append(cur); return runs


def out(S, act, speed=True):
    fj, fr = load(S, act, 'c'); keys = [f['key'] for f in fj['frames']]; G = [g for g, _ in fr]
    seq = []  # (rgba, ms, label)
    plan = {}
    if act == 'slash':
        plan = slash_plan(G, keys); sm = plan['smear']; pv = plan['pivot']; hit = plan['hit']
        ism, iim, ifo = keys.index('smear'), keys.index('impact'), keys.index('follow')
        for i, f in enumerate(fj['frames']):
            b = body_rgba(G[i])
            if i == ism: seq.append((put(b, sm, 0, pv), f['ms'], 'smear'))
            elif i == iim:
                ms = f['ms']
                c = put(body_rgba(G[i]), sm, 1, pv); c = put(c, 'hit_flash', 0, hit); seq.append((c, 40, 'impact+flash'))
                c = put(body_rgba(G[i]), sm, 2, pv); c = put(c, 'hit_spark', 0, hit); seq.append((c, 60, 'hitstop1'))
                c = put(body_rgba(G[i]), 'hit_spark', 1, hit); seq.append((c, max(60, ms - 40), 'hitstop2'))
            elif i == ifo: seq.append((put(b, 'hit_spark', 2, hit), f['ms'], 'follow'))
            else: seq.append((b, f['ms'], f['key']))
    elif act == 'run':
        n = len(G); dust = {}
        for i, k in enumerate(keys):
            if k.startswith('contact'):
                rs = soles(G[i]);
                if not rs: continue
                r = max(rs, key=len) if len(rs) == 1 else min(rs, key=lambda r: r[0])  # back-most sole = heel side
                x0 = r[0]
                for j in range(3): dust.setdefault((i + j) % n, []).append((j, (x0 - 2 * j, ground_y())))
        # fastest frame = largest silhouette displacement vs previous
        A = [arr(g) != '.' for g in G]; mv = [(A[i] ^ A[i - 1]).sum() for i in range(n)]
        fast = int(np.argmax([mv[i] if fj['frames'][i]['air'] else 0 for i in range(n)]))
        plan = {'dust': {k: v for k, v in dust.items()}, 'speed_frame': fast if speed else None}
        for i, f in enumerate(fj['frames']):
            c = body_rgba(G[i])
            for j, xy in dust.get(i, []): c = put(c, 'dust_step', j, xy)
            if speed and i == fast:
                ys, xs = np.nonzero(A[i]); cx = xs.min() + 1  # back silhouette edge
                c = put(c, 'speed_lines_short', 0, (cx - MF['speed_lines_short']['offset_from_body_centre'][0] - 11, (ys.min() + ys.max()) / 2 + 3), behind=True)
            seq.append((c, f['ms'], f['key']))
    else:
        for i, f in enumerate(fj['frames']): seq.append((body_rgba(G[i]), f['ms'], f['key']))
    os.makedirs(AN + '/gifs', exist_ok=True); os.makedirs(AN + '/strips', exist_ok=True)
    name = '%s_SE_%s' % (act, S)
    FX.save_gif(AN + '/gifs/%s.gif' % name, [s[0] for s in seq], [s[1] for s in seq], 6)
    w, h = seq[0][0].size
    st = Image.new('RGBA', (w * len(seq), h), (0, 0, 0, 0))
    for i, s in enumerate(seq): st.paste(s[0], (i * w, 0))
    st.save(AN + '/strips/%s.png' % name)
    sb = Image.new('RGBA', (CW * len(G), CH), (0, 0, 0, 0))
    for i, g in enumerate(G): sb.paste(body_rgba(g).crop((PAD, PAD, PAD + CW, PAD + CH)), (i * CW, 0))
    sb.save(AN + '/strips/%s_body.png' % name)
    # 4x review strip on grey (<=800 px wide: 2 rows if needed)
    json.dump({'seq': [[s[2], s[1]] for s in seq], 'plan': plan}, open(AN + '/strips/%s.json' % name, 'w'), default=str)
    print(name, [(s[2], s[1]) for s in seq], plan)
    return seq


def sheet(act):
    rows = []
    for S in 'AB':
        fj, fr = load(S, act, 'c'); rows.append([body_rgba(g) for g, _ in fr])
    al = [np.array(im)[..., 3] > 0 for r in rows for im in r]; m = np.any(al, 0)
    xs = np.nonzero(m.any(0))[0]; ys = np.nonzero(m.any(1))[0]
    box = (max(0, xs.min() - 1), max(0, ys.min() - 1), xs.max() + 2, ys.max() + 2)
    cw, ch = box[2] - box[0], box[3] - box[1]; n = max(len(r) for r in rows)
    s = max(1, min(4, (790 - 30) // (n * cw)))
    Wd, Hd = 30 + n * cw * s, 2 * (ch * s + 4) + 16
    sh = Image.new('RGB', (Wd, Hd), BG); dr = ImageDraw.Draw(sh)
    keys = [f['key'] for f in fj_of('A', act)['frames']]
    for j, k in enumerate(keys): dr.text((30 + j * cw * s + 2, 2), k[:9], fill=(255, 255, 255))
    for r, (S, ims) in enumerate(zip('AB', rows)):
        y0 = 16 + r * (ch * s + 4); dr.text((8, y0 + ch * s // 2), S, fill=(255, 255, 0))
        for j, im in enumerate(ims):
            c = im.crop(box).resize((cw * s, ch * s), Image.NEAREST); sh.paste(c, (30 + j * cw * s, y0), c)
    sh.save(AN + '/gifs/%s_SE_AvsB.png' % act); print('sheet', act, sh.size)


def review(S, act, s=3):
    """grey review strip of the composite sequence, <=800px wide (wraps)."""
    st = Image.open(AN + '/strips/%s_SE_%s.png' % (act, S)); w = CW + 2 * PAD; n = st.width // w
    per = max(1, 800 // (w * s)); rows = (n + per - 1) // per
    im = Image.new('RGB', (min(n, per) * w * s, rows * w * s), BG)
    for i in range(n):
        f = st.crop((i * w, 0, (i + 1) * w, w)).resize((w * s, w * s), Image.NEAREST)
        im.paste(f, ((i % per) * w * s, (i // per) * w * s), f)
    p = AN + '/work/review_%s_%s.png' % (act, S); im.save(p); print(p, im.size); return p


def _opt(a, k, n=1, cast=int):
    if k not in a: return None
    i = a.index(k); v = [cast(x) for x in a[i + 1:i + 1 + n]]; del a[i:i + 1 + n]; return v[0] if n == 1 else v


if __name__ == '__main__':
    _a = sys.argv
    v = _opt(_a, '--sole'); SOLE = SOLE if v is None else v
    v = _opt(_a, '--cell', 2); CW, CH = (CW, CH) if v is None else v
    v = _opt(_a, '--fx-pivot-y'); FXPIV_Y = FXPIV_Y if v is None else v
    FX_DY = _opt(_a, '--fx-dy')
    WDIR = _opt(_a, '--dir', cast=str); PALP = _opt(_a, '--palette', cast=str); MASTER = _opt(_a, '--master', cast=str)
    STAMP = _opt(_a, '--stamp', cast=str); _pre = _opt(_a, '--pre', cast=str)
    for k, kk, cs in (('--head-px', 'head_px', int), ('--hist', 'hist_t', float), ('--region-px', 'region_px', int), ('--shape', 'shape_t', float)):
        v = _opt(_a, k, cast=cs)
        if v is not None: COLOPT[kk] = v
    if PALP:
        PALP = os.path.abspath(PALP); LS.set_palette(PALP); RGB = {k: tuple(int(v[0][j:j + 2], 16) for j in (1, 3, 5)) for k, v in LS.PAL.items()}
    c = sys.argv[1]
    if c == 'clean': clean(sys.argv[2], sys.argv[3])
    elif c == 'out': out(sys.argv[2], sys.argv[3], '--nospeed' not in sys.argv)
    elif c == 'sheet': sheet(sys.argv[2])
    elif c == 'review': review(sys.argv[2], sys.argv[3])
    elif c == 'colors': sys.exit(1 if colors(sys.argv[2], sys.argv[3], _pre)['flags'] else 0)
