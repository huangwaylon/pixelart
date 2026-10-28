"""m96.py helpers. CLI:
  m96.py crop STEM X0 Y0 X1 Y1 [S=8] OUT.png   : illustration crop | sprite crop (S x), side by side
  m96.py gate DIR [views]                       : metrics vs master0 + lint + colorcheck(vs master0); exit 1 if fidelity drops
  m96.py txt STEM X0 Y0 X1 Y1                   : print char crop with coordinates
"""
import sys, os, json, subprocess, numpy as np
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
sys.path.insert(0, ROOT + 'v2/pixelize/tools')
import pzlib as Z
from PIL import Image, ImageDraw
PAL = ROOT + 'v2/pixelize/palette.json'
BASE = os.environ.get('M96_BASE', ROOT + 'v2/m96/master0')
TOL = dict(ssim_b=-0.002, dE=0.10, face_ssim=-0.01, sil=-0.003, line_f=-0.01)

def illus_box(meta, x0, y0, x1, y1):
    x, m = Z.load(meta['view'], meta['src']); Hh, Ww = m.shape
    fx = lambda X: (X - meta['ox']) * Ww / meta['w']; fy = lambda Y: (Y - meta['oy']) * Hh / meta['h']
    return x, (fx(x0), fy(y0), fx(x1), fy(y1))

def crop(stem, x0, y0, x1, y1, s, out):
    g, meta = Z.read(stem); keys, rgb, _ = Z.load_pal(PAL)
    im = Z.render(g, keys, rgb).crop((x0, y0, x1, y1)); im = im.resize((im.width * s, im.height * s), Image.NEAREST)
    x, b = illus_box(meta, x0, y0, x1, y1)
    il = Image.fromarray(x.astype(np.uint8)).crop(tuple(int(round(v)) for v in b)).resize(im.size, Image.LANCZOS)
    W = im.width * 2 + 8; S = Image.new('RGB', (W, im.height), 'white'); S.paste(il, (0, 0))
    bg = Image.new('RGB', im.size, (200, 200, 200)); bg.paste(im, (0, 0), im); d = ImageDraw.Draw(bg)
    for X in range(x0, x1):
        if X % 5 == 0: d.line([((X - x0) * s, 0), ((X - x0) * s, 3)], fill='blue')
    S.paste(bg, (im.width + 8, 0)); S.save(out); print(out, S.size)

def metrics(stem):
    import metrics as M
    sys.argv = ['m']
    r = M.compute(stem) if hasattr(M, 'compute') else None
    return r

def runmetrics(stems):
    py = ROOT + '.scratch/pixtools/venv/bin/python'
    tmp = f'/tmp/m96_met_{os.getpid()}.json'
    subprocess.run([py, '-I', ROOT + 'v2/pixelize/tools/metrics.py', *stems, '--json', tmp], capture_output=True, cwd=ROOT)
    r = json.load(open(tmp)); os.remove(tmp); return r

def gate(d, views):
    d = os.path.abspath(d); stems = [f'{d}/EC0_{v}_96' for v in views]; base = [f'{BASE}/EC0_{v}_96' for v in views]
    a = runmetrics(stems); b = runmetrics(base); ok = True
    def get(r, s):
        k = os.path.basename(s); return r[k] if isinstance(r, dict) and k in r else next(x for x in r if x.get('name') == k)
    for v, s, bs in zip(views, stems, base):
        ra, rb = get(a, s), get(b, bs); line = [v]
        for k, t in TOL.items():
            va, vb = ra.get(k), rb.get(k)
            if not isinstance(va, (int, float)) or not isinstance(vb, (int, float)) or va != va or vb != vb: continue
            bad = (va - vb > t) if k == 'dE' else (va - vb < t)
            ok &= not bad; line.append(f'{k}={va:.3f}({va - vb:+.3f}){"!" if bad else ""}')
        lint = subprocess.run(['python3', ROOT + 'v2/anim_cut/tools/lint_style.py', s + '.txt', '--palette', PAL, '--pivot', '64', '124'], capture_output=True, text=True).stdout
        cnt = {l.split()[0]: (str(l.count("('")) if l.split()[0] == 'O3' else l.split()[1]) for l in lint.splitlines()[1:] if l.strip()}
        cc = subprocess.run(['python3', ROOT + 'v2/anim_cut/tools/colorcheck.py', 'material', s + '.txt', '--master', bs + '.txt', '--palette', PAL], capture_output=True, text=True).stdout
        pal = 'PAL' in cnt
        ok &= not pal
        line.append('lint ' + ' '.join(f'{k}:{n}' for k, n in cnt.items()) + f' | cc {cc.count("MAT")} MAT')
        print('  '.join(line))
    return ok

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'crop':
        s = int(a[6]) if len(a) > 7 else 8
        crop(a[1], *map(int, a[2:6]), s, a[-1])
    elif a[0] == 'txt':
        g, _ = Z.read(a[1]); x0, y0, x1, y1 = map(int, a[2:6])
        print('    ' + ''.join(str(x // 10 % 10) for x in range(x0, x1))); print('    ' + ''.join(str(x % 10) for x in range(x0, x1)))
        for y in range(y0, y1): print(f'{y:3d} ' + ''.join(g[y, x0:x1]))
    elif a[0] == 'gate':
        sys.exit(0 if gate(a[1], a[2:] or ['S', 'SE', 'E', 'NE', 'N']) else 1)
