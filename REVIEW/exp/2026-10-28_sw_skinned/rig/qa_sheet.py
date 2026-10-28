# qa_sheet.py DIR STEM COLS OUT [crop=x0,y0,x1,y1 in 1x 192-cell px] : labelled contact sheet of <STEM>_fNN_pv.png frames
import sys, json, glob
from PIL import Image, ImageDraw
d, stem, cols, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
cr = [int(x) for x in sys.argv[5].split(',')] if len(sys.argv) > 5 else [40, 30, 152, 160]
info = json.load(open(f'{d}/{stem}.json')); M = None
try: M = json.load(open(sys.argv[6]))
except Exception: pass
ims = []
for f in info['frames']:
    a = Image.open(f"{d}/{stem}_f{f['i']:02d}_pv.png").convert('RGBA'); k = a.size[0] // 192
    a = a.crop(tuple(c * k for c in cr)); bg = Image.new('RGBA', a.size, (110, 110, 110, 255)); bg.alpha_composite(a); ims.append(bg.convert('RGB'))
w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (w * cols, (h + 16) * rows), (40, 40, 44)); dr = ImageDraw.Draw(S)
for i, im in enumerate(ims):
    x, y = (i % cols) * w, (i // cols) * (h + 16); S.paste(im, (x, y + 16))
    lab = (M['frames'][info['frames'][i]['i']].get('key') if M else None) or f"f{info['frames'][i]['i']:02d}"
    dr.text((x + 4, y + 2), lab, fill=(240, 230, 120))
S.save(out)
