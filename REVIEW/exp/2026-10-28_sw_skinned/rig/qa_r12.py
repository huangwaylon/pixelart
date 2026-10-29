"""qa_r12.py : round-9 rig-preview face-integrity sheet (head crops, PVS=4): walk SE/E x8, run E x8, hurt E x9, jump E (f0-15), idle E/NE x12"""
import json
from PIL import Image, ImageDraw
D = 'rig/qa/r12'; rows = [('walk', 'SE'), ('walk', 'E'), ('run', 'E'), ('hurt', 'E'), ('jump', 'E'), ('idle', 'E'), ('idle', 'NE')]; T = 120
n = max(len(json.load(open(f'{D}/{a}_{v}.json'))['frames']) for a, v in rows)
W = Image.new('RGB', (T * n, (T + 14) * len(rows)), (40, 40, 44)); d = ImageDraw.Draw(W)
for j, (a, v) in enumerate(rows):
    info = json.load(open(f'{D}/{a}_{v}.json'))
    for k, f in enumerate(info['frames']):
        im = Image.open(f'{D}/{a}_{v}_f{f["i"]:02d}_pv.png').convert('RGBA'); s = im.size[0] // 192; hx_, hy_ = f['pts']['head']
        c = im.crop((int((hx_ - 22) * s), int((hy_ - 26) * s), int((hx_ + 22) * s), int((hy_ + 18) * s))).resize((T, T)); bg = Image.new('RGBA', c.size, (110, 110, 110, 255)); bg.alpha_composite(c)
        W.paste(bg.convert('RGB'), (k * T, j * (T + 14) + 14)); d.text((k * T + 2, j * (T + 14) + 1), f"{a}{v} f{f['i']} {f.get('proj_view')}", fill=(240, 230, 120))
W.save('rig/qa/r12_preview_integrity.png'); print(W.size)
