#!/usr/bin/env python3
"""post96.py: post pass for the 96 px pipeline (ff_redraw --head-lock clips, 128 cell).
  post96.py clean CLIPDIR [--dx N] [--sock-thin]         fNN -> cNN.txt: re-paste the locked head at head_at, deboil 1-frame blips,
                                     static-region boil report (guide unchanged but drawing changed) -> clean.txt
  post96.py out   CLIPDIR [--fx auto|none] [--outdir v2/animate96/gifs]
                                     FX (walk/run contacts: fx96 dust_step at the planted heel; others none),
                                     <clip>.gif (4x on #6e6e6e, frames.json ms), <clip>_1x.png strip (RGBA),
                                     <clip>_sheet.png (guide | frame per key, <=800 px wide), <clip>_fx.json
  post96.py qc    CLIPDIR [qc_gate clip options]   -> qc_gate.py clip (report in v2/qc/out/clip_<clip>)
Old animate/tools/post.py is untouched (48/64 px pipeline)."""
import os, sys, json, re
import numpy as np
from PIL import Image, ImageDraw
V2 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2'
sys.path.insert(0, V2 + '/anim_cut/tools'); sys.path.insert(0, V2 + '/animate/tools')
import lint_style as LS, colorcheck as CC
import post as P0  # deboil()
BG = (0x6e, 0x6e, 0x6e)
FXM = json.load(open(V2 + '/fx96/manifest.json'))['effects']


def load(cd, pre='f'):
    fj = json.load(open(cd + '/frames.json')); cw, ch = fj['cell']; out = []
    for f in fj['frames']:
        p = '%s/%s%02d.txt' % (cd, pre, f['i'])
        if not os.path.exists(p): p = '%s/f%02d.txt' % (cd, f['i'])
        g, meta = LS.read(p); g = [r[:cw].ljust(cw, '.') for r in g[:ch]] + ['.' * cw] * max(0, ch - len(g))
        out.append((g, meta))
    return fj, out


def rgbmap(fj):
    pal = CC.load(fj.get('palette') or V2 + '/pixelize/palette.json'); return pal, dict(pal.rgb)


def paste(a, st, at):
    for r, row in enumerate(st):
        for c, ch in enumerate(row):
            X, Y = at[0] + c, at[1] + r
            if ch != '.' and 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]: a[Y, X] = ch


def shift(a, dx):
    if not dx: return a
    b = np.full_like(a, '.')
    if dx > 0: b[:, dx:] = a[:, :-dx]
    else: b[:, :dx] = a[:, -dx:]
    return b


def clean(cd, dx=0, sock_thin=False):
    """dx: shift the whole clip horizontally (per-view pivot correction, e.g. guide body vs master obi centre)."""
    fj, fr = load(cd); n = len(fj['frames']); cw, ch = fj['cell']; loop = fj.get('loop', True); rep = []
    pal, _ = rgbmap(fj); LS.set_palette(pal.path)
    P0.CW, P0.CH = cw, ch
    A = [np.array([list(r) for r in g]) for g, _ in fr]
    for i, f in enumerate(fj['frames']):
        if f.get('head_at'): paste(A[i], LS.read(f['stamp'])[0], f['head_at'])
        A[i] = shift(A[i], dx)
    B, c = P0.deboil(A, loop); rep.append('deboil %d px' % c)
    if sock_thin:  # sock light d = 1 px streak like the master: in every run 'dd..' keep the first d, rest -> D
        n0 = 0
        for b in B:
            for y in range(b.shape[0]):
                for x in range(1, b.shape[1]):
                    if b[y, x] == 'd' and b[y, x - 1] == 'd': b[y, x] = 'D'; n0 += 1
        rep.append('sock-thin %d px d->D' % n0)
    # head windows are never deboiled (expression changes are deliberate)
    for i, f in enumerate(fj['frames']):
        if f.get('head_at'): paste(B[i], LS.read(f['stamp'])[0], [f['head_at'][0] + dx, f['head_at'][1]])
    G = [shift(np.array([list(r) for r in LS.read('%s/g%02d.txt' % (cd, f['i']))[0]]), dx) for f in fj['frames']]
    rep.append('clip shift dx %+d' % dx)
    for i in range(n):
        j = (i + 1) % n
        if not loop and j == 0: break
        same = (G[i] == G[j]); k = np.ones((5, 5), bool)
        st = np.array([[same[max(0, y - 2):y + 3, max(0, x - 2):x + 3].all() for x in range(cw)] for y in range(ch)])
        hd = np.zeros_like(st)
        for f2 in (fj['frames'][i], fj['frames'][j]):
            if f2.get('head_at'):
                s = LS.read(f2['stamp'])[0]; x0, y0 = f2['head_at'][0] + dx, f2['head_at'][1]; hd[max(0, y0):y0 + len(s), max(0, x0):x0 + len(s[0])] = True
        ch_px = (B[i] != B[j]); boil = ch_px & st & ~hd & (G[i] != '.')
        rep.append('d%02d-%02d changed %d px, static-guide boil %d px' % (i, j, ch_px.sum(), boil.sum()))
    for i, f in enumerate(fj['frames']):
        meta = P0.meta_lines(fr[i][1]); g = [''.join(r) for r in B[i]]
        open('%s/c%02d.txt' % (cd, i), 'w').write(''.join('; %s\n' % m for m in meta) + '\n'.join(g) + '\n')
    open(cd + '/clean.txt', 'w').write('\n'.join(rep) + '\n'); print('\n'.join(rep))
    json.dump({'dx': dx}, open(cd + '/post96.json', 'w'))


