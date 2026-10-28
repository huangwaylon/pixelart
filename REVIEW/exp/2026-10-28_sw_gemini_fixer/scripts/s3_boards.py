"""Step-2/3 boards. Fixer venv.
boards/b2_SE.png        illustration | master | a1/a1b/a2/a2b raw | fixer->r96 lock (4x) | 1x
boards/b3_poses.png     per pose: guide | b raw | b lock 4x (x2 samples) | c raw | c E2 4x (x2 samples)   [scale = MODE]
boards/b4_consistency.png  master + chosen pose per (b) and (c), 1x and 4x, same scale
Usage: s3_boards.py [hn|gh] [b_choice c_choice as pose=k,...]"""
import sys, os, json
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boardlib import *

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'
MODE = sys.argv[1] if len(sys.argv) > 1 else 'hn'
PR = E + f'work/proc_{MODE}/'
SC = json.load(open(PR + 'scale.json'))
ID = {d['name']: d for d in json.load(open(E + 'work/proc/identity.json'))}
MT = {d['name']: d for d in json.load(open(E + 'work/proc/metrics.json'))}
G = E + 'work/gen/'; R = E + 'work/refs/'
POSES = ['walk', 'run', 'jump', 'throw']
MASTER = Image.open(SW + 'v2/m96/masters/EC0_SE_96.png')
ILL = Image.open(SW + 'v2/hair/turnE_final/iso_SE_fixed.png')


def x4(im, k=4):
    im = trim(im, 3); return on_grey(im.resize((im.width * k, im.height * k), Image.NEAREST))


def b2():
    H = 420
    tiles = [fit(ILL, H, False), x4(MASTER), on_grey(trim(MASTER, 3))]; labs = ['illustration', 'm96 master 4x', '1x']
    for n in ['a1', 'a1b', 'a2', 'a2b']:
        m = MT.get(n + '_r96L2', {}); i = ID.get(n + '_r96L2', {})
        info = json.load(open(E + f'work/proc/{n}_info.json'))
        r = Image.open(E + f'work/proc/{n}_r96L2.png')
        tiles += [fit(Image.open(G + n + '.png'), H, False), x4(r), on_grey(trim(r, 3))]
        labs += [f'{n} raw (grid {info["step_x"]:.2f}, fig {info["fig_native_h"]}px)', f'{n} fixer->96 lock\nssim_b {m.get("ssim_b", 0):.2f} dE {m.get("dE", 0):.1f} face {m.get("face_ssim", 0):.2f}', '1x']
    top = row(tiles[:9], labs[:9], H, title='(a) SE illustration -> Gemini "true pixel art" -> pixel-art-fixer -> 96 px -> palette lock')
    bot = row(tiles[9:], labs[9:], H)
    stack([top, bot]).save(E + 'boards/b2_SE.png')


def b3():
    H = 400; rows = []
    for p in POSES:
        tiles = [fit(Image.open(R + f'guide_{p}.png'), H, False)]; labs = [f'guide {p} (rig H)']
        for kind in 'bc':
            for k in (0, 1):
                n = f'{kind}_{p}_{k}'; s = SC[n]
                im = Image.open(PR + n + ('_L2' if kind == 'b' else '') + '.png')
                tiles += [fit(Image.open(G + n + '.png'), H, False), x4(im)]
                lab2 = f'{"fixer" if kind == "b" else "E2"} h{s["h"]} 4x  hair {s["hair_h"]}px'
                labs += [f'{n} raw' + (' (pixel)' if kind == 'b' else ' (illus)'), lab2]
        rows.append(row(tiles, labs, H, title=f'{p}: (b) Gemini pixel pose -> fixer -> lock  |  (c) Gemini illustration pose -> E2   [scale={MODE}]'))
    stack(rows).save(E + f'boards/b3_poses_{MODE}.png')


def b4(choice):
    rows = []
    for kind in 'bc':
        ims = [Image.open(SW + 'v2/m96/masters/EC0_SE_96.png')] + [Image.open(PR + f'{kind}_{p}_{choice[kind][p]}' + ('_L2' if kind == 'b' else '') + '.png') for p in POSES]
        labs = ['master'] + [f'{kind}_{p}_{choice[kind][p]}' for p in POSES]
        r1 = row([x4(i) for i in ims], labs, 4 * 112, title=('(b) Gemini pixel art + fixer' if kind == 'b' else '(c) Gemini illustration + E2') + f'  4x  [scale={MODE}]')
        r2 = row([on_grey(i) for i in ims], ['1x'] * 5, 128)
        rows += [r1, r2]
    stack(rows).save(E + f'boards/b4_consistency_{MODE}.png')


if __name__ == '__main__':
    os.makedirs(E + 'boards', exist_ok=True)
    b2(); b3()
    ch = {'b': {p: 0 for p in POSES}, 'c': {p: 0 for p in POSES}}
    for a in sys.argv[2:]:
        kind, rest = a.split(':')
        for kv in rest.split(','):
            p, k = kv.split('='); ch[kind][p] = int(k)
    b4(ch)
    print('ok')
