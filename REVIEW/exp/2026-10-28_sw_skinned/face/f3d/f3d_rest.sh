#!/bin/zsh
# f3d_rest.sh "<views>" [motion] : F round-5 face test, ALL STANDARD: face/tex3d textures (f3d_lib) -> R's render_motion.py (guide/lum/dep with the
# face textures switched by the frame keys) -> P's part pass -> P's pixel_chain.py (via f3d_chain.py: face mats registered) -> board
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
VIEWS=(${=1:-S SE E}); MOT=${2:-rest}; A=${MOT:t:r}; O=$EXP/face/f3d/out/$A
[ -n "$NOTEX" ] || $PY $EXP/face/f3d/f3d_lib.py 2>&1 | grep -v Warn
for v in $VIEWS; do
  KINDS=guide,lum,dep $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $MOT $v $O --no-post ${FR:+--frames=$FR} 2>&1 | grep -E "rror"
  [ -f $O/parts/${A}_${v}_f00_part.png ] || $B -b $EXP/rig/rig.blend -P $EXP/render/p_parts.py -- $MOT $v $O/parts ${FR:+--frames=$FR} 2>&1 | grep -E "rror"
  SHAPE=${SHAPE:-0} $PY $EXP/face/f3d/f3d_chain.py $O/${A}_$v.json 2>&1 | grep -iE "error"
done
TAG=${TAG:-$A} $PY $EXP/face/f3d/f3d_board.py $EXP/face/f3d/out ${VIEWS[@]/#/$O/${A}_} 2>&1 | grep -v Warn
