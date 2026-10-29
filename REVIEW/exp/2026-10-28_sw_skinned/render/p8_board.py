"""p8_board.py (P) -> render/out/p8/board_ec0_vs_chain.png: per view S/SE/E rest (+ walk SE f00/f03):
illustration (turnE_final, head crop) | m96 master | rig preview (R --preview, unlit textured head) | P pixel (final), at 4x on mid-grey."""
import sys, json
from PIL import Image, ImageDraw
ROOT = '/Users/waylonhuang/Documents/other/pixelart/'; EXP = ROOT + 'REVIEW/exp/2026-10-28_sw_skinned/'; P7 = EXP + 'render/out/p7/'; P8 = EXP + 'render/out/p8/'
sys.path.insert(0, ROOT + 'swordswoman/v2/pixelize/tools'); import pzlib as Z
BG = (128, 128, 128); S = 4; CW, CH = 80 * S, 64 * S


def on(im):
    im = im.convert('RGBA'); b = Image.new('RGBA', im.size, BG + (255,)); b.alpha_composite(im); return b.convert('RGB')


def headbox(im):
    a = im.convert('RGBA').split()[3].point(lambda v: 255 if v > 0 else 0); x0, y0, x1, y1 = a.getbbox(); h = y1 - y0
    return (x0 + x1) // 2, y0, int(0.45 * h)


def tile(im, nearest=True):
    cx, y0, hh = headbox(im); w = int(hh * CW / CH); box = (cx - w // 2, y0 - 2, cx + w // 2, y0 - 2 + hh)
    return on(im).crop(box).resize((CW, CH), Image.NEAREST if nearest else Image.LANCZOS)


rows = [('S', 'rest', 0), ('SE', 'rest', 0), ('E', 'rest', 0), ('SE', 'walk', 0), ('E', 'walk', 3), ('SE', 'idle', 6)]
B = Image.new('RGB', (7 * (CW + 6) + 70, len(rows) * (CH + 16) + 18), (40, 40, 44)); d = ImageDraw.Draw(B)
for k, t in enumerate(('illustration', 'm96 master', 'rig preview (8x colour)', 'chain (r7)', 'EC0 on render', 'per-material composite', 'chain + masters cleanup (new)')): d.text((70 + k * (CW + 6), 3), t, fill=(230, 230, 120))
for r, (V, act, fi) in enumerate(rows):
    y = 18 + r * (CH + 16); d.text((4, y + 4), f'{act} {V} f{fi:02d}', fill=(230, 230, 230))
    il = Image.open(Z.srcpath(V)).convert('RGBA')
    if il.getextrema()[3][0] == 255:  # opaque illustration: key out the white background
        px = il.load(); W_, H_ = il.size
        il = Image.eval(il, lambda v: v); a = Image.new('L', il.size, 255)
        g = il.convert('L'); a = g.point(lambda v: 0 if v > 245 else 255); il.putalpha(a)
    ims = [tile(il, False), tile(Image.open(ROOT + f'swordswoman/v2/m96/masters/EC0_{V}_96.png'))]
    ims.append(tile(Image.open(P8 + f'{act}/{act}_{V}_f{fi:02d}_pv.png'), False))
    ims.append(tile(Image.open(P8 + f'{act}/{act}_{V}_px/f{fi:02d}.png')))
    ims.append(tile(Image.open(P8 + f'{act}/{act}_{V}_ec0/f{fi:02d}.png')))
    ims.append(tile(Image.open(P8 + f'{act}/{act}_{V}_cmp/f{fi:02d}.png')))
    ims.append(tile(Image.open(P8 + f'{act}/{act}_{V}_pzc/f{fi:02d}.png')))
    for k, im in enumerate(ims): B.paste(im, (70 + k * (CW + 6), y))
B.save(P8 + 'board_r8_composite.png'); print(P8 + 'board_r8_composite.png')
