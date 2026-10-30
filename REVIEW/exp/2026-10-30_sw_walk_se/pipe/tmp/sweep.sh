#!/bin/zsh
cd /Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-30_sw_walk_se/pipe
PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
$PY lock_chain.py work/walk_SE/walk_SE.json out/walk_SE >/dev/null && $PY export.py out/walk_SE work/walk_SE/walk_SE.json >/dev/null && $PY gates.py out/walk_SE work/walk_SE/walk_SE.json walk_lock.json out/walk_SE/walk_SE_4x.gif 2>&1 | tail -1
python3 -c "
import json; r=json.load(open('out/walk_SE/gates.json'))
print('zig',[x['zig'] for x in r['line']],'dbl',[x['dbl'] for x in r['line']],'gap',[x['gap'] for x in r['line']],'clump',[x['clump'] for x in r['line']])
for i in range(8): print(i, {k:v['flags'] for k,v in r['limbs'][i].items() if v['flags']})
"
