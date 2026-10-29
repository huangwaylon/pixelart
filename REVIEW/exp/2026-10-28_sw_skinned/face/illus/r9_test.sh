#!/bin/zsh
# r9_test.sh <tag> : rest S/SE + walk SE through R's renderer (illustration head, F's expression files) + P's part pass + P's standard chain
# -> face/illus/r9/<tag>/<act>/ ; then r9_eval.py (face_ssim vs m96 masters + board)
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
T=$1; O=$EXP/face/illus/r9/$T
for spec in "rest S" "rest SE" "$EXP/motion/walk.json SE" ${=EXTRA}; do
  m=${spec% *}; v=${spec##* }; a=${m:t:r}; o=$O/$a; mkdir -p $o/parts
  $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $m $v $o --no-post 2>&1 | grep -E "FATAL|rror"
  [ -f $o/parts/${a}_${v}_f00_part.png ] || $B -b $EXP/rig/rig.blend -P $EXP/render/p_parts.py -- $m $v $o/parts 2>&1 | grep -E "rror"
  $PY $EXP/render/pixel_chain.py $o/${a}_$v.json 2>&1 | grep -iE "error|Trace" 
done
$PY $EXP/face/illus/r9_eval.py $T 2>&1 | grep -v Warn
