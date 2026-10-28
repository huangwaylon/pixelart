# view.py out.png a.txt b.txt ... [--s 5]: crops (rows 2-63, cols 12-52) zoomed side by side + a 1x and 2x row below. Keep <=800 px wide.
import sys; sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/archive/v2/mastersF/tools'); import mf
from PIL import Image
a = sys.argv[1:]; s = int(a[a.index('--s') + 1]) if '--s' in a else 5; fs = [f for f in a[1:] if f.endswith('.txt')]
BG = (150, 150, 160, 255); gs = [mf.load(f)[0] for f in fs]
big = [mf.png(g, None, 1, BG).crop((12, 2, 52, 64)).resize((40 * s, 62 * s), 0) for g in gs]
W = sum(b.width + 8 for b in big); H = 62 * s + 130; S = Image.new('RGBA', (W, H), BG); x = 0
for b in big: S.alpha_composite(b, (x, 0)); x += b.width + 8
x = 0
for g in gs:
    one = mf.png(g, None, 1, BG); S.alpha_composite(one, (x, 62 * s + 2)); S.alpha_composite(one.resize((128, 128), 0), (x + 66, 62 * s + 2)); x += 200
S.save(a[0]); print(a[0], S.size)
