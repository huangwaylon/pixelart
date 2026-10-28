"""Thin wrapper around Retro Diffusion's pixel-art-fixer (https://github.com/Retro-Diffusion/pixel-art-fixer).

The upstream CLI imports its old package name (`detector`), so we call the Python API directly.
Run with the fixer venv:
  .models/pixel-art-fixer/venv/bin/python -I pipeline/tools/pixelfix.py IN.png OUT.png [--step SX SY] [--json OUT.json]

Without --step: detect the pseudo-pixel grid (for "fake" pixel art, e.g. Gemini output) and rebuild 1 cell = 1 px.
With --step: skip detection and reconstruct on a known grid (e.g. a hi-res render downscaled by an exact factor).
"""
import argparse, json, os, sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.models', 'pixel-art-fixer', 'src', 'python')
sys.path.insert(0, os.path.abspath(SRC))

import numpy as np
from PIL import Image
from pixelfixer import detect
from pixelfixer.reconstruct import reconstruct


def fix(rgba, step=None):
    """Return (pixel_art_rgba, info). `step` = (sx, sy) forces the grid; otherwise it is detected."""
    h, w = rgba.shape[:2]
    if step:
        sx, sy = step
        info = {'step_x': sx, 'step_y': sy, 'cols': int(round(w / sx)), 'rows': int(round(h / sy)), 'consensus': 'forced'}
    else:
        info = detect(rgba)
    out = reconstruct(rgba, info['step_x'], info['step_y'], info['cols'], info['rows'])
    return out, {k: (float(v) if isinstance(v, (np.floating,)) else v) for k, v in info.items()
                 if isinstance(v, (int, float, str, np.integer, np.floating))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('out')
    ap.add_argument('--step', nargs=2, type=float)
    ap.add_argument('--json')
    a = ap.parse_args()
    rgba = np.array(Image.open(a.inp).convert('RGBA'))
    out, info = fix(rgba, a.step)
    Image.fromarray(out).save(a.out)
    info = {k: (int(v) if isinstance(v, np.integer) else v) for k, v in info.items()}
    print(json.dumps({'in': a.inp, 'out': a.out, **info}))
    if a.json:
        json.dump(info, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
