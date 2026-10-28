"""Pick Gemini candidates, flip mirror-space ones back to the real (LEFT-hand) space -> hires/<name>.png; then pixelize -> sprite/."""
import json, os, subprocess, sys
from PIL import Image, ImageOps
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
B = R + '/hybrid/S1_redraw/r1'
PICKS = json.load(open(B + '/picks.json'))
FR = json.load(open(B + '/guide_in/frames.json'))
os.makedirs(B + '/hires', exist_ok=True); os.makedirs(B + '/sprite', exist_ok=True)
only = sys.argv[1:]
for n, (src, space, pick) in PICKS.items():
    if only and n not in only: continue
    im = Image.open(f'{B}/gen/{src}').convert('RGB')
    if space == 'M': im = ImageOps.mirror(im); pick = None if pick is None else ('R%d' % pick)
    im.save(f'{B}/hires/{n}.png')
    cmd = [R + '/.venv/bin/python', R + '/tools/hybrid/pixelize.py', f'{B}/hires/{n}.png', '--guide', FR[n], '--out', f'{B}/sprite/{n}.png']
    if pick is not None:
        # after a mirror, figure K from the left becomes figure (N-1-K); the picks file stores the index in the FINAL image
        cmd += ['--pick', str(pick if isinstance(pick, int) else int(pick[1:]))]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=R)
    print(n, r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:] )
