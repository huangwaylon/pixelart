#!/bin/zsh
# runjob.sh NAME VIEW X0 Y0 X1 Y1 REGION ACCOUNT
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96; n=$1; v=$2; x0=$3; y0=$4; r=$7; acc=$8; D=$R/art/$n
typeset -A PB; PB=(S "54 49 80 60" SE "60 49 80 60" E "70 49 82 60" NE "0 0 0 0" N "0 0 0 0")
typeset -A TT
TT[hair]="hair/head crop: clean the outer hair outline and the ribbon. The thin ribbon tails must read as continuous thin RED ribbons following the illustration (1-2px E/R core, K edge only where it borders background or hair), not as dashed black lines; the bow keeps e/E/R. Keep hair strand separation readable (h lines on H, g/L sheen) without speckle."
TT[body]="upper body crop (kimono, bell sleeves, obi, skirt, hands, top of the thighs): clean the sleeve and skirt outlines (consistent stepping, the bell-sleeve hem as a clean shape); make the HANDS small but readable at the sleeve ends as in the illustration (a 2-4px skin s/S shape with K outline, a hint of fingers/thumb if it fits); kimono uses only the main red ramp e/E/R (E base, R folds/shadow, e top-light) - no maroon/grey drift; obi Q/O/o; keep the skin band between the skirt hem and the sock tops clearly readable (s with an S shadow row under the skirt, at least 2px of s visible per leg if the illustration shows it); remove orphan specks."
TT[legs]="legs crop (skin band, black thigh-high socks D/d, boots): clean sock/leg/boot outlines (consistent stepping, no notches/gaps, legs not fattened); socks D with a d sheen line, sock top as in the illustration; boots h/H/g/L with K outline and a readable cuff separating boot from sock; skin band above the socks readable s/S; remove orphans. Feet stay on the same bottom row."
if [ "${PB[$v]}" = "0 0 0 0" ]; then PT="none"; else PT="do NOT change any pixel inside the already-polished face box x ${PB[$v]% * *}.. (sprite coords x0 y0 x1 y1 = ${PB[$v]}); edits there are discarded."; fi
b=$(sed "s#DIR#$D#g; s#X0#$x0#g; s#Y0#$y0#g; s#VIEWCODE#$v#g; s#PROTBOX#${PB[$v]}#g; s#REGION#$v view, $r#; s#PROTTEXT#$PT#" $R/art/brief_region.md)
T="${TT[$r]}"; [ -f $D/task.txt ] && T="$(cat $D/task.txt)"
b=${b//TASKTEXT/$T}
zsh -ic "claude-as $acc --dangerously-skip-permissions --model claude-opus-5-5 -p \"\$(cat)\"" <<<"$b" > $D/log.txt 2>&1
echo "$n: $(tail -1 $D/log.txt | cut -c1-160)"
