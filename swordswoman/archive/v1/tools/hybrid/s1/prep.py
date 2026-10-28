"""S1_redraw: build per-frame guide inputs for Gemini (mirror space). Guide only, never art."""
import json, os, sys
from PIL import Image, ImageOps
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
G = ROOT + '/hybrid/guide/p2'
OUT = ROOT + '/hybrid/S1_redraw/r1/guide_in'
DIRS = ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']
FRAMES = {}
for d in DIRS: FRAMES['turn_' + d] = f'{G}/turn/{d}/f00'
for i in range(4): FRAMES[f'walk_SE_k{i}'] = f'{G}/walk_SE_keys/SE/f0{i}'
for i in range(4): FRAMES[f'slash_SE_k{i}'] = f'{G}/slash_SE_keys/SE/f0{i}'
for i, k in enumerate(['crouch', 'apex', 'land']): FRAMES[f'jump_E_{k}'] = f'{G}/jump_E_keys/E/f0{i}'
CROP = (160, 300, 864, 1004)

def flat(p, bg=(255, 255, 255)):
    im = Image.open(p).convert('RGBA')
    b = Image.new('RGBA', im.size, bg + (255,)); b.alpha_composite(im)
    return b.convert('RGB')

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    json.dump(FRAMES, open(OUT + '/frames.json', 'w'), indent=1)
    for name, pre in FRAMES.items():
        for pas in ['clay', 'id', 'line']:
            im = flat(f'{pre}_{pas}.png').crop(CROP).resize((1024, 1024), Image.LANCZOS)
            ImageOps.mirror(im).save(f'{OUT}/{name}_{pas}_M.png')
    # mirrored lock cells
    for d in DIRS:
        ImageOps.mirror(flat(f'{ROOT}/hybrid/lock/turn/turn_{d}.png')).save(f'{OUT}/lock_{d}_M.png')
    print('ok', len(FRAMES))
