#!/bin/bash
# gen_turn.sh ID view : turnID/view.png from opt/ID_front.png (design) + turnE/view.png (angle only)
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman; id=$1; v=$2; o=v2/hair/turn$id/$v.png; [ -f $o ] && exit 0
case $id in
A) H="long glossy dark twin tails tied high on each side of the head with two big red ribbon bows, tails falling to mid-back with a soft outward curve, soft rounded bangs, short side locks";;
D) H="two round buns (odango) on top of the head, each with a short twin tail falling to the shoulders, small red ribbon bows at each bun, soft rounded bangs, side locks";;
esac
case $v in
left) W="STRICT 90-degree LEFT side PROFILE view: her nose points at the LEFT edge of the picture, we see only the left side of her face with exactly one eye, the body is seen from the side (not from the back, not 3/4), both bun-tails seen from the side, eye level camera";;
right) W="RIGHT side profile view: she faces the RIGHT edge of the picture, true profile, one eye visible, eye level camera";;
back) W="BACK view: facing directly away from the viewer, eye level camera, back of the hair and both bows visible";;
iso_S) W="FRONT view seen from a camera 30 degrees ABOVE her (game isometric camera): top of the head visible, face slightly lower in the head, body slightly foreshortened";;
iso_E) W="STRICT 90-degree RIGHT side PROFILE (nose points at the RIGHT edge of the picture, one eye and the cheek clearly visible, body seen from its side, NOT from the back) facing the RIGHT edge of the picture (one eye visible), seen from a camera 30 degrees ABOVE her (top of the head visible, obi and hem curve downward)";;
iso_NE) W="3/4 BACK view turned away toward the upper-RIGHT (face hidden, a sliver of cheek on the right), seen from a camera 30 degrees ABOVE her (top of the head visible)";;
iso_N) W="BACK view facing directly away, seen from a camera 30 degrees ABOVE her (top of the head seen from above, obi and hem curve downward)";;
esac
P="Draw the EXACT same character as the FIRST image (same cute anime face with large eyes, same hairstyle: $H; same red short kimono-dress with wide short sleeves, grey-lavender obi, dark short boots; same proportions, flat cel style and colours) in this view: $W. The SECOND image is a different character used ONLY to show the camera angle and direction - do NOT copy its hair, bow or face. NO sword, no weapon. Neutral relaxed standing pose, arms slightly away from the body. Single full-body figure on a plain white background, no text."
for t in 1 2 3 4; do .venv/bin/python tools/gemini.py image "$P" $o v2/hair/opt/${id}_front.png v2/design/turnE/$v.png > /dev/null 2>&1; [ -f $o ] && exit 0; sleep 30; done
echo FAIL $id $v
