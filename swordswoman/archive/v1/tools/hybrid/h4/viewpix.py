"""view .pix / png files side by side at zoom: viewpix.py OUT.png [--z 8] files..."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import read_grid, to_rgba, load, strip
import numpy as np
args = sys.argv[1:]; out = args.pop(0); z = 8
if args and args[0] == '--z': z = int(args[1]); args = args[2:]
ims = []
for f in args:
    a = to_rgba(read_grid(f)) if f.endswith('.pix') else load(f)
    ims.append(a)
    if f.endswith('.pix'):
        g = read_grid(f); hair = np.isin(g, list('hHJ')).sum()
        if hair: print(os.path.basename(f), g.shape, {c: round(float((g == c).sum()) / hair, 2) for c in 'hHJ'})
strip(ims, z=z, labels=[os.path.basename(f) for f in args], grid=False).save(out)
