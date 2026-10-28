"""sheet.py out.png a.txt b.txt ... : 1x row + 4x row on mid-grey, guide lines at rows 10 (bow top), 16 (skull top), 35 (chin), 59 (ground); prints head metrics."""
import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import cm
out, fs = sys.argv[1], sys.argv[2:]; S = 4
gs = [cm.read(f) for f in fs]; n = len(gs)
W = n * (64 * S + 8) + 8; H = 64 + 16 + 64 * S + 24
sh = Image.new('RGB', (W, H), cm.GREY); d = ImageDraw.Draw(sh)
for i, (f, g) in enumerate(zip(fs, gs)):
    x = 8 + i * (64 * S + 8)
    sh.paste(cm.to_img(g, 1), (x, 4), cm.to_img(g, 1))
    big = cm.to_img(g, S); y0 = 64 + 16
    sh.paste(big, (x, y0), big)
    for r, col in [(10, (255, 220, 0)), (16, (0, 220, 255)), (35, (0, 255, 120)), (60, (255, 80, 80))]:
        d.line([(x, y0 + r * S), (x + 64 * S - 1, y0 + r * S)], fill=col)
    d.text((x, H - 18), f.split('/')[-1][:-4], fill='white')
    A = np.array([list(l) for l in g]); hair = np.isin(A[:42], list('Hh'))
    rows = np.where(hair.sum(1) >= 2)[0]; ink = A != '.'
    hw = max(np.ptp(np.where(ink[r])[0]) + 1 for r in range(rows.min() + 2, min(rows.min() + 17, 36)))
    print(f.split('/')[-1], 'top', np.where(ink.any(1))[0].min(), 'hair', rows.min(), '-', rows.max(), 'head_w', hw, 'bottom', np.where(ink.any(1))[0].max())
sh.save(out); print(out, sh.size)
