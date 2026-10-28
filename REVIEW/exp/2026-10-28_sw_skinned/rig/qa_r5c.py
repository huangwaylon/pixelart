"""qa_r5c.py : round-5b QA (cost-efficient: S/SE/E/NE only) -> rig/qa/r5c_head_QA.png : per view: master (lifted like the output) | rest + head poses at 4x"""
import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx
from PIL import Image, ImageDraw
M = json.load(open('rig/qa/r5_head.json')); keys = [f['key'] for f in M['frames']]; AL = json.load(open('rig/align.json')); V = ('S', 'SE', 'E', 'NE')
W = Image.new('RGB', (240 * (len(keys) + 1), 254 * len(V)), (40, 40, 44)); d = ImageDraw.Draw(W)
for j, v in enumerate(V):
    m = hx.read_grid(hx.SW + f'v2/m96/masters/EC0_{v}_96.txt'); L = AL[v]['lift_px']; mm = np.full_like(m, '.'); mm[:128 - L] = m[L:]
    tiles = [hx.render(mm, 4)] + [hx.render(hx.read_grid(f'rig/qa/r5c/r5_head_{v}_rq/f{i:02d}.txt'), 4) for i in range(len(keys))]
    for i, im in enumerate(tiles):
        W.paste(im.crop((140, 60, 380, 300)), (240 * i, j * 254 + 14)); d.text((240 * i + 3, j * 254 + 1), f"{v} {'master' if i == 0 else keys[i - 1]}", fill=(240, 230, 120))
W.save('rig/qa/r5c_head_QA.png'); print(W.size)
