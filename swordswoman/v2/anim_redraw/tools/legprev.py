"""legprev.py ACT: composite work48/<act>/legs/fNN.txt onto work48/<act>/k1/bNN.png -> legs/preview.png (8x top, 1x strip)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fin48 as F, numpy as np
from PIL import Image
act = sys.argv[1]; W = f'{F.A}/work48/{act}'
fr = []
for i in range(8):
    g = F.to_grid(f'{W}/k1/b{i:02d}.png'); p = f'{W}/legs/f{i:02d}.txt'
    if os.path.exists(p): g = F.apply_legs(g, p, np.zeros(g.shape, bool))
    fr.append(g)
S = 5; sh = Image.new('RGB', (4 * (40 * S + 4), 2 * (34 * S + 4) + 40), (40, 40, 40))
for i, g in enumerate(fr):
    im = F.to_img(g[28:62, 12:52], (110, 110, 110))
    sh.paste(im.resize((40 * S, 34 * S), Image.NEAREST), ((i % 4) * (40 * S + 4), (i // 4) * (34 * S + 4)))
    sh.paste(im, (i * 44, 2 * (34 * S + 4) + 3))
sh.save(f'{W}/legs/preview.png'); print('wrote', f'{W}/legs/preview.png', sh.size)
