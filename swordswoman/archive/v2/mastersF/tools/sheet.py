# sheet.py [suffix]: v2/mastersF/sheet_4x.png = refs (Hilda/Rosa/Lyra/Dawn) + masters S SE E NE N at the same figure height
# (4x row with template mean lines + each figure's measured ticks, then 1x row), plus sheet_thumb.png (<=800 px wide).
import sys, os
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/tools'); sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/archive/v2/mastersF/tools')
import overlay, mf, verify
from landmarks import REFS
from PIL import Image
R = mf.R; V = ['S', 'SE', 'E', 'NE', 'N']; items = [(n,) + REFS[n] for n in REFS]
for v in V:
    f = R + f'mastersF/{v}.txt'
    if not os.path.exists(f): continue
    g, meta = mf.load(f); m, body, B, chin = mf.material(g, v, meta); H, mm, w, rep, bad = verify.check(v, m, body)
    mf.png(g, R + f'mastersF/{v}.png')
    rows = {k: mm.get(k) for k in overlay.ROWS}; rows['crown'] = mm['crown']; rows['sole'] = mm['sole']
    items.append((f'F_{v}', f'mastersF/{v}.png', rows, w))
P4 = overlay.panel(items, 192); P1 = overlay.panel(items, 48, tmpl=False, pad=3)
W = max(P4.width, P1.width); S = Image.new('RGB', (W, P4.height + P1.height), (96, 96, 104)); S.paste(P4, (0, 0)); S.paste(P1, (0, P4.height))
S.save(R + 'mastersF/sheet_4x.png'); t = S.resize((800, round(S.height * 800 / S.width)), Image.LANCZOS) if S.width > 800 else S
t.save(R + 'mastersF/sheet_thumb.png'); print('sheet', S.size, 'thumb', t.size)
