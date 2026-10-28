#!/usr/bin/env python3
"""Guide-conditioned redraw (method a for animation).

For each frame: refs = [master @8x, aligned guide @8x, previous cleaned frame @8x] -> Gemini image ->
snap (cell 8) -> palette lock -> orphan clean -> re-pivot (feet y=120 in a 128 cell) -> metrics.

Usage: redraw.py MASTER_1X GUIDE_DIR OUT_DIR [--frames 0,1,2] [--body_h 82] [--prompt-extra "..."]
Run from anywhere; uses project tools/gemini.py.
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image

ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
PX = os.path.join(ROOT, 'v2/pixel/tools')
sys.path.insert(0, PX)
import px  # noqa

S = 8                 # art-pixel scale used for every image handed to Gemini
CELL = 128
FOOT = 120
BG = (192, 192, 192)

ap = argparse.ArgumentParser()
ap.add_argument('master'); ap.add_argument('guide_dir'); ap.add_argument('out')
ap.add_argument('--frames', default=None); ap.add_argument('--body_h', type=int, default=82)
ap.add_argument('--prompt-extra', default=''); ap.add_argument('--chain', type=int, default=1,
                help='1 = also pass the previous cleaned frame as a reference')
ap.add_argument('--tag', default=''); ap.add_argument('--guide_pat', default='guide_f{:02d}.png'); ap.add_argument('--meta_name', default='meta.json')
a = ap.parse_args()
a.out = os.path.abspath(a.out); a.guide_dir = os.path.abspath(a.guide_dir)
os.makedirs(a.out, exist_ok=True)
meta = json.load(open(os.path.join(a.guide_dir, a.meta_name)))
nf = len(meta['frames'])
frames = [int(v) for v in a.frames.split(',')] if a.frames else list(range(nf))


def on_bg(im_rgba, scale):
    big = im_rgba.resize((im_rgba.width * scale, im_rgba.height * scale), Image.NEAREST)
    base = Image.new('RGBA', big.size, BG + (255,)); base.alpha_composite(big)
    return base.convert('RGB')


def bbox(arr):
    op = arr[..., 3] >= 128
    ys, xs = np.nonzero(op)
    return ys.min(), ys.max(), xs.min(), xs.max()


def aligned_guide(i):
    """Scale the anim strand's 4x guide so the character height matches the master, feet on the master pivot."""
    g = Image.open(os.path.join(a.guide_dir, a.guide_pat.format(i))).convert('RGBA')
    g0 = np.array(Image.open(os.path.join(a.guide_dir, a.guide_pat.format(0))).convert('RGBA'))
    y0, y1, _, _ = bbox(g0)                          # body height of the guide character (frame 0, 4x)
    k = a.body_h / ((y1 - y0 + 1) / 4.0) * S / 4.0   # guide is 4x
    gs = g.resize((int(g.width * k), int(g.height * k)), Image.BILINEAR)
    px0, py0 = meta['pivot']                         # 1x pivot in the 96x80 cell
    canvas = Image.new('RGBA', (CELL * S, CELL * S), BG + (255,))
    ox = int(CELL * S / 2 - px0 * 4 * k); oy = int((FOOT + 1) * S - py0 * 4 * k)
    canvas.alpha_composite(gs, (ox, oy)) if ox >= 0 and oy >= 0 else canvas.paste(gs, (ox, oy), gs)
    return canvas.convert('RGB')


master = Image.open(a.master).convert('RGBA')
mpath = os.path.join(a.out, '_ref_master8x.png'); on_bg(master, S).save(mpath)
prev = None
log = []
PROMPT = (
    "Image 1 is the MASTER pixel-art sprite of our character (chibi swordswoman, dark hair, red bow with bun, "
    "red kimono, dark obi, dark boots, katana). Image 2 is a rough 3D POSE GUIDE (ignore its colours, face, "
    "hair shape and proportions - use it ONLY for body pose, limb positions, sword position/angle, lean and "
    "squash/stretch). {prev}"
    "Redraw the MASTER character in exactly the pose of image 2, as TRUE PIXEL ART at exactly the same pixel "
    "scale as image 1 (each art pixel = one 8x8 block, identical block size and grid), same canvas size, same "
    "position (feet on the same ground line, body centred the same), same proportions, same head size, same "
    "palette and the same 1-pixel dark outline, same flat cel shading with light from the top-left. Keep the "
    "face, eyes, bow, bun and hair silhouette identical to image 1 (only rotate/shift them as the pose requires). "
    "No anti-aliasing, no blur, no gradients, no new colours, no extra details. Plain flat light grey (#c0c0c0) "
    "background only. {extra}")
for i in frames:
    gpath = os.path.join(a.out, f'_guide{a.tag}_f{i:02d}.png'); aligned_guide(i).save(gpath)
    refs = [mpath, gpath]
    ptxt = ''
    if prev is not None and a.chain:
        ppath = os.path.join(a.out, f'_prev{a.tag}_f{i:02d}.png'); on_bg(prev, S).save(ppath); refs.append(ppath)
        ptxt = ("Image 3 is the PREVIOUS animation frame already cleaned - match its colours, hair, bow and "
                "face exactly so the animation does not flicker. ")
    raw = os.path.join(a.out, f'raw{a.tag}_f{i:02d}.png')
    prompt = PROMPT.format(prev=ptxt, extra=a.prompt_extra)
    r = subprocess.run([os.path.join(ROOT, '.venv/bin/python'), os.path.join(ROOT, 'tools/gemini.py'), 'image',
                        prompt, raw] + refs, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(raw):
        print('FAIL', i, r.stdout[-300:], r.stderr[-300:]); continue
    im = Image.open(raw).convert('RGBA')
    sx, sy = im.width / (CELL * S), im.height / (CELL * S)
    sn = os.path.join(a.out, f'snap{a.tag}_f{i:02d}.png')
    px.snap(raw, sn, ['--w', str(CELL), '--h', str(CELL)])
    q = os.path.join(a.out, f'q{a.tag}_f{i:02d}.png'); px.quant(sn, q)
    c = os.path.join(a.out, f'c{a.tag}_f{i:02d}.png'); px.clean(q, c)
    fin = os.path.join(a.out, f'f{a.tag}_f{i:02d}.png')
    Image.open(c).save(fin)                     # keep Gemini's placement (it follows the guide pivot)
    prev = Image.open(fin).convert('RGBA')
    y0, y1, x0, x1 = bbox(np.array(prev))
    log.append({'f': i, 'out_size': im.size, 'scale_err': round(max(abs(sx - 1), abs(sy - 1)), 3),
                'h': int(y1 - y0 + 1), 'w': int(x1 - x0 + 1)})
    print('frame', i, log[-1], flush=True)
json.dump(log, open(os.path.join(a.out, f'log{a.tag}.json'), 'w'), indent=1)
