#!/usr/bin/env python3
"""Legs-only redraw + upper-body lock (for locomotion cycles whose upper body is ~rigid).

base = an approved cleaned frame (1x, 128 cell). For each frame i: Gemini gets [base @8x, aligned guide @8x] and
is asked to change ONLY legs/feet/skirt hem. Then: final = Gemini output below the cut row, and the base's
upper body (rows < cut) pasted back, shifted vertically by the guide's head bob (dy, in art px).

Usage: legs_redraw.py BASE_1X GUIDE_DIR OUT_DIR --cut ROW [--frames 1,2,..] [--tag _L]
cut = first row of the skirt (below the obi) in the base frame."""
import argparse, os, subprocess, sys, json
import numpy as np
from PIL import Image

ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, os.path.join(ROOT, 'v2/pixel/tools'))
import px  # noqa
S, CELL, BG = 8, 128, (192, 192, 192)

ap = argparse.ArgumentParser()
ap.add_argument('base'); ap.add_argument('guide_dir'); ap.add_argument('out')
ap.add_argument('--cut', type=int, required=True); ap.add_argument('--frames', default=None)
ap.add_argument('--tag', default='_L'); ap.add_argument('--prompt', default=None); ap.add_argument('--guide_png', default='_guide_nc_f{:02d}.png',
                help='aligned 8x guides already written by redraw.py into OUT_DIR')
a = ap.parse_args()
a.out = os.path.abspath(a.out)
meta = json.load(open(os.path.join(os.path.abspath(a.guide_dir), 'meta.json')))
frames = [int(v) for v in a.frames.split(',')] if a.frames else list(range(len(meta['frames'])))


def on_bg(im, s):
    big = im.resize((im.width * s, im.height * s), Image.NEAREST)
    b = Image.new('RGBA', big.size, BG + (255,)); b.alpha_composite(big); return b.convert('RGB')


def guide_top(i):
    g = np.array(Image.open(os.path.join(a.out, a.guide_png.format(i))).convert('RGB')).astype(int)
    m = np.abs(g - np.array(BG)).sum(-1) > 30
    return np.nonzero(m.any(1))[0].min() / S


base = Image.open(a.base).convert('RGBA'); B = np.array(base)
bpath = os.path.join(a.out, f'_base{a.tag}.png'); on_bg(base, S).save(bpath)
t0 = guide_top(0)
PROMPT = ("Image 1 is a finished pixel-art animation frame. Image 2 is a 3D pose guide for the next frame. "
          "EDIT image 1: change ONLY the legs, feet and the bottom edge of the skirt so the legs/feet match the "
          "stride in image 2 (which foot is forward, which is lifted, knee bend). Keep EVERYTHING above the skirt "
          "(head, hair, bow, face, arms, hands, sword, torso, obi) pixel-identical to image 1, same position. "
          "Same 8x8 pixel grid, same palette, same 1px dark outline, no anti-aliasing, plain flat light grey "
          "(#c0c0c0) background. Make the stride clear and readable: legs apart on contact frames, one leg "
          "lifted and bent on passing frames.")
if a.prompt:
    PROMPT = a.prompt
log = []
for i in frames:
    g = os.path.join(a.out, a.guide_png.format(i))
    raw = os.path.join(a.out, f'raw{a.tag}_f{i:02d}.png')
    for attempt in range(3):
        r = subprocess.run([os.path.join(ROOT, '.venv/bin/python'), os.path.join(ROOT, 'tools/gemini.py'), 'image',
                            PROMPT, raw, bpath, g], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(raw):
            print('FAIL', i, r.stdout[-200:]); continue
        sn = raw.replace('raw', 'snap'); px.snap(raw, sn, ['--w', str(CELL), '--h', str(CELL)])
        q = raw.replace('raw', 'q'); px.quant(sn, q)
        c = raw.replace('raw', 'c'); px.clean(q, c)
        C = np.array(Image.open(c).convert('RGBA'))
        low = C[a.cut + 2:]
        iris = sum(((low[..., 3] >= 128) & (low[..., :3] == np.array(px.hex2rgb(h))).all(-1)).sum()
                   for h in ('#2a395a', '#5580a2'))
        if iris == 0:
            break
        print('reject', i, 'attempt', attempt, 'iris below cut', int(iris), flush=True)
    dy = int(round(guide_top(i) - t0))
    out = C.copy()
    out[:a.cut + dy] = 0
    up = B[:a.cut]                                  # base upper body, shifted by the bob
    y0 = dy
    for y in range(a.cut):
        yy = y + y0
        if 0 <= yy < CELL:
            row = up[y]; m = row[:, 3] >= 128
            out[yy][m] = row[m]
            if yy >= a.cut + dy - 1:
                pass
    fin = raw.replace('raw', 'f'); Image.fromarray(out).save(fin)
    log.append({'f': i, 'dy': dy}); print('frame', i, 'dy', dy, flush=True)
json.dump(log, open(os.path.join(a.out, f'log{a.tag}.json'), 'w'))
