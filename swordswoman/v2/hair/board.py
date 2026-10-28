import sys; sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair')
from probe import sprite
from PIL import Image, ImageDraw, ImageFont
D = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair/'
NAMES = dict(A='A Twin tails + twin bows', B='B Side ponytail + big bow', C='C Hime cut + back bow', D='D Odango + short tails',
             E='E Half-up + big bow', F='F Fluffy bob + braids + bow', G='G High ponytail + bow', H='H Low pigtails (Lyra)')
ids = sys.argv[1] if len(sys.argv) > 1 else 'ABCDEFGH'; out = sys.argv[2] if len(sys.argv) > 2 else D + 'options_board.png'
try: fnt = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 20)
except Exception: fnt = None
CW, IH, BG = 400, 300, (110, 110, 118)
cols = 4; rows = (len(ids) + cols - 1) // cols; CH = 28 + IH + 8 + 48*4 + 12
B = Image.new('RGB', (CW*cols, CH*rows), (235, 235, 238)); dr = ImageDraw.Draw(B)
for n, i in enumerate(ids):
    X, Y = (n % cols) * CW, (n // cols) * CH; dr.text((X+8, Y+4), NAMES[i], fill='black', font=fnt)
    x = X + 8
    for v in ('front', 'iso_SE'):
        im = Image.open(f'{D}opt/{i}_{v}.png').convert('RGB'); im = im.resize((int(im.width*IH/im.height), IH), Image.LANCZOS)
        B.paste(im, (x, Y+28)); x += im.width + 4
    y = Y + 28 + IH + 8; dr.rectangle([X+4, y-4, X+CW-4, y+48*4+4], fill=BG); x = X + 8
    sps = [sprite(f'{D}opt/{i}_{v}.png') for v in ('front', 'iso_SE')]
    for s in sps: B.paste(s, (x, y + 48*4 - 48), s); x += s.width + 6
    for s in sps:
        s4 = s.resize((s.width*4, s.height*4), Image.NEAREST); B.paste(s4, (x, y), s4); x += s4.width + 6
B.save(out); t = B.copy(); t.thumbnail((800, 800)); t.save(out.replace('.png', '_thumb.png')); print(out, B.size, t.size)
