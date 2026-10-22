"""List orphan pixels (no same-colour 8-neighbour) per rendered pose: python _orphans.py [pose...]"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from pipeline.illustrate import render_illustration  # noqa
from poses_def import POSES  # noqa
for n in sys.argv[1:] or POSES:
    pal, idx, _, _ = render_illustration(os.path.join(HERE, n + ".json"))
    H, W = idx.shape
    pad = np.full((H + 2, W + 2), -9, int); pad[1:-1, 1:-1] = idx
    same = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                same |= pad[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx] == idx
    o = np.argwhere((idx >= 0) & ~same)
    print(n, len(o), " ".join(f"({x},{y}){pal.names[idx[y, x]]}" for y, x in o))
