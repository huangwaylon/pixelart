"""S3 edit chain: prepare mirror-space guide refs (clay on white, fixed crop) and mirrored lock cells."""
import os, sys
from PIL import Image, ImageOps
R = 'hybrid/S3_editchain/r1/guides'
os.makedirs(R, exist_ok=True)
G = 'hybrid/guide/p2'
CROP = (182, 300, 862, 980)
MIR = {'S':'S','SE':'SW','E':'W','NE':'NW','N':'N','NW':'NE','W':'E','SW':'SE'}
items = {}
for d in MIR: items[f'turn_{d}'] = f'{G}/turn/{d}/f00'
for k in range(4): items[f'walk_SE_k{k}'] = f'{G}/walk_SE_keys/SE/f{k:02d}'
for k in range(4): items[f'slash_SE_k{k}'] = f'{G}/slash_SE_keys/SE/f{k:02d}'
for k, n in enumerate(['crouch', 'apex', 'land']): items[f'jump_E_{n}'] = f'{G}/jump_E_keys/E/f{k:02d}'
def onwhite(p):
    im = Image.open(p).convert('RGBA').crop(CROP).resize((1024, 1024), Image.LANCZOS)
    bg = Image.new('RGBA', im.size, 'white'); bg.alpha_composite(im); return bg.convert('RGB')
for name, pre in items.items():
    c = onwhite(pre + '_clay.png')
    if os.path.exists(pre + '_mask_smear.png'):
        # tint smear helper pink into the guide so Gemini sees the arc
        sm = Image.open(pre + '_mask_smear.png').convert('RGBA').crop(CROP).resize((1024, 1024))
        a = sm.getchannel('A') if sm.getchannel('A').getextrema()[1] > 0 else sm.convert('L')
        pink = Image.new('RGB', c.size, (248, 160, 190))
        c = Image.composite(pink, c, a.point(lambda v: 255 if v > 100 else 0))
    c.save(f'{R}/{name}_clay.png')
    ImageOps.mirror(c).save(f'{R}/{name}_clay_M.png')
for d in MIR:
    ImageOps.mirror(Image.open(f'hybrid/lock/turn/turn_{d}.png').convert('RGB')).save(f'{R}/lock_{d}_M.png')
print('ok', len(items))
