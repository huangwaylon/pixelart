"""S3 r1 polish: compose ANIMATION keys from the hand-typed turn cels (tools/hybrid/s3pol/cels/turn_<DIR>.cel).

Each key = the turn cel of its direction, with
  - layers dropped / replaced by hand-typed or hand-placed rows (legs, arms, sleeves, katana, ribbons ...),
  - integer layer offsets (bounce, weight shift, lunge),
  - the locked head stamp moved by its own lag offset, its top (bun + bow) shifted by a further lag offset,
  - a painted expression (calm / frown / wide / smile / effort) on the stamp,
  - FX ops (smears, sparks, dust, motion lines) from tools/hybrid/draw.py.
Usage: anim.py SPEC.py OUT_DIR [name ...]
"""
import sys, os, copy, importlib.util
import numpy as np
sys.path.insert(0, 'tools/hybrid/s3'); sys.path.insert(0, 'tools/hybrid/s3pol')
import cel as CEL
from pol import load, save, put, chars

def rows_of(text):
    """cel-format rows -> parsed row tuples"""
    tmp = '/tmp/_rows_%d.cel' % os.getpid()
    open(tmp, 'w').write('[x]\n' + text.strip('\n') + '\n')
    return CEL.parse(tmp)['layers'][0]['rows']

# expression edits per stamp dir: list of (col, row, char) relative to the stamp top-left
EXPR = {
 'SE': {
  'calm': [],
  'frown': [(11, 23, 'K'), (12, 23, 'K'), (18, 23, 'K'), (19, 23, 'K'), (10, 22, 'h'), (20, 22, 'h'), (8, 24, 's'),
            (14, 29, 'm'), (15, 29, 'm')],
  'glare': [(11, 23, 'K'), (12, 23, 'K'), (18, 23, 'K'), (19, 23, 'K'), (10, 22, 'h'), (20, 22, 'h'), (8, 24, 's'),
            (9, 25, 'K'), (10, 25, 'K'), (11, 25, 'K'), (18, 25, 'K'), (19, 25, 'K'), (20, 25, 'K'),
            (14, 29, 'm'), (15, 29, 'm'), (16, 29, 'm')],
  'wide': [(11, 23, 'K'), (12, 23, 'K'), (18, 23, 'K'), (19, 23, 'K'), (14, 29, 'K'), (15, 29, 'K'), (14, 30, 'v'), (15, 30, 'v')],
  'smile': [(c, r, 's') for c in range(8, 13) for r in (24, 25, 26, 27)] + [(c, r, 's') for c in range(18, 22) for r in (24, 25, 26, 27)]
           + [(9, 25, 'K'), (10, 24, 'K'), (11, 24, 'K'), (12, 25, 'K'), (8, 26, 'K'),
              (18, 25, 'K'), (19, 24, 'K'), (20, 24, 'K'), (21, 25, 'K'), (17, 26, 'K'),
              (13, 29, 'K'), (14, 30, 'K'), (15, 30, 'K'), (16, 29, 'K'), (14, 29, 's'), (15, 29, 's')],
  'effort': [(11, 23, 'K'), (12, 23, 'K'), (18, 23, 'K'), (19, 23, 'K'), (10, 22, 'h'), (20, 22, 'h'),
             (9, 25, 'K'), (10, 25, 'K'), (11, 25, 'K'), (12, 25, 'K'), (18, 25, 'K'), (19, 25, 'K'), (20, 25, 'K'),
             (13, 29, 'K'), (14, 29, 'K'), (15, 29, 'K'), (16, 29, 'K'), (14, 30, 'v'), (15, 30, 'v')],
 },
 'E': {
  'calm': [],
  'frown': [(21, 23, 'K'), (22, 23, 'K'), (19, 22, 'h'), (23, 24, 's'), (23, 30, 'm')],
  'wide': [(21, 23, 'K'), (24, 30, 'K'), (24, 31, 'v')],
  'smile': [(c, r, 's') for c in range(18, 24) for r in (24, 25, 26)] + [(19, 25, 'K'), (20, 24, 'K'), (21, 24, 'K'),
            (22, 25, 'K'), (23, 26, 'K'), (22, 30, 'K'), (23, 31, 'K'), (24, 30, 'K')],
  'effort': [(21, 23, 'K'), (22, 23, 'K'), (19, 22, 'h'), (19, 25, 'K'), (20, 25, 'K'), (21, 25, 'K'), (22, 25, 'K'),
             (23, 30, 'K'), (24, 30, 'K'), (23, 31, 'v')],
 },
}

