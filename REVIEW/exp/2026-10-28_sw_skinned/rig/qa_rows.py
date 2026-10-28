# qa_rows.py PREFIX : per view, rows/cols of material bands in the render (1x) vs master (palette codes)
import sys, numpy as np
from PIL import Image
pre = sys.argv[1]; MT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_{}_96.txt'
MATS = {'hair': (61, 50, 53), 'dress': (192, 59, 61), 'skin': (248, 218, 194), 'sleeve': (142, 34, 44), 'socks': (38, 42, 71),
        'boots': (42, 34, 42), 'bow': (232, 96, 79), 'obi': (69, 56, 73), 'eyes': (85, 128, 162)}
MN = list(MATS); MC = np.array([MATS[k] for k in MN], float)
for v in ('S', 'E', 'SE'):
    a = np.asarray(Image.open(f'{pre}_{v}.png').convert('RGBA')).astype(float); k = a.shape[0] // 192
    a = a[32 * k:160 * k, 32 * k:160 * k].reshape(128, k, 128, k, 4)[:, k // 2, :, k // 2]
    al = a[..., 3] > 127; mid = ((a[..., None, :3] - MC) ** 2).sum(-1).argmin(-1); mid[~al] = -1
    g = np.array([list(l.rstrip('\n')) for l in open(MT.format(v)) if l.strip() and not l.startswith(';')])
    def rr(mask):
        ys = np.where(mask.any(1))[0]; return (int(ys.min()), int(ys.max())) if len(ys) else None
    def cc(mask):
        xs = np.where(mask.any(0))[0]; return (int(xs.min()), int(xs.max())) if len(xs) else None
    R = {'all': rr(al), 'obi': rr(mid == MN.index('obi')), 'socks': rr(mid == MN.index('socks')), 'boots': rr(mid == MN.index('boots')), 'cols': cc(al)}
    Mm = {'all': rr(g != '.'), 'obi': rr(np.isin(g, list('oOQ'))), 'socks': rr(np.isin(g, list('Dd'))), 'boots': rr(np.isin(g[90:], list('hHgL'))) , 'cols': cc(g != '.')}
    if Mm['boots']: Mm['boots'] = (Mm['boots'][0] + 90, Mm['boots'][1] + 90)
    print(v, 'rig', R); print(v, 'mst', Mm)
