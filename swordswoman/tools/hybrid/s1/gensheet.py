import json, sys
from PIL import Image, ImageDraw
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/hybrid/S1_redraw/r1'
gd, out = sys.argv[1], sys.argv[2]
names = sys.argv[3:] or list(json.load(open(R + '/guide_in/frames.json')))
T = 300; cols = 8
rows = (len(names) + cols - 1) // cols
s = Image.new('RGB', (T * cols, rows * T * 2), 'white'); d = ImageDraw.Draw(s)
for i, n in enumerate(names):
    x, y = (i % cols) * T, (i // cols) * 2 * T
    g = Image.open(f'{R}/guide_in/{n}_clay_M.png').convert('RGB'); g.thumbnail((T, T)); s.paste(g, (x, y))
    try:
        im = Image.open(f'{gd}/{n}.png').convert('RGB'); im.thumbnail((T, T)); s.paste(im, (x, y + T))
    except Exception as e: pass
    d.text((x + 4, y + 4), n, fill='red')
s.save(out)
