#!/bin/zsh
# r2_render.sh "<acts>" "<views>" : round-2 pixel frames of my motion with P's chain (no head stamp, so head/hair motion shows)
#   -> motion/prev/r2/<act>/  (R render --no-post + P part pass + P pixel_chain.py; also R --preview for the smooth boards)
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
ACTS=(${=1:-walk run idle jump}); VIEWS=(${=2:-SE})
for a in $ACTS; do for v in $VIEWS; do
  MD=${MDIR:-$EXP/motion}; o=$EXP/motion/prev/${OTAG:-r2}/$a; mkdir -p $o/parts
  $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $MD/$a.json $v $o --no-post 2>&1 | grep -E "rror" | head -3
  $B -b $EXP/rig/rig.blend -P $EXP/render/p_parts.py -- $MD/$a.json $v $o/parts 2>&1 | grep -E "rror" | head -3
  $PY $EXP/render/pixel_chain.py $o/${a}_$v.json 2>&1 | tail -2
  [ -z "$MDIR" ] && $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $MD/$a.json $v $EXP/motion/prev/rig/$a --preview >/dev/null 2>&1
done; done
echo R2_DONE
