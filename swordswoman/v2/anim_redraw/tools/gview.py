#!/usr/bin/env python3
"""gview.py OUT size img... : side-by-side resize (LANCZOS), max 1000px wide"""
import sys
from PIL import Image
out, sz, ims = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
cols = max(1, min(len(ims), 1000 // (sz + 2))); rows = (len(ims) + cols - 1) // cols
sh = Image.new('RGB', (cols * (sz + 2), rows * (sz + 2)), (40, 40, 40))
for i, p in enumerate(ims):
    im = Image.open(p).convert('RGBA'); bg = Image.new('RGBA', im.size, (110, 110, 110, 255)); bg.alpha_composite(im)
    sh.paste(bg.convert('RGB').resize((sz, sz), Image.LANCZOS if im.width > sz else Image.NEAREST), ((i % cols) * (sz + 2), (i // cols) * (sz + 2)))
sh.save(out)
