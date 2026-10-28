#!/bin/zsh
# var_render.sh name1 name2 ... : pixel (R --no-post + P parts + P chain) + smooth preview (SE, and E for run) of motion/variants/<name>.json -> motion/prev/var/<name>/
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
for a in $@; do
  f=$EXP/motion/variants/$a.json; o=$EXP/motion/prev/var/$a; mkdir -p $o/parts
  $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $f SE $o --no-post 2>&1 | grep -E "rror" | head -2
  $B -b $EXP/rig/rig.blend -P $EXP/render/p_parts.py -- $f SE $o/parts 2>&1 | grep -E "rror" | head -2
  $PY $EXP/render/pixel_chain.py $o/${a}_SE.json > $o/chain.log 2>&1
  for v in SE E; do $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $f $v $o/pv --preview >/dev/null 2>&1; done
  echo "done $a"
done
