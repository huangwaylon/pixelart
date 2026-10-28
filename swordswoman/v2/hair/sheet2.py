"""sheet2.py dir : sheet.png = illustrations + 64px and 80px probes (3x) + 1x, per view"""
import sys; sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair')
from probe import sprite
from PIL import Image
D = sys.argv[1]; V = ['front', 'left', 'back', 'right', 'iso_S', 'iso_SE', 'iso_E', 'iso_NE', 'iso_N']; IH = 400
cols = []
for v in V:
    i = Image.open(f'{D}/{v}.png').convert('RGB'); i = i.resize((int(i.width*IH/i.height), IH), Image.LANCZOS)
    s64, s80 = sprite(f'{D}/{v}.png', 64), sprite(f'{D}/{v}.png', 80)
    a, b = s64.resize((s64.width*3, 192), Image.NEAREST), s80.resize((s80.width*3, 240), Image.NEAREST)
    cols.append((i, s64, s80, a, b, max(i.width, a.width + b.width + 6)))
W = sum(c[-1] + 6 for c in cols); S = Image.new('RGB', (W, IH + 240 + 100), (110, 110, 118)); x = 0
for i, s64, s80, a, b, w in cols:
    S.paste(i, (x + (w - i.width)//2, 0)); S.paste(a, (x, IH + 8 + 240 - 192), a); S.paste(b, (x + a.width + 6, IH + 8), b)
    S.paste(s64, (x + 4, IH + 260 + 80 - 64), s64); S.paste(s80, (x + 10 + s64.width, IH + 260), s80); x += w + 6
S.save(f'{D}/sheet.png'); t = S.copy(); t.thumbnail((800, 800)); t.save(f'{D}/sheet_thumb.png'); print(S.size)
