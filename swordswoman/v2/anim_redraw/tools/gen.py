#!/usr/bin/env python3
"""Candidate generator: master@8x + aligned r6 guide@8x -> Gemini -> snap/quant/clean, N candidates per frame (parallel).
gen.py ACTION [--dir SE] [--frames 0,1] [--n 3] [--master PATH] [--hints hints.json] [--tag t] [--extra "..."]
Writes v2/anim_redraw/work/<action>_<dir>/cand/<tag>fNN_kK.png (1x 128 cell) + raw."""
import argparse, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, ROOT + '/v2/pixel/tools'); import px  # noqa
S, CELL, FOOT, BG = 8, 128, 120, (192, 192, 192)
ap = argparse.ArgumentParser()
ap.add_argument('action'); ap.add_argument('--dir', default='SE'); ap.add_argument('--frames')
ap.add_argument('--n', type=int, default=3); ap.add_argument('--master', default=ROOT + '/v2/pixel/master/SE_katana.png')
ap.add_argument('--hints', default=ROOT + '/v2/anim_redraw/tools/hints.json'); ap.add_argument('--tag', default='')
ap.add_argument('--extra', default=''); ap.add_argument('--body_h', type=int, default=82); ap.add_argument('--workers', type=int, default=6)
ap.add_argument('--guide', default=None, help='guide folder name override')
a = ap.parse_args()
gd = f'{ROOT}/v2/anim/guides/{a.guide or a.action + "_" + a.dir}'
meta = json.load(open(gd + '/frames.json'))
out = f'{ROOT}/v2/anim_redraw/work/{a.action}_{a.dir}'; cd = out + '/cand'; os.makedirs(cd, exist_ok=True)
frames = [int(v) for v in a.frames.split(',')] if a.frames else list(range(len(meta['frames'])))
hints = json.load(open(a.hints)).get(a.action, {}) if os.path.exists(a.hints) else {}


def on_bg(im, s):
    big = im.resize((im.width * s, im.height * s), Image.NEAREST)
    b = Image.new('RGBA', big.size, BG + (255,)); b.alpha_composite(big); return b.convert('RGB')


def bbox(arr):
    ys, xs = np.nonzero(arr[..., 3] >= 128); return ys.min(), ys.max(), xs.min(), xs.max()


def aligned_guide(i):
    g = Image.open(f'{gd}/f{i:02d}_shade4x.png').convert('RGBA')
    g0 = np.array(Image.open(f'{gd}/f00_shade4x.png').convert('RGBA')) if a.action != 'slash' else np.array(g)
    ref = f'{ROOT}/v2/anim/guides/idle_{a.dir}/f00_shade4x.png'
    g0 = np.array(Image.open(ref).convert('RGBA'))           # scale from the idle rest pose for every action
    y0, y1, _, _ = bbox(g0)
    k = a.body_h / ((y1 - y0 + 1) / 4.0) * S / 4.0
    gs = g.resize((int(g.width * k), int(g.height * k)), Image.BILINEAR)
    px0, py0 = meta['pivot']
    c = Image.new('RGBA', (CELL * S, CELL * S), BG + (255,))
    c.paste(gs, (int(CELL * S / 2 - px0 * 4 * k), int((FOOT + 1) * S - py0 * 4 * k)), gs)
    return c.convert('RGB')


master = Image.open(a.master).convert('RGBA')
mpath = f'{out}/_master8x.png'; on_bg(master, S).save(mpath)
P = ("Image 1 is the MASTER pixel-art sprite of our character (chibi swordswoman: dark bob hair with bangs, back bun, "
     "big red bow, red short kimono-dress, one dark obi, pale legs, dark boots{kat}). Image 2 is a rough 3D POSE GUIDE "
     "(ignore its colours, face, hair and proportions; use it ONLY for body pose, leg and arm positions, {swd}lean and "
     "squash/stretch). This frame: {hint}. Redraw the MASTER character in exactly the pose of image 2 as TRUE PIXEL ART at "
     "exactly the same pixel scale as image 1 (each art pixel = one 8x8 block on the same grid), same canvas, feet on the "
     "same ground line, same proportions, same head size, same palette, same 1-pixel dark outline, flat cel shading lit "
     "from the top-left. Face looks toward the viewer's lower-right like the master, both eyes visible. Legs and boots "
     "clearly visible below the hem. No anti-aliasing, no blur, no gradients, no new colours, no ground shadow, no "
     "effects. Plain flat light grey (#c0c0c0) background only. {extra}")
nok = 'nokatana' in a.master


def job(i, k):
    gp = f'{out}/_guide_f{i:02d}.png'
    if not os.path.exists(gp):
        aligned_guide(i).save(gp)
    raw = f'{cd}/raw_{a.tag}f{i:02d}_k{k}.png'
    if os.path.exists(f'{cd}/{a.tag}f{i:02d}_k{k}.png'):
        return f'skip f{i} k{k}'
    pr = P.format(kat='' if nok else ', katana in the right hand', swd='' if nok else 'sword hand position, ',
                  hint=hints.get(str(i), meta['frames'][i].get('head_tilt', '')), extra=a.extra)
    if nok:
        pr += " NO sword: the right hand is an empty closed fist exactly where the guide's sword hand is."
    for t in range(2):
        r = subprocess.run([ROOT + '/.venv/bin/python', ROOT + '/tools/gemini.py', 'image', pr, raw, mpath, gp],
                           cwd=ROOT, capture_output=True, text=True)
        if os.path.exists(raw):
            break
    if not os.path.exists(raw):
        return f'FAIL f{i} k{k}'
    sn = f'{cd}/_s.{i}.{k}{a.tag}.png'; q = sn.replace('_s.', '_q.')
    try:
        px.snap(raw, sn, ['--w', str(CELL), '--h', str(CELL)]); px.quant(sn, q)
        px.clean(q, f'{cd}/{a.tag}f{i:02d}_k{k}.png'); os.remove(sn); os.remove(q)
    except Exception as e:
        return f'ERR f{i} k{k} {e}'
    return f'ok f{i} k{k}'


with ThreadPoolExecutor(a.workers) as ex:
    for r in ex.map(lambda ik: job(*ik), [(i, k) for i in frames for k in range(a.n)]):
        print(r, flush=True)
