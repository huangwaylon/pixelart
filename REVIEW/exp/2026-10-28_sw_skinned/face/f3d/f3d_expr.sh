#!/bin/zsh
# f3d_expr.sh "<views>" [motion] : every expression (face/f3d/fexpr.json, 1 frame each) through R's renderer + P's part pass + P's chain,
# with the TEST fringe cut at the agreed hairline (f3d_cut.py; NOCUT=1 renders R's head as is) -> face/f3d/out/<act>/ + expression board
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
VIEWS=(${=1:-S SE E}); MOT=${2:-$EXP/face/f3d/fexpr.json}; A=${MOT:t:r}; O=$EXP/face/f3d/out/$A${NOCUT:+_nocut}
[ -n "$NOTEX" ] || $PY $EXP/face/f3d/f3d_lib.py 2>&1 | grep -v Warn
for v in $VIEWS; do
  if [ -n "$NOCUT" ]; then
    KINDS=guide,lum,dep $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $MOT $v $O --no-post 2>&1 | grep -E "rror"
    [ -f $O/parts/${A}_${v}_f00_part.png ] || $B -b $EXP/rig/rig.blend -P $EXP/render/p_parts.py -- $MOT $v $O/parts 2>&1 | grep -E "rror"
  else
    KINDS=guide,lum,dep $B -b $EXP/rig/rig.blend -P $EXP/face/f3d/f3d_cut.py -- render $MOT $v $O --no-post 2>&1 | grep -E "rror"
    [ -f $O/parts/${A}_${v}_f00_part.png ] || $B -b $EXP/rig/rig.blend -P $EXP/face/f3d/f3d_cut.py -- parts $MOT $v $O/parts 2>&1 | grep -E "rror"
  fi
  SHAPE=${SHAPE:-0} $PY $EXP/face/f3d/f3d_chain.py $O/${A}_$v.json ${CHAINF:---no-temporal} 2>&1 | grep -iE "error"
done
$PY $EXP/face/f3d/f3d_exprboard.py $O ${VIEWS[@]} 2>&1 | grep -v Warn
