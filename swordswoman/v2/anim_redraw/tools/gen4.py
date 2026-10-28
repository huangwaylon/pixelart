#!/usr/bin/env python3
"""Batch generator: 4 frames per Gemini call in a 2x2 sheet (same-image consistency).
gen4.py ACTION --groups 0,1,2,3/4,5,6,7 [--n 2] [--tag b] [--extra ".."]
ref1 = master@8x (1024^2), ref2 = 2x2 sheet of aligned r6 guides (each 512 = 128 art px @4x).
Output split 2x2 -> snap 128 -> quant -> clean -> work/<act>_SE/cand/<tag>fNN_kK.png"""
import argparse, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, ROOT + '/v2/pixel/tools'); import px  # noqa
ap = argparse.ArgumentParser()
ap.add_argument('action'); ap.add_argument('--groups', required=True); ap.add_argument('--n', type=int, default=2)
ap.add_argument('--tag', default='b'); ap.add_argument('--extra', default='')
ap.add_argument('--master', default=ROOT + '/v2/anim_redraw/master/SE_nokatana_D2.png')
ap.add_argument('--hints', default=ROOT + '/v2/anim_redraw/tools/hints.json')
a = ap.parse_args()
W = f'{ROOT}/v2/anim_redraw/work/{a.action}_SE'; cd = W + '/cand'; os.makedirs(cd, exist_ok=True)
hints = json.load(open(a.hints)).get(a.action, {})
BG = (192, 192, 192)
m = Image.open(a.master).convert('RGBA').resize((1024, 1024), Image.NEAREST)
mb = Image.new('RGBA', m.size, BG + (255,)); mb.alpha_composite(m); mp = f'{W}/_m8.png'; mb.convert('RGB').save(mp)
groups = [[int(v) for v in g.split(',')] for g in a.groups.split('/')]
POS = ['TOP-LEFT', 'TOP-RIGHT', 'BOTTOM-LEFT', 'BOTTOM-RIGHT']
P = ("Image 1 is the MASTER pixel-art sprite of our character (chibi girl: dark bob hair with bangs, back bun, big red bow, "
     "red short kimono-dress with wide sleeves, one dark obi band, pale legs, dark boots; NO sword, hands are small closed "
     "fists). Image 2 is a 2x2 sheet of rough 3D POSE GUIDES for 4 consecutive frames of a '{act}' animation (ignore their "
     "colours, face and proportions; use them ONLY for body pose, limb positions, lean and squash/stretch). Draw a 2x2 "
     "SPRITE SHEET: the same 4 panels in the same layout, each panel showing the MASTER character in the pose of the "
     "matching guide panel. Panel poses: {hints}. Requirements: TRUE PIXEL ART at exactly half the pixel scale of image 1 "
     "(each art pixel = one 4x4 block), each character the same size as the master would be at that scale and standing "
     "on the same ground line as its guide; the character must be IDENTICAL across the 4 panels (same head size, same "
     "sleeve length, same hem shape, same obi width, same boots, same palette) - only the pose changes; same 1-pixel dark "
     "outline, flat cel shading lit from the top-left, face toward the viewer's lower-right, both eyes visible, legs and "
     "boots clearly visible. No anti-aliasing, no gradients, no new colours, no ground line, no shadow, no effects, no "
     "panel borders. Plain flat light grey (#c0c0c0) background. {extra}")


def guide_sheet(g):
    s = Image.new('RGB', (1024, 1024), BG)
    for j, i in enumerate(g):
        gp = f'{W}/_guide_f{i:02d}.png'
        if not os.path.exists(gp):
            raise SystemExit(f'missing {gp}: run gen.py once to build aligned guides')
        s.paste(Image.open(gp).convert('RGB').resize((512, 512), Image.LANCZOS), ((j % 2) * 512, (j // 2) * 512))
    return s


def job(gi, k):
    g = groups[gi]
    if all(os.path.exists(f'{cd}/{a.tag}f{i:02d}_k{k}.png') for i in g):
        return f'skip g{gi} k{k}'
    gs = f'{W}/_gs{gi}.png'; guide_sheet(g).save(gs)
    h = '; '.join(f'{POS[j]} = frame {i}: {hints.get(str(i), "")}' for j, i in enumerate(g))
    raw = f'{cd}/raw4_{a.tag}g{gi}_k{k}.png'
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
        sn = cp.replace('_c', '_s'); q = cp.replace('_c', '_q')
        try:
            px.snap(cp, sn, ['--w', '128', '--h', '128']); px.quant(sn, q); px.clean(q, f'{cd}/{a.tag}f{i:02d}_k{k}.png')
        except Exception as e:
            return f'ERR g{gi} k{k} {e}'
        for f in (cp, sn, q):
            os.path.exists(f) and os.remove(f)
    return f'ok g{gi} k{k} {w}x{hh}'


with ThreadPoolExecutor(8) as ex:
    for r in ex.map(lambda t: job(*t), [(gi, k) for gi in range(len(groups)) for k in range(a.n)]):
        print(r, flush=True)
