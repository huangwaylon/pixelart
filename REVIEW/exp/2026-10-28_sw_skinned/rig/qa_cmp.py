# qa_cmp.py OUTPREFIX : downsample the 4x matid renders to 1x (128 cell crop), palette-ish colour, side by side with the m96 masters at 4x
import sys, numpy as np
from PIL import Image
pre = sys.argv[1]; M = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_{}_96.png'
tiles = []
for v in ('S', 'E', 'SE'):
    a = np.asarray(Image.open(f'{pre}_{v}.png').convert('RGBA')); k = 4
    a = a[32 * k:160 * k, 32 * k:160 * k]
    b = a.reshape(128, k, 128, k, 4)[:, k // 2, :, k // 2]  # point sample centres
    im = Image.fromarray(b, 'RGBA'); bg = Image.new('RGBA', (128, 128), (110, 110, 110, 255)); bg.alpha_composite(im)
    m = Image.open(M.format(v)).convert('RGBA'); bm = Image.new('RGBA', (128, 128), (110, 110, 110, 255)); bm.alpha_composite(m)
    # overlay: master outline over render
    ov = np.asarray(bg).copy(); mm = np.asarray(m)[..., 3] > 0; mk = (np.asarray(m)[..., :3].sum(-1) < 80) & mm
    ov[mk] = (255, 255, 0, 255)
    for t in (bg, bm, Image.fromarray(ov)): tiles.append(t.resize((384, 384), Image.NEAREST))
W = Image.new('RGBA', (384 * 3, 384 * 3))
for i, t in enumerate(tiles): W.paste(t, ((i % 3) * 384, (i // 3) * 384))
W.crop((0, 0, 1152, 1152)).save(f'{pre}_cmp.png')
