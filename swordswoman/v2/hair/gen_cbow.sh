#!/bin/bash
# gen_cbow.sh view tag : turnE_final/cbow/<view>_<tag>.png  (centre knot+bow on midline)
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman; v=$1; t=$2; T=v2/hair/turnE_final; o=$T/cbow/${v}_$t.png; [ -f $o ] && exit 0
case $v in
front) W="she faces the viewer: the knot sits centred on the back-top of the crown, so the red bow appears exactly CENTRED above the top of her head, its two loops peeking out symmetrically on the left and right of the crown, the two short ribbon tails hidden behind the head or hanging symmetrically";;
iso_S) W="front view from above: the knot and bow are exactly CENTRED on the top/back of the crown on her midline, the two bow loops symmetric left and right, seen from slightly above";;
back) W="back view: the round knot is exactly CENTRED on the back-top of her head on the midline, with the red two-loop bow centred on it (loops symmetric left and right) and the two short ribbon tails hanging down the centre of her back hair";;
iso_N) W="back view from above: the knot and the two-loop red bow are exactly CENTRED on the back-top of the head on her midline, loops symmetric, two short tails hanging down the centre";;
left|iso_E) W="side profile: the knot and the red bow sit at the BACK-TOP of the head on her midline (the crown's back), seen from the side: the bow is seen edge-on/in profile at the back of the head, one loop toward the viewer partly overlapping the other, the tails hanging down the back; nothing on the side of the head above the ear";;
iso_SE) W="3/4 view facing the LOWER-RIGHT of the picture (keep that direction!): the knot and bow sit on her MIDLINE at the back-top of the crown, so they appear behind the top of the head, slightly toward the picture-LEFT (the back of her head), foreshortened at 30 degrees; nothing on the side of the head";;
iso_NE) W="3/4 back view turned toward the upper-right: the knot and the bow sit on her MIDLINE at the back-top of the head, centred on the back of the head as seen in this 3/4 view, loops foreshortened, tails hanging down the middle of the back hair";;
esac
P="Edit the FIRST image: keep EVERYTHING exactly the same (same view and facing direction, pose, face and expression, hair length and bangs, red kimono, obi, black thigh-high socks with the red trim, boots, colours, slim proportions, flat cel style), EXCEPT move the hair knot (bun) and the red two-loop ribbon bow from the side of her head to the CENTRE: symmetric about her midline. $W. Keep the same bow shape (two rounded loops, a small knot and two short tails) and the same red colours; the SECOND image shows the bow design. Remove any knot or bow from the side of the head. NO sword. Plain white background, no text."
R="$T/$v.png $T/front.png"
for k in 1 2 3; do .venv/bin/python tools/gemini.py image "$P" $o $R > /dev/null 2>&1; [ -f $o ] && { rm -f ${o%.png}_1.png; exit 0; }; sleep 30; done; echo FAIL $v $t
