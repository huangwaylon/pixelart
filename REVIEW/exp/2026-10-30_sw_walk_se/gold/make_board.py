"""Review board + 2-frame toggle GIF for the gold frames.  Usage: make_board.py"""
import os, numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = '/Users/waylonhuang/Documents/other/pixelart'
GUIDE = ROOT + '/REVIEW/exp/2026-10-28_sw_skinned/release/out/20261030_66119a7/work/walk/SE/final/'
BG = (110, 110, 110)
cols = [('master EC0_SE_96', ROOT + '/swordswoman/v2/m96/masters/EC0_SE_96.png'),
        ('pose guide f00 (contact L)', GUIDE + 'f00_rgba.png'),
        ('pose guide f02 (passing L)', GUIDE + 'f02_rgba.png'),
        ('GOLD contact', HERE + '/walk_SE_contact.png'),
        ('GOLD passing', HERE + '/walk_SE_passing.png')]
ims = [(t, Image.open(p).convert('RGBA')) for t, p in cols]
X0, Y0, X1, Y1 = 34, 22, 94, 128          # crop for the 6x row
S = 6
tw = (X1 - X0) * S
pad, head = 10, 22
W = len(ims) * (tw + pad) + pad
H = head + 128 + 16 + (Y1 - Y0) * S + pad + 40
board = Image.new('RGB', (W, H), (60, 60, 60))
d = ImageDraw.Draw(board)
for i, (t, im) in enumerate(ims):
    x = pad + i * (tw + pad)
    d.text((x, 4), t, fill=(255, 255, 160) if t.startswith('GOLD') else (230, 230, 230))
    one = Image.new('RGB', (128, 128), BG); one.paste(im, (0, 0), im)
    board.paste(one, (x, head))
    big = one.crop((X0, Y0, X1, Y1)).resize((tw, (Y1 - Y0) * S), Image.NEAREST)
    board.paste(big, (x, head + 128 + 16))
d.text((pad, H - 34), '1x (full 128 cell) on mid-grey, then 6x crop x34-93 y22-127.  Gold = hand-authored to DESIGN_LOCK.md (14-colour lock, '
       'eyes+brows face, 1-px K outline, interior K only at listed overlaps).', fill=(220, 220, 220))
d.text((pad, H - 18), 'Pose guide = round-10 pipeline render (20261030_66119a7), shown for pose only.', fill=(220, 220, 220))
board.save(HERE + '/board_gold_walk_SE.png')

# 2-frame toggle GIF, 4x full cell on mid-grey, 400 ms per frame, infinite loop
fr = []
for t, p in cols[3:]:
    im = Image.open(p).convert('RGBA'); one = Image.new('RGB', (128, 128), BG); one.paste(im, (0, 0), im)
    big = one.resize((512, 512), Image.NEAREST)
    ImageDraw.Draw(big).text((6, 6), t.replace('GOLD ', 'gold walk SE: '), fill=(255, 255, 255))
    fr.append(big.convert('P', palette=Image.ADAPTIVE, colors=64))
fr[0].save(HERE + '/gold_toggle.gif', save_all=True, append_images=fr[1:], duration=400, loop=0, disposal=1)
# 1x toggle too (actual size)
fr1 = []
for t, p in cols[3:]:
    im = Image.open(p).convert('RGBA'); one = Image.new('RGB', (128, 128), BG); one.paste(im, (0, 0), im)
    fr1.append(one.convert('P', palette=Image.ADAPTIVE, colors=64))
fr1[0].save(HERE + '/gold_toggle_1x.gif', save_all=True, append_images=fr1[1:], duration=400, loop=0, disposal=1)
print('ok', board.size)
