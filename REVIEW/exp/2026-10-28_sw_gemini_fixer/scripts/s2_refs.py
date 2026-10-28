"""Prepare Gemini references: guide crops (rig H frames, SE) on mid-grey, master 8x on grey, rig H2 rest. Fixer venv.
-> work/refs/{guide_<pose>.png, master_SE_8x.png, guide_rest.png}"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boardlib import trim, on_grey

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
O = E + 'work/refs/'; os.makedirs(O, exist_ok=True)
POSES = {'walk': 'walk_SE/s96/f00', 'run': 'run_SE/s96/f02', 'jump': 'jump_SE/s96/f04', 'throw': 'throw_SE/s96/f03',
         'crouch': 'jump_SE/s96/f01'}


def square(im, S=1024, fill=(128, 128, 128), hfrac=0.86):
    im = trim(im, 0)
    r = S * hfrac / max(im.height, im.width * 0.9)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    bg = Image.new('RGBA', (S, S), fill + (255,)); bg.alpha_composite(im.convert('RGBA'), ((S - im.width) // 2, S - im.height - int(S * 0.06)))
    return bg.convert('RGB')


for k, p in POSES.items():
    square(Image.open(SW + f'v2/hy3d/frames_H/{p}_shade.png')).save(O + f'guide_{k}.png')
square(Image.open(SW + 'v2/hy3d/rigs/H2/rest_SE/f00_shade.png')).save(O + 'guide_rest.png')
m = Image.open(SW + 'v2/m96/masters/EC0_SE_96.png')
on_grey(m.resize((1024, 1024), Image.NEAREST)).save(O + 'master_SE_8x.png')
il = Image.open(SW + 'v2/hair/turnE_final/iso_SE_fixed.png'); il.save(O + 'illus_SE.png')
print('ok')
