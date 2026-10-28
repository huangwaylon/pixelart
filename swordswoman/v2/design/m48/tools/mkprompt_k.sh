#!/bin/bash
# mkprompt_k.sh VIEW ROUND [feedback] -> Opus prompt: add katana to the final no-katana master
n=$1; r=$2; X=$3; M=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/design/m48
case $n in
S) H="her right hand = the hand on the LEFT of the picture; blade points down and outward to the lower-left, foreshortened (slightly shorter, ~13-15px) because it angles toward the camera";;
E) H="the near hand (her right hand, at the end of the visible arm); the blade goes from that mitten diagonally down toward the lower-right ground in front of her feet, not crossing the boots, ~16-18px";;
NE) H="the near hand (her right hand, at the end of the visible arm); the blade goes from that mitten diagonally down toward the lower-right ground in front of her feet, not crossing the boots, ~16-18px";;
N) H="her right hand = the hand on the RIGHT of the picture; blade points down and outward to the lower-right, ~16-18px";;
esac
cat <<P
You are a professional pixel artist. Add a KATANA to a finished 48px pixel-art master sprite (64x64 char-map), view $n.
Base (final no-katana master, keep every pixel of the character unchanged except the hand that holds the sword and pixels the blade covers): $M/${n}.txt  (8x preview: $M/work/${n}_final_8x.png)
Design reference for the sword pose in this view: $M/work/ref_${n}_k.png (sword held DOWN at her side, $H).
Palette legend: $M/work/legend.txt ('.' transparent). Style anchor: $M/work/SE_anchor_8x.png.
KATANA PIXEL RULE (locked): blade = 2px steel (w on the upper/lit pixel, n on the lower pixel) + a 1px dark # edge on the UNDERSIDE, one clean regular stack per step along the blade (even stair-steps, no broken dashes), tip = 1px n + #; straight blade. Grip = 3-4px dark (# with D/d), visibly sticking out of the mitten on the side opposite the blade; guard (tsuba) = 1x3 or 2x2 k with # outline between mitten and blade, clearly visible. The hand closes around the grip (mitten 2 skin + 1 shadow). Blade must not cross the boots or the face, must stay inside the 64x64 cell and above row 60, and must read against the red dress where it overlaps (the dark # edge separates it).
$( [ -n "$X" ] && echo "FEEDBACK you MUST fix: $(cat $X)" )
$( [ -f $M/work/${n}_k_r$((r-1)).txt ] && echo "Your previous version: $M/work/${n}_k_r$((r-1)).txt (start from it)." )
Write the result to $M/work/${n}_k_r$r.txt (exactly 64 lines x 64 chars). Self-check:
  /Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python $M/tools/cm.py render $M/work/${n}_k_r$r.txt $M/work/${n}_k_r${r}_8x.png --s 8 --bg
  /Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python $M/tools/cm.py lint $M/work/${n}_k_r$r.txt
Read the 8x png and fix until clean. Finish by replying with ONE short line.
P
