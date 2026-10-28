#!/bin/zsh
# f_pchain.sh "<acts>" "<views>" : P's current chain (render_motion --no-post + p_parts + pixel_chain.py, unchanged) on the CURRENT
# motion files, into face/out/p2cur/<act>/ (F's copy, so the face anchors and P's frames come from the same pose; P's dirs untouched).
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
ACTS=(${=1:-walk run idle jump}); VIEWS=(${=2:-SE E S})
for a in $ACTS; do for v in $VIEWS; do
  o=$EXP/face/out/p2cur/$a; mkdir -p $o/parts
  $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $EXP/motion/$a.json $v $o --no-post 2>&1 | grep -E "RENDERED|rror"
  $B -b $EXP/rig/rig.blend -P $EXP/render/p_parts.py -- $EXP/motion/$a.json $v $o/parts 2>&1 | grep -E "PARTS_DONE|rror"
  $PY $EXP/render/pixel_chain.py $o/${a}_$v.json 2>&1 | grep -v Warn | tail -1
done; done
echo PCHAIN_DONE
