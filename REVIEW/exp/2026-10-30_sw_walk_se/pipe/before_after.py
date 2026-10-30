"""before_after.py BEFORE_DIR AFTER_DIR OUTDIR [label_before] [label_after]  -- round-3 deliverable: before/after walk SE boards.
  OUTDIR/before_after_strip1x.png (2 rows, 1x), before_after_4x.png (2 rows, 4x, labelled), before_after_4x.gif (side by side, motion timing)"""
import sys, os, json
from PIL import Image, ImageDraw
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/render')
from gifio import write_gif  # noqa: E402
BG = (110, 110, 110, 255)
bd, ad, od = sys.argv[1:4]; lb = sys.argv[4] if len(sys.argv) > 4 else 'before'; la = sys.argv[5] if len(sys.argv) > 5 else 'after'
os.makedirs(od, exist_ok=True)
A = [Image.open(os.path.join(bd, f'f{i:02d}.png')).convert('RGBA') for i in range(8)]
B = [Image.open(os.path.join(ad, f'f{i:02d}.png')).convert('RGBA') for i in range(8)]
bb = [im.getbbox() for im in A + B]; box = (min(b[0] for b in bb) - 2, min(b[1] for b in bb) - 2, max(b[2] for b in bb) + 2, max(b[3] for b in bb) + 2)
w, h = box[2] - box[0], box[3] - box[1]
for s, name, lab in ((1, 'before_after_strip1x.png', 0), (4, 'before_after_4x.png', 14)):
    out = Image.new('RGBA', (w * 8 * s, (h * s + lab) * 2), BG); d = ImageDraw.Draw(out)
    for r, (row, t) in enumerate(((A, lb), (B, la))):
        for i, im in enumerate(row): out.alpha_composite(im.crop(box).resize((w * s, h * s), Image.NEAREST), (i * w * s, r * (h * s + lab) + lab))
        if lab: d.text((3, r * (h * s + lab)), t, fill=(255, 255, 0, 255))
    out.save(os.path.join(od, name))
ms = json.load(open(os.path.join(ad, 'chain.json')))['ms']; frs = []
for a, b in zip(A, B):
    c = Image.new('RGBA', (w * 2 + 4, h), BG); c.alpha_composite(a.crop(box), (0, 0)); c.alpha_composite(b.crop(box), (w + 4, 0)); frs.append(c)
write_gif(os.path.join(od, 'before_after_4x.gif'), frs, ms, bg=BG[:3], scale=4)
print('BEFORE_AFTER', od)