def render_frame(fs, cels_dir='tools/hybrid/s3pol/cels'):
    base = CEL.parse(os.path.join(cels_dir, fs['base']))
    layers = []
    for L in base['layers']:
        if L['name'] in fs.get('drop', ()):
            continue
        L = copy.deepcopy(L)
        if L['name'] in fs.get('replace', {}):
            L['rows'] = rows_of(fs['replace'][L['name']])
        if L['name'] in fs.get('add', {}):
            L['rows'] = L['rows'] + rows_of(fs['add'][L['name']])
        layers.append(L)
    for pos, name, text in fs.get('insert', ()):
        L = dict(name=name, off=(0, 0), rows=rows_of(text))
        if pos == 'back': layers.insert(0, L)
        elif pos == 'front': layers.append(L)
        else:                                   # before:<layer>
            idx = [l['name'] for l in layers].index(pos.split(':')[1]); layers.insert(idx, L)
    base['layers'] = layers
    d, hx, hy = base['head']
    hdx, hdy = fs.get('head', (0, 0))
    base['head'] = (d, hx + hdx, hy + hdy)
    hd = fs.get('head_dir')
    if hd: base['head'] = (hd[0], hd[1], hd[2])
    base['ops'] = []                            # ops of the turn cel are not reused
    a = CEL.render(base, layer_off=fs.get('off', {}))
    d, hx, hy = base['head']
    # bun/bow lag: shift the stamp's top rows (0..rows) by (bx,by) relative to the head
    bx, by = fs.get('bow', (0, 0))
    if (bx, by) != (0, 0):
        R = fs.get('bow_rows', 9)
        top = a[hy:hy + R + 1, hx:hx + 26].copy()
        reg = a[hy - 3:hy + R + 2, hx - 3:hx + 29]
        # clear the stamp top, then paste it shifted; keep the original row R+1 under it (stretch / compress)
        a[hy:hy + R + 1, hx:hx + 26][top[..., 3] > 0] = 0
        y0, x0 = hy + by, hx + bx
        sub = a[y0:y0 + R + 1, x0:x0 + 26]
        m = top[..., 3] > 0
        sub[m] = top[m]
        if by < 0:                              # stretched: repeat the row under the shifted top
            for k in range(-by):
                row = a[hy + R + 1, hx:hx + 26]
                r2 = a[hy + R - k, hx:hx + 26]
                fill = (r2[..., 3] == 0) & (row[..., 3] > 0)
                r2[fill] = row[fill]
    for c, r, ch in EXPR.get(d[-2:] if d[-2:] in EXPR else d, {}).get(fs.get('expr', 'calm'), []):
        put(a, hx + c, hy + r, ch)
    tmp = '/tmp/_anim_%d.png' % os.getpid()
    save(a, tmp)
    if fs.get('ops'):
        CEL.draw(tmp, tmp, fs['ops'])
    return load(tmp)

def load_spec(path):
    s = importlib.util.spec_from_file_location('aspec', path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m.FRAMES

if __name__ == '__main__':
    frames = load_spec(sys.argv[1]); out = sys.argv[2]; only = sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    for n, fs in frames.items():
        if only and n not in only: continue
        save(render_frame(fs), os.path.join(out, n + '.png')); print('wrote', n)
