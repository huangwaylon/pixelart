"""gridgif.py CLIP OUT.gif M1,M2,.. [S]: methods side by side (4x nearest, grey), labelled, clip timing"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hx
from PIL import Image, ImageDraw
clip, out, ms = sys.argv[1], sys.argv[2], sys.argv[3].split(','); s = int(sys.argv[4]) if len(sys.argv) > 4 else 4
J = json.load(open(hx.EXP + f'big/{clip}/{clip}.json'))['frames']; TW, TH = 84 * s, 114 * s; fr = []
for i in range(len(J)):
    B = Image.new('RGB', (len(ms) * TW, TH + 14), (110, 110, 110)); d = ImageDraw.Draw(B)
    for k, m in enumerate(ms):
        g = hx.read_grid(hx.EXP + f'out/{clip}/{m}/f{i:02d}.txt'); B.paste(hx.render(g[14:128, 22:106], s), (k * TW, 14)); d.text((k * TW + 3, 1), m, fill=(255, 255, 0))
    d.text((len(ms) * TW - 90, 1), f'{clip} f{i}', fill=(255, 255, 255)); fr.append(B)
fr[0].save(out, save_all=True, append_images=fr[1:], duration=[f['ms'] for f in J], loop=0, disposal=1)
