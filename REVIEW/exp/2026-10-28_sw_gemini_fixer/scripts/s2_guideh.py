"""Guide figure heights (1x px of the 96 px-figure scale) for the pose guides: frames_H renders are 4x of the 192 cell."""
import json, os, numpy as np
from PIL import Image
SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hy3d/frames_H/'
E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
P = {'walk': 'walk_SE/s96/f00', 'run': 'run_SE/s96/f02', 'jump': 'jump_SE/s96/f04', 'throw': 'throw_SE/s96/f03', 'idle': 'idle_SE/s96/f00'}
out = {}
for k, p in P.items():
    a = np.array(Image.open(SW + p + '_shade.png'))[..., 3] > 0
    ys, xs = np.where(a)
    out[k] = {'h': (ys.max() - ys.min() + 1) / 4, 'w': (xs.max() - xs.min() + 1) / 4}
print(out)
json.dump(out, open(E + 'work/refs/guide_heights.json', 'w'), indent=1)
