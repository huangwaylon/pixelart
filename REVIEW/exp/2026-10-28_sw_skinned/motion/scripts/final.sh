#!/bin/zsh
# final.sh [acts] : full pixel renders (SE, +head stamp) + preview gifs (SE/E/S) + OLD|NEW side-by-side + pxeval seq -> motion/out/
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned; M=$EXP/motion; O=$M/out; mkdir -p $O
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python
PX=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
ACTS=($@); [[ ${#ACTS} -eq 0 ]] && ACTS=(walk run idle jump); for a in $ACTS; do
  $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $M/$a.json SE $M/prev/px/$a --stamp 2>&1 | grep -E "^full" | tail -1
  cp $M/prev/px/$a/${a}_SE_hs_4x.gif $O/${a}_SE_px4x.gif; cp $M/prev/px/$a/${a}_SE_hs_sheet.png $O/${a}_SE_px_sheet.png
  for v in SE E S; do
    $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $M/$a.json $v $M/prev/rig/$a --preview >/dev/null 2>&1
    cp $M/prev/rig/$a/${a}_${v}_preview.gif $O/${a}_${v}_preview.gif
  done
  [ $a != jump ] && $PY $M/scripts/mcompare.py $a $O/${a}_SE_px4x.gif $O/cmp_${a}_SE_old_vs_new.gif
  (cd /Users/waylonhuang/Documents/other/pixelart && $PX -I pipeline/tools/pxeval.py seq $M/prev/px/$a/${a}_SE_px_hs --json $O/pxeval_${a}_SE.json > /dev/null 2>&1)
done
echo FINAL_DONE
