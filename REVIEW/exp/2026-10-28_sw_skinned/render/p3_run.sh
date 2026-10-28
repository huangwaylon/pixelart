#!/bin/zsh
# p3_run.sh "<motions>" "<views>" [pixel_chain flags]   (P, round 3)  -> render/out/p3/<name>/
#   <motions>: names under motion/ (walk run idle jump) or motion/variants/ (e.g. walk_8e); <views>: any of S SE E NE N NW W SW
#   per clip: R's render_motion.py --no-post (8x guide/lum/dep/tex/lid)  +  render/p_parts.py (part + rest-position passes)
#             + face/f_render.py into <clip>/face (F's anchors + faceless head)  +  render/pixel_chain.py (chain + face layer + limb audit
#             + GIF via gifio)  ->  <name>_<V>_px/fNN.{png,txt,json}, _4x.gif, _sheet.png, _px.json, _limbs.json
#   env NORENDER=1 skips the Blender passes (re-run the chain only).  Exit status 0 always; read LIMB_AUDIT lines / *_limbs.json.
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
ACTS=(${=1:-walk run idle jump}); VIEWS=(${=2:-SE E S}); shift 2 2>/dev/null
for a in $ACTS; do for v in $VIEWS; do
  M=$EXP/motion/$a.json; [ -f $M ] || M=$EXP/motion/variants/$a.json; [ -f $M ] || { echo "no motion $a"; continue; }
  o=$EXP/render/out/p3/$a; mkdir -p $o/parts $o/face
  if [ -z "$NORENDER" ]; then
    $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $M $v $o --no-post 2>&1 | grep -E "RENDERED|rror"
    $B -b $EXP/rig/rig.blend -P $EXP/render/p_parts.py -- $M $v $o/parts 2>&1 | grep -E "PARTS_DONE|rror"
    [ -f $EXP/face/f_render.py ] && $B -b $EXP/rig/rig.blend -P $EXP/face/f_render.py -- $M $v $o/face 2>&1 | grep -E "FACE_DONE|MISS|rror"
  fi
  $PY $EXP/render/pixel_chain.py $o/${a}_$v.json $@ 2>&1 | grep -E "LIMB_AUDIT|FACE|WARN|full|rror|Trace" | cut -c1-300
done; done
echo P3_DONE
