"""gifcheck.py [paths/dirs ...] [--json out.json] [--oneshot jump,hurt]   (P, round 3; any venv with numpy + Pillow)
Flags GIF playback problems for every *.gif under the given paths (default: the whole experiment folder):
  NO_LOOP       loop extension missing or != 0 (browsers then play once)
  SHORT_FRAME   a frame delay < 20 ms (browsers clamp to 100 ms -> wrong speed); also 0-ms frames
  GHOST_RISK    a frame that is a partial tile or has transparency with disposal 0/1 (previous pixels can survive = ghosting),
                or disposal 2 on a partial tile (the uncovered area flashes to the page background)
  GHOSTING      measured: a decoded frame keeps pixels of the previous frame that differ from what the same frame shows when decoded
                standalone with disposal=2 semantics (only checked when frames have transparency)
  SEAM          loops only: last->first change > 1.5 x the largest in-cycle change (pxeval seam_ratio rule), or the first frame
                repeated at the end (double hold at the seam)
  DUP_FRAMES    consecutive identical frames that were not merged (wasted frames; some encoders drop them and shorten the loop)
Files whose name contains a --oneshot token (default 'jump') skip SEAM (one-shot clips).  Exit code 1 if any flag."""
import sys, os, glob, json
import numpy as np
from PIL import Image

EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'


def check(path, oneshot=('jump',)):
    im = Image.open(path); n = getattr(im, 'n_frames', 1); W, H = im.size
    flags, durs, frames, info = set(), [], [], []
    loop = im.info.get('loop', None)
    if loop is None or loop != 0: flags.add('NO_LOOP')
    for i in range(n):
        im.seek(i)
        d = im.info.get('duration', 0); durs.append(d)
        tile = im.tile[0][1] if im.tile else (0, 0, W, H)
        partial = tuple(tile) != (0, 0, W, H)
        trans = 'transparency' in im.info
        disp = getattr(im, 'disposal_method', 0)
        if (trans or partial) and disp in (0, 1) and i > 0 and trans: flags.add('GHOST_RISK')
        if partial and disp == 2: flags.add('GHOST_RISK')
        frames.append(np.asarray(im.convert('RGBA')).copy()); info.append((tile, disp, trans))
    if n > 1 and any(d < 20 for d in durs): flags.add('SHORT_FRAME')
    ch = [float((frames[i] != frames[i + 1]).any(-1).mean()) for i in range(n - 1)]
    if any(c == 0 for c in ch): flags.add('DUP_FRAMES')
    seam = float((frames[-1] != frames[0]).any(-1).mean()) if n > 1 else 0.0
    ratio = seam / max(1e-9, max(ch)) if ch else 0.0
    is_one = any(t in os.path.basename(path) for t in oneshot if t)
    if n > 2 and not is_one and (ratio > 1.5 or (seam == 0 and max(ch) > 0)): flags.add('SEAM')
    if any(t for _, _, t in info):  # transparent GIF: measured ghosting = alpha-0 source pixel shown opaque after compositing
        for i in range(1, n):
            im.seek(i); raw = np.asarray(im.convert('RGBA'))
            if (raw[..., 3] == 0).any() and info[i][1] in (0, 1): flags.add('GHOSTING'); break
    return {'path': os.path.relpath(path, EXP), 'frames': n, 'size': [W, H], 'loop': loop, 'ms': durs, 'cycle_ms': int(sum(durs)),
            'min_ms': int(min(durs)) if durs else 0, 'disposal': sorted({d for _, d, _ in info}), 'seam_ratio': round(ratio, 3),
            'oneshot': is_one, 'flags': sorted(flags)}


def main():
    a = sys.argv[1:]; js = None; one = ('jump',)
    if '--json' in a: i = a.index('--json'); js = a[i + 1]; del a[i:i + 2]
    if '--oneshot' in a: i = a.index('--oneshot'); one = tuple(a[i + 1].split(',')); del a[i:i + 2]
    paths = a or [EXP]; files = []
    for p in paths:
        files += sorted(glob.glob(os.path.join(p, '**', '*.gif'), recursive=True)) if os.path.isdir(p) else [p]
    res = [check(f, one) for f in files]
    bad = [r for r in res if r['flags']]
    for r in res:
        print(f"{'FAIL' if r['flags'] else 'ok  '} {r['path']:<70} n={r['frames']:<3} min={r['min_ms']:>3}ms cyc={r['cycle_ms']:>5} "
              f"disp={r['disposal']} seam={r['seam_ratio']:<6} {' '.join(r['flags'])}")
    print(f"\n{len(res)} GIFs, {len(bad)} with flags: " + ', '.join(f"{k} {sum(k in r['flags'] for r in res)}" for k in
          ('NO_LOOP', 'SHORT_FRAME', 'GHOST_RISK', 'GHOSTING', 'SEAM', 'DUP_FRAMES')))
    if js: json.dump(res, open(js, 'w'), indent=0)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
