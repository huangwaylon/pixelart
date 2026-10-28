import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/tools')
from blockout import render, OUT
from PIL import Image, ImageDraw
T = json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/template.json'))
HR = {'_doc': 'REPLACEABLE HEAD REGION (HAIR strand v2/hair/, FACE strand v2/face2/ own it). In blockout/<V>.txt the codes H,B,W,F,e (hair, bun, bow, face, eyes) above the chin line are placeholders. Body sections (neck row 28 down) are fixed by the template. Rows are 64-cell rows, soles on row 61 (sole line 62), crown 14.',
      'head_box': {'crown_row': 14, 'chin_line': 28, 'rows': [14, 27], 'width_px': 15, 'cols': [25, 39]},
      'latitude': {'head_h_px': T['head_latitude']['px48_head_h'], 'head_w_px': T['head_latitude']['px48_head_w'],
                   'rule': 'crown row may rise to 13 (h 15) or chin line drop to 29 (then shoulder line 30, neck 1 row). Head width (hair mass at temple/cheek level) <= 16 px (cols 24-39/40). Big anime eyes: fine inside this; keep eye centre <= 0.66 of head height down.'},
      'hair_envelope': {'top_row_incl_bow_bun': 5, 'side_cols': [22, 42], 'note': 'Free hair silhouette zone. Hair below the chin line is allowed only BEHIND the body (it must not widen shoulders >12 px or hide the neck gap / waist pinch in S,SE); ponytails/side locks may hang to row 41 (hem) outside the body only if <=2 px wide, so arms/waist still read.'},
      'body_fixed_rows': {'neck': 28, 'shoulder_line': 29, 'armpit': 32, 'obi': [34, 36], 'hip_flare_full': 39, 'hem_line': 42, 'knee_line': 48, 'boot_top': 55, 'sole_line': 62},
      'unarmed': True}
json.dump(HR, open(OUT + 'head_region.json', 'w'), indent=1)
ims = []
for v in ['S', 'SE', 'E', 'NE', 'N']:
    g = np.array([list(l.rstrip('\n')) for l in open(OUT + v + '.txt')]); im = render(g, 3).convert('RGB')
    bg = Image.new('RGB', im.size, (96, 96, 104)); bg.paste(render(g, 3), (0, 0), render(g, 3)); d = ImageDraw.Draw(bg)
    x0, x1 = 22 * 3, 43 * 3; y0, y1 = 5 * 3, 28 * 3
    for x in range(x0, x1, 6): d.line([(x, y0), (x + 3, y0)], fill=(0, 255, 255)); d.line([(x, y1), (x + 3, y1)], fill=(0, 255, 255))
    for y in range(y0, y1, 6): d.line([(x0, y), (x0, y + 3)], fill=(0, 255, 255)); d.line([(x1, y), (x1, y + 3)], fill=(0, 255, 255))
    d.text((4, 4), v, fill=(255, 255, 255)); ims.append(bg)
S = Image.new('RGB', (sum(i.width for i in ims), ims[0].height)); x = 0
for i in ims: S.paste(i, (x, 0)); x += i.width
S.save(OUT + 'sheet_3x.png'); print(S.size)
