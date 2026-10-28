# qa_zoom.py PREFIX : rig 1x (point-sampled) vs master per view at 5x, rows ruled every 5 px
import sys, numpy as np
from PIL import Image, ImageDraw
pre = sys.argv[1]; M = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_{}_96.png'
out = Image.new('RGB', (6 * 70 * 5, 104 * 5), (110, 110, 110))
for i, v in enumerate(('S', 'E', 'SE')):
    a = np.asarray(Image.open(f'{pre}_{v}.png').convert('RGBA')); k = a.shape[0] // 192
    b = a[32 * k:160 * k, 32 * k:160 * k].reshape(128, k, 128, k, 4)[:, k // 2, :, k // 2]
    for j, im in enumerate((Image.fromarray(b, 'RGBA'), Image.open(M.format(v)).convert('RGBA'))):
        bg = Image.new('RGBA', (128, 128), (110, 110, 110, 255)); bg.alpha_composite(im); t = bg.crop((29, 24, 99, 128)).resize((350, 520), Image.NEAREST)
        d = ImageDraw.Draw(t)
        for y in range(0, 104, 5): d.line([(0, y * 5), (8, y * 5)], fill=(255, 255, 0) if (y + 24) % 10 == 0 else (0, 255, 255))
        out.paste(t.convert('RGB'), ((2 * i + j) * 350, 0))
out.save(f'{pre}_zoom.png')
