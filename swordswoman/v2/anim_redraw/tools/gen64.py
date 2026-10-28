#!/usr/bin/env python3
"""48px pipeline generator: 4 frames per Gemini call (2x2 sheet, 512px panel = 64px cell @8x).
gen64.py ACTION --groups 0,1,2,3/4,5,6,7 [--n 2] [--tag a] [--extra ".."] [--hint_file]
ref1 = master m48/SE.png @8x centred on 1024 grey; ref2 = 2x2 sheet of r6 guides (shade4x -> 8x, feet on FOOT=59).
Output split -> snap 64 -> quant -> clean -> work48/<act>/cand/<tag>fNN_kK.png"""
import argparse, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'; A = ROOT + '/v2/anim_redraw'
sys.path.insert(0, ROOT + '/v2/pixel/tools'); import px  # noqa
ap = argparse.ArgumentParser()
ap.add_argument('action'); ap.add_argument('--groups', required=True); ap.add_argument('--n', type=int, default=2)
ap.add_argument('--tag', default='a'); ap.add_argument('--extra', default='')
ap.add_argument('--master', default=A + '/m48/SE.png'); ap.add_argument('--hints', default=A + '/tools/hints48.json')
ap.add_argument('--guide', default=None); ap.add_argument('--mine', action='store_true', help='use work48/<act>/guide mannequin keys'); ap.add_argument('--sword', action='store_true')
a = ap.parse_args()
gd = f'{ROOT}/v2/anim/guides/{a.guide or a.action + "_SE"}'
meta = json.load(open(gd + '/frames.json'))
W = f'{A}/work48/{a.action}'; cd = W + '/cand'; os.makedirs(cd, exist_ok=True)
hints = json.load(open(a.hints)).get(a.action, {}) if os.path.exists(a.hints) else {}
if a.mine:
    MG = json.load(open(f'{W}/guide/frames.json'))['frames']; hints = {str(i): f['hint'] for i, f in enumerate(MG)}
BG = (192, 192, 192); FOOT = 59
m = Image.open(a.master).convert('RGBA').resize((512, 512), Image.NEAREST)
mb = Image.new('RGBA', (1024, 1024), BG + (255,)); mb.alpha_composite(m, (256, 256)); mp = f'{W}/_m8.png'
mb.convert('RGB').save(mp)
groups = [[int(v) for v in g.split(',')] for g in a.groups.split('/')]
POS = ['TOP-LEFT', 'TOP-RIGHT', 'BOTTOM-LEFT', 'BOTTOM-RIGHT']
P = ("Image 1 is the MASTER pixel-art sprite of our character (chibi girl, about 2.4 heads tall: dark bob hair with blunt "
     "bangs, back bun, big red bow on top, red short kimono-dress with wide sleeves, one dark obi band, pale legs, dark "
     "boots; NO sword, hands are tiny closed fists). Image 2 is a 2x2 sheet of rough POSE GUIDES (a flat "
     "mannequin of the same character) for 4 consecutive frames of a '{act}' animation; her near (right) arm and leg "
     "are drawn lighter, her far (left) arm and leg darker. Use them ONLY for body pose, limb positions, lean, height "
     "above the ground and squash/stretch; follow the leg positions exactly. Draw a 2x2 SPRITE SHEET with the same layout: each panel shows "
     "the MASTER character in the pose of the matching guide panel, at the same position and size as the guide figure, "
     "feet on the same ground line. Panel poses: {hints}. Requirements: TRUE PIXEL ART at exactly the same pixel scale "
     "as image 1 (each art pixel = one 8x8 block; the character is about 50 art pixels tall); the character must be "
     "IDENTICAL across the 4 panels (same big head, same sleeve length, same hem shape, same obi width, same boots, same "
     "palette) - only the pose changes; 1-pixel dark outline, flat 2-tone cel shading lit from the top-left, face toward "
     "the viewer's lower-right, both eyes visible, legs and boots clearly visible. Simple shapes, no tiny details. No "
     "anti-aliasing, no gradients, no new colours, no ground line, no shadow, no effects, no sword, no panel borders. "
     "Plain flat light grey (#c0c0c0) background. {extra}")
if a.sword:
    P = P.replace("NO sword, hands are tiny closed fists", "a katana in her near (right) fist exactly as in the guide: straight thin silver blade 2 pixels wide with a short dark hilt")
    P = P.replace("ignore their colours, face, hair, sword and proportions", "ignore their colours, face, hair and proportions")
    P = P.replace("no sword, no panel borders", "the katana exactly at the guide's angle and length, no panel borders")


def guide_panel(i):
    if a.mine:
        return Image.open(f'{W}/guide/f{i:02d}.png').convert('RGB')
    g = Image.open(f'{gd}/f{i:02d}_shade4x.png').convert('RGBA')
    g = g.resize((g.width * 2, g.height * 2), Image.NEAREST)
    px0, py0 = meta['pivot']
    c = Image.new('RGBA', (512, 512), BG + (255,))
    c.alpha_composite(g, (int((31 - px0) * 8), int((FOOT - py0 - 2) * 8)))   # idle feet row 74 = pivot+2 -> FOOT
    return c.convert('RGB')


def guide_sheet(g):
    s = Image.new('RGB', (1024, 1024), BG)
    for j, i in enumerate(g):
        s.paste(guide_panel(i), ((j % 2) * 512, (j // 2) * 512))
    return s


def job(gi, k):
    g = groups[gi]
    if all(os.path.exists(f'{cd}/{a.tag}f{i:02d}_k{k}.png') for i in g):
        return f'skip g{gi} k{k}'
    gs = f'{W}/_gs_{"-".join(map(str, g))}.png'; guide_sheet(g).save(gs)
    h = '; '.join(f'{POS[j]} = frame {i}: {hints.get(str(i), "")}' for j, i in enumerate(g))
    raw = f'{cd}/raw_{a.tag}g{"-".join(map(str, g))}_k{k}.png'
    for t in range(2):
        subprocess.run([ROOT + '/.venv/bin/python', ROOT + '/tools/gemini.py', 'image',
                        P.format(act=a.action, hints=h, extra=a.extra), raw, mp, gs], cwd=ROOT, capture_output=True)
        if os.path.exists(raw):
            break
    if not os.path.exists(raw):
        return f'FAIL g{gi} k{k}'
    im = Image.open(raw).convert('RGB'); w, hh = im.size
    for j, i in enumerate(g):
        c = im.crop(((j % 2) * w // 2, (j // 2) * hh // 2, (j % 2 + 1) * w // 2, (j // 2 + 1) * hh // 2))
        cp = f'{cd}/_c{a.tag}{i}_{k}.png'; c.save(cp)
        sn = cp.replace('/_c', '/_s'); q = cp.replace('/_c', '/_q')
        try:
            px.snap(cp, sn, ['--w', '64', '--h', '64']); px.quant(sn, q); px.clean(q, f'{cd}/{a.tag}f{i:02d}_k{k}.png')
        except Exception as e:
            return f'ERR g{gi} k{k} {e}'
        for f in (cp, sn, q):
            os.path.exists(f) and os.remove(f)
    return f'ok g{gi} k{k} {w}x{hh}'


if __name__ == '__main__':
    with ThreadPoolExecutor(8) as ex:
        for r in ex.map(lambda t: job(*t), [(gi, k) for gi in range(len(groups)) for k in range(a.n)]):
            print(r, flush=True)
