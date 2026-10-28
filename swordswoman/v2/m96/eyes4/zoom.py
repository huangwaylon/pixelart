# zoom.py SHEET OUT rowsY cells : stack chosen (row y, cells) of an eyesheet at full 8x, thumbnail <=800
import sys; from PIL import Image
im = Image.open(sys.argv[1]); ys = [int(y) for y in sys.argv[3].split(',')]; cs = [int(c) for c in sys.argv[4].split(',')]; cw = 182
o = Image.new('RGB', (cw * len(cs), 86 * len(ys)), 'white')
for j, y in enumerate(ys):
    for i, c in enumerate(cs): o.paste(im.crop((70 + c * cw, y, 70 + (c + 1) * cw, y + 86)), (i * cw, j * 86))
o.thumbnail((800, 800)); o.save(sys.argv[2]); print(o.size)
