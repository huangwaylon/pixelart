"""strip.py OUT.png box(x0,y0,x1,y1) z files... : zoomed crops side by side on grey, with 4px grid ticks"""
import sys
from PIL import Image, ImageDraw
out, box, z = sys.argv[1], tuple(int(v) for v in sys.argv[2].split(',')), int(sys.argv[3])
fs = sys.argv[4:]
w, h = box[2]-box[0], box[3]-box[1]
W = Image.new('RGBA', ((w*z+6)*len(fs), h*z+14), (30,30,36,255)); d = ImageDraw.Draw(W)
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGBA').crop(box)
    bg = Image.new('RGBA', im.size, (110,112,118,255)); bg.alpha_composite(im)
    X = i*(w*z+6); W.paste(bg.resize((w*z, h*z), Image.NEAREST), (X, 14))
    d.text((X+2, 1), f.split('/')[-1][:-4], fill='white')
    if z >= 6:
        for x in range(w):
            if (box[0]+x) % 8 == 0: d.line([(X+x*z, 14), (X+x*z, 18)], fill='yellow'); d.text((X+x*z+1, 16), str(box[0]+x), fill='yellow')
        for y in range(h):
            if (box[1]+y) % 8 == 0: d.line([(X, 14+y*z), (X+4, 14+y*z)], fill='yellow'); d.text((X+1, 14+y*z+1), str(box[1]+y), fill='yellow')
W.save(out)
