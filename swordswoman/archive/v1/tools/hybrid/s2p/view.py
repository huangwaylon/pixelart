"""view.py: zoomed crops of sprites with a pixel grid for hand polishing.
usage: view.py out.png zoom x0,y0,x1,y1 sprite.png [sprite2.png ...]"""
import sys, os
from PIL import Image, ImageDraw
out, z, box = sys.argv[1], int(sys.argv[2]), [int(v) for v in sys.argv[3].split(',')]
files = sys.argv[4:]
w, h = box[2]-box[0], box[3]-box[1]
sheet = Image.new('RGB', (len(files)*(w*z+8), h*z+16), (40, 40, 48))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGBA').crop(box)
    bg = Image.new('RGBA', im.size, (70, 70, 80, 255)); bg.alpha_composite(im)
    big = bg.resize((w*z, h*z), Image.NEAREST)
    ox = i*(w*z+8)
    sheet.paste(big, (ox, 16))
    if z >= 6 and os.environ.get("GRID", "0") == "1":
        for x in range(0, w+1):
            c = (100, 100, 110) if (box[0]+x) % 8 else (160, 160, 60)
            d.line([(ox+x*z, 16), (ox+x*z, 16+h*z)], fill=c if (box[0]+x)%8==0 else (55,55,62))
        for y in range(0, h+1):
            d.line([(ox, 16+y*z), (ox+w*z, 16+y*z)], fill=(160,160,60) if (box[1]+y)%8==0 else (55,55,62))
    d.text((ox+2, 2), f.split('/')[-1] + f' x0={box[0]} y0={box[1]}', fill=(220, 220, 220))
sheet.save(out)
