#!/bin/zsh
# r2_all.sh [acts] [views] : R round-2 renders -> render/out/r2/<act>/ : 8x passes (guide,lum,dep,tex,lid) + preview + R QA chain (r_qa_chain.py)
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
ACTS=(${=1:-walk idle run jump}); VIEWS=(${=2:-SE E S})
for a in $ACTS; do for v in $VIEWS; do
  [ -f $EXP/motion/$a.json ] || continue
  o=$EXP/render/out/r2/$a; mkdir -p $o
  $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $EXP/motion/$a.json $v $o --preview --no-post 2>&1 | grep -E "RENDERED|rror"
  $PY $EXP/render/pixel_chain_r1.py $o/${a}_$v.json >/dev/null 2>&1; mv -f $o/${a}_${v}_preview.gif $o/${a}_${v}_preview.gif 2>/dev/null
  $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $EXP/motion/$a.json $v $o --no-post 2>&1 | grep -E "RENDERED|rror"
  $PY $EXP/render/r_qa_chain.py $o/${a}_$v.json 2>&1 | grep -E "^full|rror"
done; done
echo R2_DONE
