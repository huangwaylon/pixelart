import sys; sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair')
from probe import sprite
from PIL import Image
D = sys.argv[1]; V = ['front', 'left', 'back', 'right', 'iso_S', 'iso_SE', 'iso_E', 'iso_NE', 'iso_N']; IH = 360
ims = [Image.open(f'{D}/{v}.png').convert('RGB') for v in V]; ims = [i.resize((int(i.width*IH/i.height), IH), Image.LANCZOS) for i in ims]
W = sum(i.width for i in ims) + 4*len(ims); S = Image.new('RGB', (W, IH + 48*4 + 16), (110, 110, 118)); x = 0
for v, i in zip(V, ims):
    S.paste(i, (x, 0)); s = sprite(f'{D}/{v}.png'); s4 = s.resize((s.width*4, s.height*4), Image.NEAREST)
    S.paste(s4, (x + (i.width - s4.width)//2, IH + 8), s4); S.paste(s, (x + 2, IH + 8 + 48*3), s); x += i.width + 4
S.save(f'{D}/sheet.png'); t = S.copy(); t.thumbnail((800, 800)); t.save(f'{D}/sheet_thumb.png'); print(S.size)
