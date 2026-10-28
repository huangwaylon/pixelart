"""S3 r3 post pass on every published sprite (logged in r3/EDITS.md): SEL-OUT on the silhouette edge.
A silhouette-edge pixel (4-touches transparency) in a mid/light tone takes its ramp's dark sel-out tone:
pink_1 -> pink_0, red_2/red_3 -> red_1, skin_1/skin_2 -> skin_0, hair_1/hair_2 -> hair_0, leather_2 -> leather_1.
Steel (blade, guard, smear cores, speed bands) and eyes are left alone (the 2 px blade keeps its steel_2 edge)."""
import glob, os, sys
import numpy as np
sys.path.insert(0, 'tools/hybrid/h4')
from common import load, save, to_chars, to_rgba
import kit
MAP = {'P': 'p', 'R': 'r', 'C': 'r', 's': 'm', 'S': 'm', 'H': 'h', 'J': 'h', 'L': 'l'}
def selout(g):
    op = g != '.'
    pad = np.pad(op, 1)
    tr = ~pad[:-2, 1:-1] | ~pad[2:, 1:-1] | ~pad[1:-1, :-2] | ~pad[1:-1, 2:]
    edge = op & tr
    out = g.copy(); n = 0
    for y, x in zip(*np.nonzero(edge)):
        c = g[y, x]
        if c in MAP: out[y, x] = MAP[c]; n += 1
    return out, n
tot = 0
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.png')) + glob.glob(os.path.join(sys.argv[1], 'bonus', '*.png'))):
    g = to_chars(load(f))
    g2, n = selout(g); g2 = kit.orphan_fix(g2)
    save(to_rgba(g2), f); tot += n
print('selout px', tot)
