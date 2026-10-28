#!/bin/zsh
# p2_run.sh "<acts>" "<views>" [extra pixel_chain flags] : P's round-2 pixel chain end to end -> render/out/p2/<act>/
#   R's render_motion.py --no-post (guide/lum/dep 8x passes)  +  render/p_parts.py (part-ID pass)  +  render/pixel_chain.py + round-1 baseline on the same passes (render/out/p2/r1/)
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
ACTS=(${=1:-walk run idle jump}); VIEWS=(${=2:-SE E S}); shift 2 2>/dev/null
for a in $ACTS; do for v in $VIEWS; do
  o=$EXP/render/out/p2/$a; mkdir -p $o/parts
  [ -n "$NORENDER" ] || $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- $EXP/motion/$a.json $v $o --no-post 2>&1 | grep -E "RENDERED|rror"
  [ -n "$NORENDER" ] || $B -b $EXP/rig/rig.blend -P $EXP/render/p_parts.py -- $EXP/motion/$a.json $v $o/parts 2>&1 | grep -E "PARTS_DONE|rror"
  $PY $EXP/render/pixel_chain.py $o/${a}_$v.json $@ 2>&1 | grep -v Warn | tail -2
  # round-1 chain on the same passes (baseline) -> render/out/p2/r1/<act>/
  r=$EXP/render/out/p2/r1/$a; mkdir -p $r; ln -sfn $o/parts $r/parts; rm -f $r/${a}_${v}_sheet.png; for f in $o/${a}_${v}_f??_*.png $o/${a}_${v}_rest_*.png $o/${a}_$v.json; do ln -sf $f $r/; done
  (cd $r && $PY $EXP/render/pixel_chain_r1.py ${a}_$v.json >/dev/null 2>&1)
done; done
echo P2_DONE
