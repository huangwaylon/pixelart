#!/bin/zsh
# crit_each.sh ROUND [dir=SE] [actions...] -> crit/<ROUND>_<act>_{gem,opus}.txt ; per-action focused critique, 3 parallel
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/anim_cut
R=$1; D=${2:-SE}; shift 2; ACTS=($@); (( $#ACTS )) || ACTS=(idle walk run jump dash slash)
typeset -A G
G[idle]="idle loop: slow breathing bob, overlap of bow/hem, blink"
G[walk]="walk cycle 8f ~100ms: contact/down/pass/up, bob, arm opposition"
G[run]="run cycle: forward lean, big stride, airborne frames, arm pump, bob"
G[jump]="jump: anticipation crouch, launch stretch, apex hang, fall, land squash, recover"
G[dash]="dash: anticipation, burst with afterimage/speed lines, skid/brake, recover"
G[slash]="katana slash: anticipation, wind-up, 1 smear frame along the blade path, impact, hit-stop, follow-through, recover"
i=0
for a in $ACTS; do
  P=crit/${R}_${a}.prompt
  echo "Contact sheet of ONE pixel-art cutout-rig animation: ${a}_${D} (${D} view, chibi swordswoman with katana, labels = frame index, ms, pose). Action goal: ${G[$a]}. Targets: lively, bouncy, energetic; readable key poses; squash & stretch; overlap; impact timing; clean tapered smears; identity consistent; strict pixel-art quality (outlines, no orphans/jaggies, palette). Score on an absolute scale where 7 = shippable indie-game quality and 9 = top commercial pixel art. Give the 3 most important concrete problems (frame + region + exact fix). End with one line: 'SCORE ${a}: N'." > $P
  tools/crit.sh ${R}_${a} $P $PWD/sheets/${a}_${D}_sheet.png &
  (( ++i % 3 == 0 )) && wait
done
wait
for a in $ACTS; do echo "$a: $(grep -ohi "score ${a}[^0-9]*[0-9.]*" crit/${R}_${a}_gem.txt crit/${R}_${a}_opus.txt | grep -o '[0-9.]*$' | tr '\n' ' ')"; done
