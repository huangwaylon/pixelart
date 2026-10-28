"""gifstrip.py OUT.png a.gif b.gif ... : every GIF frame side by side (one row per GIF) with its duration"""
import sys
from PIL import Image, ImageDraw, ImageSequence
rows = []
for g in sys.argv[2:]:
    im = Image.open(g); fr = []
    for f in ImageSequence.Iterator(im): fr.append((f.convert('RGBA'), f.info.get('duration', 0)))
    rows.append(fr)
W = max(sum(f.width for f, _ in r) for r in rows); Ht = sum(r[0][0].height + 12 for r in rows)
S = Image.new('RGBA', (W, Ht), (30, 30, 36, 255)); d = ImageDraw.Draw(S); y = 0
for r in rows:
    x = 0
    for f, ms in r:
        S.paste(f, (x, y + 12)); d.text((x + 2, y), f'{ms}ms', fill='white'); x += f.width
    y += r[0][0].height + 12
S.save(sys.argv[1])
