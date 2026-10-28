"""Contact sheet: sheet.py out.png [--h 512] img... (labels = filenames)"""
import sys
from PIL import Image, ImageDraw
a = sys.argv[1:]; H = 512
if '--h' in a: i = a.index('--h'); H = int(a[i+1]); del a[i:i+2]
out, imgs = a[0], a[1:]
ims = []
for p in imgs:
    im = Image.open(p).convert('RGBA'); bg = Image.new('RGBA', im.size, 'white'); bg.alpha_composite(im); im = bg.convert('RGB')
    im = im.resize((round(im.width * H / im.height), H), Image.LANCZOS); ims.append((p.split('/')[-1], im))
W = sum(i.width for _, i in ims) + 10 * (len(ims) + 1)
s = Image.new('RGB', (W, H + 30), 'white'); x = 10; d = ImageDraw.Draw(s)
for n, i in ims: s.paste(i, (x, 25)); d.text((x, 5), n, fill='black'); x += i.width + 10
s.save(out); print(out, s.size)
