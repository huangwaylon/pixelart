#!/usr/bin/env python3
"""S2_gridsheet r1 POLISH (Claude hand pixel pass).  sprite/ -> polished/
Global passes (passes.py) + per-sprite hand edits (hand.py).  Every changed pixel is logged with a
reason in polished/<stem>_polish.json."""
import json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import numpy as np
import plib, passes as P, hand
SRC = 'hybrid/S2_gridsheet/r1/sprite'
OUT = 'hybrid/S2_gridsheet/r1/polished'
BACK = ('turn_N', 'turn_NW', 'turn_NE')
NO_BLADE = ('slash_SE_k1',)
only = sys.argv[1:]
os.makedirs(OUT, exist_ok=True)
for f in sorted(os.listdir(SRC)):
    if not plib.H.is_sprite_name(f):
        continue
    stem = f[:-4]
    if only and stem not in only:
        continue
    g = plib.load(os.path.join(SRC, f)); before = g.copy(); log = []
    pre = getattr(hand, 'pre_' + stem, None)
    if pre:
        pre(g, log)
    P.blade_clean(g, log); P.despeckle(g, log); P.red_mode(g, log)
    P.hair_shade(g, log, ymax=hand.HAIR_YMAX.get(stem, 82), tJ=0.50, tH=0.62)
    P.lint_clean(g, log)
    if not stem.startswith(BACK):
        P.corset_dress(g, log, **hand.CORSET.get(stem, {}))
    if not stem.startswith(NO_BLADE):
        bl = hand.BLADE.get(stem) or P.blade_find(g)
        if bl is not None:
            P.blade_redraw(g, log, *bl)
    fn = getattr(hand, 'post_' + stem, None)
    if fn:
        fn(g, log)
    for fn in hand.FINAL:
        fn(stem, g, log)
    plib.save(g, os.path.join(OUT, f))
    src_h = os.path.join(SRC, stem + '_hires.png')
    if os.path.exists(src_h):
        shutil.copy(src_h, os.path.join(OUT, stem + '_hires.png'))
    changed = int((g != before).sum())
    json.dump({'sprite': stem, 'source': os.path.join(SRC, f), 'changed_px': changed,
               'n_ops': len(log), 'edits': log}, open(os.path.join(OUT, stem + '_polish.json'), 'w'), indent=0)
    print(f'{stem:16s} changed {changed:4d} px  ops {len(log)}')
