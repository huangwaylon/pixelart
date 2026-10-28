#!/bin/bash
# gen_final.sh view tag : turnE_final/cand/view_tag.png
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman; v=$1; t=$2; o=v2/hair/turnE_final/cand/${v}_$t.png; [ -f $o ] && exit 0
HAIR="HALF-UP hairstyle: soft dark brown-black hair to the shoulder blades, ending in 3-4 clumps with tapered pointed ends, gap between hair and neck; the top section is pulled back into a small round knot at the side-back of the crown on HER LEFT side (asymmetric), tied with a red ribbon bow with two rounded loops and two short red tails; clear side parting, soft side-swept bangs, a thin tapered side lock in front of each ear; 3 hair tones with one glossy sheen band on the crown. The knot and bow are ONLY on her left side of the head (on the right side of the picture when she faces the viewer). NOT Reimu: no frilly bow, no hair tubes"
FACE="cute Japanese anime face (Pokemon trainer / Ken Sugimori style), very large sparkling eyes, small nose, small smile, soft round cheeks"
OUT="red short kimono-dress with wide short sleeves, one grey-lavender obi sash, slender legs, dark short boots, small hands, NO sword, no weapon"
case $v in
front) W="FRONT view facing the viewer, eye level";;
left) W="STRICT 90-degree LEFT side PROFILE: her nose points at the LEFT edge of the picture, exactly one eye visible, eye level. The face profile is NOT flat: clear forehead curve, a small but definite nose bump, small lips, a soft chin and a rounded cheek contour";;
right) W="STRICT 90-degree RIGHT side PROFILE: her nose points at the RIGHT edge of the picture, exactly one eye visible, eye level; the knot and bow are on the FAR side of her head so only part of the bow peeks out behind/above the crown. The face profile is NOT flat: clear forehead curve, a small but definite nose bump, small lips, a soft chin and a rounded cheek contour";;
back) W="BACK view facing directly away, eye level; the half-up knot, bow and streamers centred on the back of the head";;
iso_S) W="FRONT view seen from a camera 30 degrees ABOVE her (top of the head and the crown sheen visible, face lower in the head, feet seen from above, body foreshortened)";;
iso_SE) W="3/4 front view turned toward the lower-RIGHT, seen from a camera 30 degrees ABOVE her (top of the head visible, obi and hem curve downward like ellipses, body foreshortened)";;
iso_E) W="STRICT 90-degree RIGHT side PROFILE (nose points at the RIGHT edge, exactly one eye visible) seen from a camera 30 degrees ABOVE her (top of the head visible, obi and hem curve downward). The face profile is NOT flat: forehead curve, small nose bump, lips, soft chin, rounded cheek contour";;
iso_NE) W="3/4 BACK view turned away toward the upper-RIGHT (face hidden, a sliver of cheek on the right), seen from a camera 30 degrees ABOVE her (top of the head, knot and bow seen from above)";;
iso_N) W="BACK view facing directly away, seen from a camera 30 degrees ABOVE her (top of the head, knot and bow seen from above, obi and hem curve downward)";;
esac
if [ $v = front ]; then
P="Character design: $FACE. Hairstyle: $HAIR. Outfit: $OUT. $W, neutral standing pose, arms slightly away from the body. The FIRST image shows the hairstyle idea to evolve. The SECOND image gives the EXACT body proportions and head size to use: slim, about 3.5 heads tall, the head must be NO bigger than in the second image. Flat cel-shaded anime style. Single full-body figure on a plain white background, no text."
R="v2/hair/opt/E_front.png v2/design/turnE/front.png"
else
P="Draw the EXACT same character as the FIRST image (same face, same hairstyle: $HAIR; same outfit: $OUT; same head size and slim proportions, same flat cel style and colours) in this view: $W. The SECOND image shows the same body in this view (match its proportions, pose and head size, but NOT its hair or bow). The THIRD image is a 3D render showing ONLY the exact camera angle. Neutral relaxed standing pose. Single full-body figure on a plain white background, no text."
R="v2/hair/turnE_final/front.png v2/design/turnE/$v.png v2/design/turnE/rigref/$v.png"
fi
for k in 1 2 3 4; do .venv/bin/python tools/gemini.py image "$P" $o $R > /dev/null 2>&1; [ -f $o ] && { mv ${o%.png}_1.png v2/hair/turnE_final/alt/ 2>/dev/null; exit 0; }; sleep 30; done
echo FAIL $v $t
