import sys; sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair')
from probe import sprite
from PIL import Image, ImageDraw, ImageFont
D = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hair/'; V = ['front', 'iso_SE', 'iso_E']
N = dict(a='(a) black thigh-highs (zettai ryouiki)', b='(b) dark opaque tights', c='(c) knee-high socks', d='(d) longer skirt + thigh-highs')
fnt = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 20); IH = 260; RH = IH + 34; BG = (110, 110, 118)
rows = []
for L in 'abcd':
    R = Image.new('RGB', (1600, RH), (235, 235, 238)); d = ImageDraw.Draw(R); d.text((8, 4), N[L], fill='black', font=fnt); x = 8
    for v in V:
        im = Image.open(f'{D}legs/{L}_{v}.png').convert('RGB'); im = im.resize((int(im.width*IH/im.height), IH), Image.LANCZOS); R.paste(im, (x, 30)); x += im.width + 4
    x += 8; d.rectangle([x-4, 28, 1596, RH-2], fill=BG)
    for v in V:
        s64, s80 = sprite(f'{D}legs/{L}_{v}.png', 64), sprite(f'{D}legs/{L}_{v}.png', 80)
        for s in (s64, s80):
            s3 = s.resize((s.width*3, s.height*3), Image.NEAREST); R.paste(s3, (x, 30 + IH - s3.height), s3); x += s3.width + 4
        R.paste(s64, (x, 30 + IH - 64), s64); x += s64.width + 2; R.paste(s80, (x, 30 + IH - 80), s80); x += s80.width + 14
    rows.append((R, x))
W = min(1600, max(x for _, x in rows) + 8); B = Image.new('RGB', (W, RH*4 + 24), (235, 235, 238))
for k, (R, _) in enumerate(rows): B.paste(R.crop((0, 0, W, RH)), (0, k*RH))
ImageDraw.Draw(B).text((8, RH*4 + 2), 'illustration: front / iso_SE / iso_E    probes per view: 64px@3x, 80px@3x, 64px@1x, 80px@1x', fill='black', font=fnt)
B.save(D + 'legs_board.png'); t = B.copy(); t.thumbnail((800, 800)); t.save(D + 'legs_board_thumb.png'); print(B.size, [x for _, x in rows])