def rgba(g, RGB, pad=0):
    h, w = len(g), len(g[0]); im = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0)); px = im.load()
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c in RGB: px[x + pad, y + pad] = tuple(RGB[c]) + (255,)
    return im


def fxframe(name, k): return Image.open('%s/fx96/%s' % (V2, FXM[name]['frames'][k])).convert('RGBA')


def heel(g, row):
    """back-most (smallest x) opaque run on the sole row -> its first x."""
    runs = [(m.start(), m.end()) for m in re.finditer(r'[^.]+', g[row])]
    return runs[0][0] if runs else None


def out(cd, fx='auto', outdir=V2 + '/animate96/gifs'):
    fj, fr = load(cd, 'c'); _, RGB = rgbmap(fj); name = os.path.basename(cd.rstrip('/'))
    cw, ch = fj['cell']; px, py = fj['pivot']; act = fj['act']; n = len(fr); G = [g for g, _ in fr]
    layers = {i: [] for i in range(n)}; plan = []
    if fx == 'auto' and act in ('walk', 'run'):
        for i, f in enumerate(fj['frames']):
            if f.get('contact') and not f.get('air'):
                x = heel(G[i], py)
                if x is None: continue
                plan.append({'frame': i, 'fx': 'dust_step', 'heel': [x, py]})
                for j in range(2 if act == 'walk' else len(FXM['dust_step']['frames'])):  # walk: contact + 1 (crit r1: 3 frames too heavy)
                    if (i + j < n) or fj.get('loop', True): layers[(i + j) % n].append(('dust_step', j, (x, py)))
    os.makedirs(outdir, exist_ok=True); seq = []
    for i, f in enumerate(fj['frames']):
        im = rgba(G[i], RGB)
        for nm, k, (x, y) in layers[i]:
            e = FXM[nm]; fi = fxframe(nm, k); pv = e['pivot']; lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
            lay.paste(fi, (int(x - pv[0]), int(y - pv[1])), fi)
            im = Image.alpha_composite(im, lay) if e.get('layer', 'over') == 'over' else Image.alpha_composite(lay, im)
        seq.append((im, f['ms']))
    # crop box = union of opaque px over the clip (+4), keeps the GIF small; 4x on grey
    al = np.any([np.array(s[0])[..., 3] > 0 for s in seq], 0); ys, xs = np.nonzero(al)
    box = (max(0, xs.min() - 4), max(0, ys.min() - 4), min(cw, xs.max() + 5), min(ch, ys.max() + 5))
    fr4 = []
    for im, ms in seq:
        c = im.crop(box); bg = Image.new('RGBA', c.size, BG + (255,)); bg.alpha_composite(c)
        fr4.append(bg.convert('RGB').resize((c.width * 4, c.height * 4), Image.NEAREST))
    fr4[0].save('%s/%s.gif' % (outdir, name), save_all=True, append_images=fr4[1:], loop=0, duration=[s[1] for s in seq], disposal=2)
    st = Image.new('RGBA', (cw * n, ch), (0, 0, 0, 0))
    for i, (im, _) in enumerate(seq): st.paste(im, (i * cw, 0))
    st.save('%s/%s_1x.png' % (outdir, name))
    # sheet: guide | frame per key, 2x, wrap to <=800 px
    dx = json.load(open(cd + '/post96.json')).get('dx', 0) if os.path.exists(cd + '/post96.json') else 0
    gb = [rgba([''.join(r) for r in shift(np.array([list(r) for r in LS.read('%s/g%02d.txt' % (cd, f['i']))[0]]), dx)], RGB) for f in fj['frames']]
    w, h = box[2] - box[0], box[3] - box[1]; s = 2; pw = 2 * w * s + 6; per = max(1, 800 // pw); rows = (n + per - 1) // per
    sh = Image.new('RGB', (min(n, per) * pw, rows * (h * s + 14)), (40, 40, 40)); dr = ImageDraw.Draw(sh)
    for i, f in enumerate(fj['frames']):
        x0, y0 = (i % per) * pw, (i // per) * (h * s + 14)
        dr.text((x0 + 2, y0), 'f%02d %s %s %dms' % (i, f['key'], f.get('expression', ''), f['ms']), fill=(230, 230, 230))
        for k, im in enumerate((gb[i], seq[i][0])):
            c = im.crop(box).resize((w * s, h * s), Image.NEAREST); bg = Image.new('RGB', c.size, BG); bg.paste(c, (0, 0), c)
            sh.paste(bg, (x0 + k * w * s, y0 + 12))
    sh.save('%s/%s_sheet.png' % (outdir, name))
    json.dump({'plan': plan, 'box': box, 'ms': [s[1] for s in seq]}, open('%s/%s_fx.json' % (outdir, name), 'w'), default=int)
    print('out %s: gif %dx%d, plan %s, sheet %s' % (name, fr4[0].width, fr4[0].height, plan, sh.size))


if __name__ == '__main__':
    a = sys.argv[1:]; c = a.pop(0); cd = os.path.abspath(a.pop(0))
    if c == 'clean': clean(cd, int(a[a.index('--dx') + 1]) if '--dx' in a else 0, '--sock-thin' in a)
    elif c == 'out':
        fx = a[a.index('--fx') + 1] if '--fx' in a else 'auto'; od = a[a.index('--outdir') + 1] if '--outdir' in a else V2 + '/animate96/gifs'
        out(cd, fx, od)
    elif c == 'qc':
        sys.path.insert(0, V2 + '/qc'); import qc_gate; sys.exit(qc_gate.main(['clip', cd] + a))
