# sheet.py OUT.png LABEL1 PREFIX1 [LABEL2 PREFIX2 ...]
# Row per method: vcol front/side/back/se, ids se, explode front, 48px-tall downsample of the se vcol view (x4 nearest, grey bg).
import sys, os
from PIL import Image, ImageDraw
out = sys.argv[1]; rows = list(zip(sys.argv[2::2], sys.argv[3::2]))
T = 240; GREY = (128, 128, 128, 255)
def load(p):
    return Image.open(p).convert('RGBA') if os.path.exists(p) else Image.new('RGBA', (512, 512), (0, 0, 0, 0))
def px48(p):
    im = load(p); bb = im.getbbox()
    if not bb: return Image.new('RGBA', (T, T), GREY)
    c = im.crop(bb); s = 48 / c.height
    sm = c.resize((max(1, round(c.width * s)), 48), Image.BOX)
    a = sm.split()[3].point(lambda v: 255 if v > 110 else 0); sm.putalpha(a)
    cell = Image.new('RGBA', (64, 64), GREY); cell.alpha_composite(sm, ((64 - sm.width) // 2, 64 - 4 - 48))
    return cell.resize((T, T), Image.NEAREST)
cols = ['front', 'side', 'back', 'iso SE 30deg', 'parts exploded', 'rigid pose test', 'pose test side', '48px SE x4']
W = Image.new('RGBA', (120 + T * len(cols), 24 + T * len(rows)), (255, 255, 255, 255)); d = ImageDraw.Draw(W)
for j, c in enumerate(cols): d.text((120 + j * T + 6, 6), c, fill=(0, 0, 0))
for i, (lab, pre) in enumerate(rows):
    y = 24 + i * T; d.text((6, y + T // 2), lab, fill=(0, 0, 0))
    ims = [load(f'{pre}_vcol_{v}.png') for v in ('front', 'side', 'back', 'se')] + [load(f'{pre}_explode_front.png'), load(f'{pre}_pose_front.png'), load(f'{pre}_pose_side.png')]
    for j, im in enumerate(ims):
        cell = Image.new('RGBA', (512, 512), GREY); cell.alpha_composite(im.resize((512, 512)))
        W.alpha_composite(cell.resize((T, T), Image.LANCZOS), (120 + j * T, y))
    W.alpha_composite(px48(f'{pre}_vcol_se.png'), (120 + 7 * T, y))
W.convert('RGB').save(out); print(out, W.size)
