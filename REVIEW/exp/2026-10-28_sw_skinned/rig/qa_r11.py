"""qa_r11.py DIR OUT : rig-preview face-integrity sheet: head crops (preview, 4x of the 192 cell) for walk SE x8, walk E x8, idle SE x12"""
import sys, json
from PIL import Image, ImageDraw
D, OUT = sys.argv[1], sys.argv[2]; rows = [('walk', 'SE', 8), ('walk', 'E', 8), ('idle', 'SE', 12)]; T = 170
W = Image.new('RGB', (T * 12, (T + 16) * 3), (40, 40, 44)); d = ImageDraw.Draw(W)
for j, (a, v, n) in enumerate(rows):
    info = json.load(open(f'{D}/{a}_{v}.json'))
    for i in range(n):
        im = Image.open(f'{D}/{a}_{v}_f{i:02d}_pv.png').convert('RGBA'); k = im.size[0] // 192; hx_, hy_ = info['frames'][i]['pts']['head']
        c = im.crop((int((hx_ - 22) * k), int((hy_ - 26) * k), int((hx_ + 22) * k), int((hy_ + 18) * k))).resize((T, T)); bg = Image.new('RGBA', c.size, (110, 110, 110, 255)); bg.alpha_composite(c)
        W.paste(bg.convert('RGB'), (i * T, j * (T + 16) + 16)); d.text((i * T + 3, j * (T + 16) + 2), f"{a} {v} f{i} [{info['frames'][i].get('proj_view')}]", fill=(240, 230, 120))
W.save(OUT); print(W.size)
