"""holistic strip: every action key at 1x AND 3x on grass and slate in one image: strip.py SPRITE_DIR OUT.png"""
import sys, os
from PIL import Image
d, out = sys.argv[1], sys.argv[2]
names = ['slash_SE_k0', 'slash_SE_k1', 'slash_SE_k2', 'slash_SE_k3', 'jump_E_crouch', 'jump_E_apex', 'jump_E_land',
         'walk_SE_k0', 'walk_SE_k1', 'walk_SE_k2', 'walk_SE_k3']
extra = [os.path.join(d, 'bonus', n + '.png') for n in ('run_SE_f1', 'dash_SE_f1') if os.path.exists(os.path.join(d, 'bonus', n + '.png'))]
files = [os.path.join(d, n + '.png') for n in names] + extra
box = (16, 24, 112, 112); W, H = box[2] - box[0], box[3] - box[1]
rows = []
for bg in ((84, 132, 66), (58, 62, 74)):
    for z in (1, 3):
        r = Image.new('RGBA', ((W * z + 4) * len(files), H * z), bg + (255,))
        for i, f in enumerate(files):
            a = Image.open(f).convert('RGBA').crop(box).resize((W * z, H * z), Image.NEAREST)
            r.alpha_composite(a, (i * (W * z + 4), 0))
        rows.append(r)
im = Image.new('RGBA', (max(r.width for r in rows), sum(r.height + 4 for r in rows)), (12, 12, 16, 255)); y = 0
for r in rows: im.paste(r, (0, y)); y += r.height + 4
im.save(out)
