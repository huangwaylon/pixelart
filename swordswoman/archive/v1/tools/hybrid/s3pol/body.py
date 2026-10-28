"""S3 r1 polish: hand-blocked BODY rig (Claude pixel artist).

The pixelized Gemini bodies were mush, so the polished bodies are re-blocked by hand: each body part is a
hand-placed polygon (traced over the Gemini hi-res / lock turnaround), rasterized at 1x, shaded with a fixed
top-left key light, separated and outlined by rule, then finished with explicit per-pixel ops (draw.py).
The locked head stamp is pasted on top unchanged (hybrid/lock/pixel/head_<DIR>.png).

spec = dict(
  head=('SE', hx, hy),                      # stamp dir + top-left
  parts=[dict(n=name, m=mat, p=[(x,y),...], z=int, sh=k, hl=1, base=char, dark=char, light=char, ol=True)],
  ops=[draw.py op strings applied after the head],  pre=[ops applied before the head])
"""
import sys, os, json, subprocess, importlib.util
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, 'tools/hybrid/s3')
from pol import C, load, save, chars, put

TONES = {   # base, shadow, light, deep/separation
    'red': ('R', 'r', 'C', 'v'), 'skin': ('s', 'm', 'S', 'm'), 'lea': ('l', 'K', 'L', 'K'),
    'dark': ('d', 'K', 'd', 'K'), 'hair': ('H', 'h', 'J', 'h'), 'pink': ('P', 'p', 'P', 'p'),
    'steel': ('T', 't', 'w', 't'), 'vio': ('v', 'v', 'r', 'K'), 'shad': ('r', 'v', 'R', 'v'),
}
LITDARK = {'R': 'r', 'r': 'v', 'C': 'R', 'v': 'v', 's': 'm', 'S': 's', 'm': 'm', 'l': 'K', 'L': 'l', 'd': 'K',
           'H': 'h', 'h': 'h', 'J': 'H', 'P': 'p', 'p': 'p', 'T': 't', 'w': 'T', 't': 't'}

def raster(p):
    im = Image.new('L', (128, 128), 0)
    d = ImageDraw.Draw(im)
    if len(p) == 2:
        d.line(p, fill=255)
    else:
        d.polygon(p, fill=255, outline=255)
    return np.array(im) > 0

def shift(m, dx, dy):
    o = np.zeros_like(m)
    H, W = m.shape
    ys, xs = slice(max(0, dy), H + min(0, dy)), slice(max(0, dx), W + min(0, dx))
    ys2, xs2 = slice(max(0, -dy), H + min(0, -dy)), slice(max(0, -dx), W + min(0, -dx))
    o[ys, xs] = m[ys2, xs2]
    return o

def render(spec, head_src=None):
    a = np.zeros((128, 128, 4), np.uint8)
    own = np.full((128, 128), -1)          # part index per pixel
    parts = sorted(enumerate(spec['parts']), key=lambda t: t[1].get('z', 0))
    for i, pt in parts:
        m = raster(pt['p'])
        for extra in pt.get('add', []): m |= raster(extra)
        for cut in pt.get('cut', []): m &= ~raster(cut)
        base, dark, light, deep = TONES[pt['m']]
        base, dark, light = pt.get('base', base), pt.get('dark', dark), pt.get('light', light)
        k = pt.get('sh', 2)
        sdx, sdy = pt.get('sd', (1, 0))
        shadow = m & ~shift(m, -k * sdx, -k * sdy) if k else np.zeros_like(m)
        lit = m & ~shift(m, 1, 1) & ~shadow if pt.get('hl', 1) else np.zeros_like(m)
        for y, x in zip(*np.nonzero(m)):
            ch = dark if shadow[y, x] else (light if lit[y, x] else base)
            put(a, x, y, ch); own[y, x] = i
    # separation lines between overlapping parts of the same material family (behind part gets its deep tone)
    c = chars(a)
    out = a.copy()
    for y in range(1, 127):
        for x in range(1, 127):
            i = own[y, x]
            if i < 0: continue
            pi = spec['parts'][i]
            if pi.get('nosep'): continue
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                j = own[y + dy, x + dx]
                if j >= 0 and j != i and spec['parts'][j].get('z', 0) > pi.get('z', 0):
                    mi, mj = pi['m'], spec['parts'][j]['m']
                    if mi == mj or pi.get('sepall') or (mi, mj) in (('skin', 'skin'),):
                        put(out, x, y, TONES[mi][3] if mi != 'lea' else 'K')
                        break
                    if mj in ('red', 'lea') and mi in ('skin', 'red'):   # cast shadow under cloth
                        put(out, x, y, TONES[mi][1]); break
    a = out
    # exterior outline (inside the part edge): bottom/right K, top/left sel-out (material dark tone)
    c = chars(a)
    out = a.copy()
    for y in range(1, 127):
        for x in range(1, 127):
            i = own[y, x]
            if i < 0 or not spec['parts'][i].get('ol', True): continue
            v = c[y, x]
            for dy, dx in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                if c[y + dy, x + dx] == '.':
                    lit = (dy == -1 or dx == -1) and spec['parts'][i].get('selout', True)
                    put(out, x, y, LITDARK.get(v, 'K') if lit else 'K')
                    break
    a = out
    tmp = '/tmp/_body_%d.png' % os.getpid()
    save(a, tmp)
    if spec.get('pre'):
        draw(tmp, tmp, spec['pre'])
    a = load(tmp)
    if 'head' in spec:
        d, hx, hy = spec['head']
        hp = spec.get('head_png', f'hybrid/lock/pixel/head_{d}.png')
        h = np.array(Image.open(hp).convert('RGBA'))
        m = h[..., 3] > 0
        sub = a[hy:hy + h.shape[0], hx:hx + h.shape[1]]
        sub[m] = h[m]
    save(a, tmp)
    if spec.get('ops'):
        draw(tmp, tmp, spec['ops'])
    return load(tmp)

def draw(inp, out, ops):
    r = subprocess.run(['.venv/bin/python', 'tools/hybrid/draw.py', inp, '--out', out] + list(ops),
                       capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); raise SystemExit(1)

def load_spec(path):
    s = importlib.util.spec_from_file_location('spec', path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m.SPEC

if __name__ == '__main__':
    spec = load_spec(sys.argv[1])
    save(render(spec), sys.argv[2])
