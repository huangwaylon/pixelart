#!/usr/bin/env python3
"""Guide-conditioned Gemini redraw for the E strand (adapted from v2/pixel/anim/redraw.py).

refs = [master @8x on grey, anim-strand 4x shaded guide scaled to master height @8x, (extra refs)]
-> gemini image -> snap to 128x128 -> palette lock -> orphan clean.  No chaining (rule: never pass prev frame).

Usage: redraw_E.py MASTER_1X GUIDE_DIR OUT_DIR [--frames 0,1] [--n 2] [--extra ref.png,...] [--prompt-extra ..]
       [--prompt FILE] [--tag T] [--jobs 4]
GUIDE_DIR = v2/anim/guides/<action>_E (fNN_shade4x.png + frames.json, pivot in 1x cell coords).
Outputs OUT/c{tag}_fNN_vK.png (clean 1x), raw/snap/q intermediates, _guide{tag}_fNN.png.
"""
import argparse, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image

ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, os.path.join(ROOT, 'v2/pixel/tools'))
import px  # noqa

S, CELL, FOOT, BG = 8, 128, 120, (192, 192, 192)
ap = argparse.ArgumentParser()
ap.add_argument('master'); ap.add_argument('guide_dir'); ap.add_argument('out')
ap.add_argument('--frames', default=None); ap.add_argument('--n', type=int, default=1)
ap.add_argument('--extra', default=''); ap.add_argument('--prompt-extra', default='')
ap.add_argument('--prompt', default=None); ap.add_argument('--tag', default='')
ap.add_argument('--jobs', type=int, default=4); ap.add_argument('--guide-glob', default='f{:02d}_shade4x.png')
a = ap.parse_args()
a.out = os.path.abspath(a.out); a.guide_dir = os.path.abspath(a.guide_dir)
os.makedirs(a.out, exist_ok=True)
meta = json.load(open(os.path.join(a.guide_dir, 'frames.json')))
nf = len(meta['frames'])
frames = [int(v) for v in a.frames.split(',')] if a.frames else list(range(nf))


def on_bg(im, scale):
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    base = Image.new('RGBA', big.size, BG + (255,)); base.alpha_composite(big)
    return base.convert('RGB')


def bbox(arr):
    ys, xs = np.nonzero(arr[..., 3] >= 128)
    return ys.min(), ys.max(), xs.min(), xs.max()


master = Image.open(a.master).convert('RGBA')
my0, my1, mx0, mx1 = bbox(np.array(master))
body_h = my1 - my0 + 1
g0 = np.array(Image.open(os.path.join(a.guide_dir, a.guide_glob.format(0))).convert('RGBA'))
gy0, gy1, _, _ = bbox(g0)
k = body_h / ((gy1 - gy0 + 1) / 4.0) * S / 4.0     # guide px (4x) -> 8x art scale


def aligned_guide(i):
    g = Image.open(os.path.join(a.guide_dir, a.guide_glob.format(i))).convert('RGBA')
    gs = g.resize((int(g.width * k), int(g.height * k)), Image.BILINEAR)
    p0x, p0y = meta['pivot']
    canvas = Image.new('RGBA', (CELL * S, CELL * S), BG + (255,))
    ox = int(CELL * S / 2 - p0x * 4 * k); oy = int((FOOT + 1) * S - p0y * 4 * k)
    canvas.paste(gs, (ox, oy), gs)
    return canvas.convert('RGB')


mpath = os.path.join(a.out, '_ref_master8x.png'); on_bg(master, S).save(mpath)
extras = [p for p in a.extra.split(',') if p]
PROMPT = open(a.prompt).read() if a.prompt else (
    "Image 1 is the MASTER pixel-art sprite of our character (chibi swordswoman: near-black bob hair with bangs, "
    "small bun at the back of the head, big red two-loop bow on top, big low-set blue eyes, red kimono dress with "
    "wide sleeves, dark obi sash, black boots, katana). Image 2 is a rough 3D POSE GUIDE seen from the side "
    "(facing right). Ignore its colours, face, hair shape and proportions; use it ONLY for body pose, facing "
    "direction, limb positions, sword position/angle, lean and squash/stretch. "
    "Redraw the MASTER character in exactly the pose and facing of image 2, as TRUE PIXEL ART at exactly the same "
    "pixel scale as image 1 (each art pixel = one 8x8 block, identical grid), same canvas size, feet on the same "
    "ground line, same proportions and head size, same palette, same 1-pixel dark outline, same flat cel shading "
    "with light from the top-left. No anti-aliasing, no blur, no gradients, no new colours, no extra details, no "
    "text. Plain flat light grey (#c0c0c0) background only. {extra}")


def job(i, v):
    gpath = os.path.join(a.out, f'_guide{a.tag}_f{i:02d}.png')
    if not os.path.exists(gpath):
        aligned_guide(i).save(gpath)
    raw = os.path.join(a.out, f'raw{a.tag}_f{i:02d}_v{v}.png')
    r = subprocess.run([os.path.join(ROOT, '.venv/bin/python'), os.path.join(ROOT, 'tools/gemini.py'), 'image',
                        PROMPT.format(extra=a.prompt_extra), raw, mpath, gpath] + extras,
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(raw):
        return f'FAIL f{i} v{v} {r.stdout[-200:]} {r.stderr[-200:]}'
    sn = raw.replace('raw', 'snap'); px.snap(raw, sn, ['--w', str(CELL), '--h', str(CELL)])
    q = raw.replace('raw', 'q'); px.quant(sn, q)
    c = raw.replace('raw', 'c'); px.clean(q, c)
    return f'ok f{i} v{v} {Image.open(raw).size}'


for f in frames:   # write guides first (no race)
    gp = os.path.join(a.out, f'_guide{a.tag}_f{f:02d}.png')
    aligned_guide(f).save(gp)
with ThreadPoolExecutor(a.jobs) as ex:
    for res in ex.map(lambda t: job(*t), [(i, v) for i in frames for v in range(a.n)]):
        print(res, flush=True)
