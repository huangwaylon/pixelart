"""zoomed grid view of cells with coordinates: view.py OUT.png a.png b.png ... [--box x0,y0,x1,y1] [--z 6]"""
import sys
from PIL import Image, ImageDraw
args = sys.argv[1:]; box = (16, 24, 112, 112); z = 6
if '--box' in args: i = args.index('--box'); box = tuple(int(v) for v in args[i + 1].split(',')); del args[i:i + 2]
if '--z' in args: i = args.index('--z'); z = int(args[i + 1]); del args[i:i + 2]
out, files = args[0], args[1:]
W, H = (box[2] - box[0]) * z, (box[3] - box[1]) * z
im = Image.new('RGB', (W * len(files) + 8 * (len(files) - 1), H + 14), (20, 20, 26))
for k, f in enumerate(files):
    a = Image.open(f).convert('RGBA').crop(box)
    bg = Image.new('RGBA', a.size, (58, 62, 74, 255)); bg.alpha_composite(a)
    t = bg.resize((W, H), Image.NEAREST); d = ImageDraw.Draw(t)
    for x in range(box[0], box[2] + 1):
        if x % 8 == 0:
            d.line([((x - box[0]) * z, 0), ((x - box[0]) * z, H)], fill=(90, 90, 110)); d.text(((x - box[0]) * z + 1, 1), str(x), fill=(255, 255, 0))
    for y in range(box[1], box[3] + 1):
        if y % 8 == 0:
            d.line([(0, (y - box[1]) * z), (W, (y - box[1]) * z)], fill=(90, 90, 110)); d.text((1, (y - box[1]) * z + 1), str(y), fill=(255, 255, 0))
    im.paste(t, (k * (W + 8), 14)); ImageDraw.Draw(im).text((k * (W + 8) + 2, 1), f.split('/')[-1], fill=(255, 255, 255))
im.save(out)
