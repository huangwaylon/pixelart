"""qa_anchors.py OUT (STEM_JSON FRAMES)+ : pixel 4x frames (R QA chain, *_rq) with the exported face anchors drawn on top
(green = visible, red = hidden; eye/brow/mouth/cheek), plus the head yaw/pitch/roll and the lowest opaque row (cell-bottom clipping check)"""
import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx
from PIL import Image, ImageDraw
out = sys.argv[1]; args = sys.argv[2:]; tiles = []
for k in range(0, len(args), 2):
    js, frs = args[k], [int(x) for x in args[k + 1].split(',')]; info = json.load(open(js)); stem = js[:-5]
    for i in frs:
        g = hx.read_grid(f'{stem}_rq/f{i:02d}.txt'); im = hx.render(g, 4).convert('RGB'); d = ImageDraw.Draw(im)
        fa = info['frames'][i]['face']
        for n, a in fa.items():
            if n.startswith('_'): continue
            x, y = a['px'][0] * 4, a['px'][1] * 4; c = (60, 255, 60) if a['visible'] else (255, 60, 60)
            d.ellipse((x - 4, y - 4, x + 4, y + 4), outline=c, width=2)
        h = fa['_head']; low = int(np.nonzero((g != '.').any(1))[0].max())
        d.text((4, 4), f"{info['action']} f{i} yaw {h['yaw']:.0f} pitch {h['pitch']:.0f} roll {h['roll']:.0f}  lowest row {low}", fill=(255, 255, 0))
        tiles.append(im.crop((96, 0, 416, 512)))
W = Image.new('RGB', (320 * len(tiles), 512))
for j, t in enumerate(tiles): W.paste(t, (320 * j, 0))
W.save(out); print(out)
