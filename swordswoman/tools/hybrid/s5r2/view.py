"""view.py OUT.png sprite.png [...] [--z 8] [--box x0,y0,x1,y1] : zoomed strip on grass + 1x row"""
import sys
from PIL import Image, ImageDraw
a = sys.argv[1:]; z = 8; box = (24, 30, 112, 110)
if '--z' in a: i = a.index('--z'); z = int(a[i + 1]); del a[i:i + 2]
if '--box' in a: i = a.index('--box'); box = tuple(int(v) for v in a[i + 1].split(',')); del a[i:i + 2]
out, fs = a[0], a[1:]
w, h = box[2] - box[0], box[3] - box[1]
W = Image.new('RGBA', (len(fs) * w * z, h * z + h + 16), (40, 40, 48, 255)); d = ImageDraw.Draw(W)
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGBA').crop(box)
    bg = Image.new('RGBA', im.size, (84, 132, 66, 255)); bg.alpha_composite(im)
    W.paste(bg.resize((w * z, h * z), Image.NEAREST), (i * w * z, 0))
    W.paste(bg, (i * w * z, h * z + 14))
    d.text((i * w * z + 2, 2), f.split('/')[-1][:-4], fill='white')
    for gx in range(0, w, 8): d.text((i * w * z + gx * z, h * z - 10), str(box[0] + gx), fill=(255, 255, 0, 160))
W.save(out)
