"""quick zoomed strip: view.py OUT.png zoom a.png b.png ... (crop 24..112 x 28..120 on slate)"""
import sys
import numpy as np
from PIL import Image, ImageDraw
out, z = sys.argv[1], int(sys.argv[2]); fs = sys.argv[3:]
C = (24, 28, 112, 120)
w, h = (C[2]-C[0])*z, (C[3]-C[1])*z
cols = min(len(fs), 8); rows = (len(fs)+cols-1)//cols
sheet = Image.new("RGB", (cols*(w+4), rows*(h+16)), (36, 32, 44))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    im = Image.open(f).convert("RGBA")
    if im.size != (128, 128): im = im.resize((128, 128), Image.NEAREST)
    bg = Image.new("RGBA", (128, 128), (36, 32, 44, 255)); bg.alpha_composite(im)
    t = bg.crop(C).resize((w, h), Image.NEAREST)
    x, y = (i % cols)*(w+4), (i//cols)*(h+16)
    sheet.paste(t, (x, y+14)); d.text((x+2, y+1), f.split("/")[-1][:-4], fill=(220, 220, 220))
sheet.save(out)
