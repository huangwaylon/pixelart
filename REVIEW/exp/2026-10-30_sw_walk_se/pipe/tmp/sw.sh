#!/bin/zsh
cd /Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-30_sw_walk_se/pipe
PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
for cfg in "$@"; do
  env ${=cfg} $PY lock_chain.py work/walk_SE/walk_SE.json tmp/sw >/dev/null 2>&1
  $PY - "$cfg" <<'P'
import sys, numpy as np
sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/docs/team_review/2026-10-30/line_art')
import lamet as LM
lab=np.load('tmp/sw/labels.npz'); z=[];d=[];m=[];c=[];gp=[]
for i in range(8):
    g=LM.load_txt(f'tmp/sw/f{i:02d}.txt'); g[lab[f'ink{i:02d}']]='s'; r=LM.metrics(g); z.append(r['zig']); d.append(r['dbl']); m.append(r['mono']); gp.append(r['gap']); c.append(r['clump'])
print(f"{sys.argv[1]:40s} zig {z} dbl {d} gap {sum(gp)} clump {sum(c)} mono {np.mean(m):.2f}")
P
done
