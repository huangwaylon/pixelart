"""strip.py CLIP OUT.png M1,M2,... : rows = methods, cols = frames (crop x22..106 y14..128), 3x nearest, grey bg"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hx
from PIL import Image, ImageDraw
clip, out, ms = sys.argv[1], sys.argv[2], sys.argv[3].split(','); s = int(os.environ.get('S', '3'))
n = len(json.load(open(hx.EXP + f'big/{clip}/{clip}.json'))['frames']); TW, TH = 84 * s, 114 * s
B = Image.new('RGB', (n * TW + 130, len(ms) * TH), (110, 110, 110)); d = ImageDraw.Draw(B)
for r, m in enumerate(ms):
    d.text((4, r * TH + 4), m, fill=(255, 255, 0))
    for i in range(n):
        g = hx.read_grid(hx.EXP + f'out/{clip}/{m}/f{i:02d}.txt'); B.paste(hx.render(g[14:128, 22:106], s), (130 + i * TW, r * TH))
B.save(out)
