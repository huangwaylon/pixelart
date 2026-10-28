# exprsheet.py: mastersF/heads/expr_sheet.png = rows S SE E NE N, columns neutral + 10 expressions, 4x (<=1000 px wide)
import sys, os, glob; sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/mastersF/tools'); import mf
from PIL import Image
R = mf.R + 'mastersF/heads/'; E = ['neutral', 'cheerful', 'determined', 'shout', 'effort', 'joy', 'surprised', 'pain', 'blink_half', 'blink_closed', 'embarrassed']
z = 4; cw, ch = 22 * z, 26 * z; BG = (150, 150, 160, 255); S = Image.new('RGBA', (cw * len(E), ch * 5), BG)
for j, v in enumerate(['S', 'SE', 'E', 'NE', 'N']):
    for i, e in enumerate(E):
        p = R + f'{v}_{e}.txt'
        if os.path.exists(p): g, _ = mf.load(p); im = mf.png(g, None, z); S.alpha_composite(im.crop((0, 0, min(im.width, cw), min(im.height, ch))), (i * cw, j * ch))
S.save(R + 'expr_sheet.png'); print(S.size)
