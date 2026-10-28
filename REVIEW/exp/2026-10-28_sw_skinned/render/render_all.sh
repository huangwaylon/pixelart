#!/bin/zsh
# render_all.sh [acts] [views] : preview + full (--stamp) for each motion/<act>.json and view -> render/out/<act>/
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender
ACTS=(${=1:-walk idle run jump}); VIEWS=(${=2:-SE E S})
for a in $ACTS; do for v in $VIEWS; do
  [ -f $EXP/motion/$a.json ] || continue
  o=$EXP/render/out/$a; mkdir -p $o
  $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $EXP/motion/$a.json $v $o --preview 2>&1 | grep -E "RENDERED|preview|rror" 
  $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $EXP/motion/$a.json $v $o --stamp 2>&1 | grep -E "RENDERED|full|rror"
done; done
echo ALL_RENDERS_DONE
