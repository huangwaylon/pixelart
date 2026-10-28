"""mksheet.py out.png h img... : labelled row sheet, each image cropped to subject and scaled to height h"""
import sys, numpy as np
from PIL import Image, ImageDraw
out, h, imgs = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
tiles = []
for p in imgs:
    im0 = Image.open(p).convert('RGB'); im = Image.new('RGB', (im0.width + 40, im0.height + 40), 'white'); im.paste(im0, (20, 20)); x = np.array(im)  # white pad: crop past the edge was black
    m = (x.min(-1) < 215) | (x.max(-1).astype(int) - x.min(-1) > 30); ys, xs = np.where(m)
    im = im.crop((xs.min()-10, ys.min()-10, xs.max()+10, ys.max()+10))
    tiles.append((p.split('/')[-1][:-4], im.resize((round(im.width*h/im.height), h), Image.LANCZOS)))
W = sum(t.width + 10 for _, t in tiles) + 10
sh = Image.new('RGB', (W, h + 30), 'white'); d = ImageDraw.Draw(sh); x = 10
for n, t in tiles: sh.paste(t, (x, 25)); d.text((x, 5), n, fill='black'); x += t.width + 10
sh.save(out); print(out, sh.size)
