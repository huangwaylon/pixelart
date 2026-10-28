"""before | after zoom grid: cmpzoom.py OUT.png DIR_A DIR_B name... (6x, cyan 8px grid)"""
import sys
from PIL import Image, ImageDraw
out, A, Bd = sys.argv[1:4]; names = sys.argv[4:]; Z = 6; C = (16, 32, 120, 116)
w = (C[2]-C[0])*Z; h = (C[3]-C[1])*Z
s = Image.new('RGBA', (w*2, h*len(names)), (36, 32, 44, 255))
for j, n in enumerate(names):
    for i, D in enumerate((A, Bd)):
        bg = Image.new('RGBA', (w, h), (120, 120, 126, 255))
        im = Image.open(f'{D}/{n}.png').convert('RGBA').crop(C).resize((w, h), Image.NEAREST); bg.alpha_composite(im)
        d = ImageDraw.Draw(bg)
        for x in range(C[0], C[2], 8): d.line([((x-C[0])*Z, 0), ((x-C[0])*Z, h)], fill=(0, 255, 255, 70)); d.text(((x-C[0])*Z+1, 1), str(x), fill='cyan')
        for y in range(C[1], C[3], 8): d.line([(0, (y-C[1])*Z), (w, (y-C[1])*Z)], fill=(0, 255, 255, 70)); d.text((1, (y-C[1])*Z+1), str(y), fill='cyan')
        d.text((w-160, h-14), n + (' before' if i == 0 else ' after'), fill='yellow')
        s.paste(bg, (i*w, j*h))
s.save(out)
