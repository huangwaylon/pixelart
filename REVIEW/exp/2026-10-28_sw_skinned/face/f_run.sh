#!/bin/zsh
# f_run.sh "<acts>" "<views>" : F's face passes (faceless head pass + 3D face anchors, full 8x and --preview) -> face/out/<act>/,
# then the face layer on P's current frames (render/out/p2/<act>/<act>_<V>_px) + boards/GIFs, and the face-composited previews.
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
ACTS=(${=1:-walk run idle jump}); VIEWS=(${=2:-SE E S})
for a in $ACTS; do for v in $VIEWS; do
  o=$EXP/face/out/$a; mkdir -p $o/pv
  M=$EXP/motion/$a.json; [ "$a" = rest ] && M=rest
  [ -n "$NORENDER" ] || $B -b $EXP/rig/rig.blend -P $EXP/face/f_render.py -- $M $v $o 2>&1 | grep -E "FACE_DONE|MISS|rror"
  [ -n "$NORENDER$NOPV" ] || $B -b $EXP/rig/rig.blend -P $EXP/face/f_render.py -- $M $v $o/pv --preview 2>&1 | grep -E "FACE_DONE|MISS|rror"
  if [ "$a" != rest ]; then
    $PY $EXP/face/f_board.py clip $a $v 2>&1 | grep -v Warn
    [ -n "$NOPV" ] || $PY $EXP/face/f_preview.py $a $v 2>&1 | grep -v Warn
  fi
done; done
echo F_DONE
