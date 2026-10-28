#!/bin/zsh
# crit.sh ACT TAG ["extra note"] -> motion/crit/<TAG>_<ACT>_{opus,argon}.txt ; validates that each file has a SCORE line (retries once)
A=$1; T=$2; X=${3:-}
E=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/motion; C=$E/crit
SE=$C/board_${A}_SE_${T}.png; EV=$C/board_${A}_E_${T}.png; ON=$C/onion_${A}_E_${T}.png
case $A in
 walk) D="8-frame walk cycle loop (in place, 105 ms/frame). Keys: f0 contact L, f1 down, f2 passing, f3 up, f4 contact R ...";;
 run) D="8-frame run cycle loop (in place, 70 ms/frame), with flight phases. Keys: f0 contact L, f1 down, f2 push-off, f3 flight, f4 contact R ...";;
 idle) D="12-frame idle loop (2.4 s) with holds: weight on L (hold, blink), transfer, weight on R (look toward camera, hold), transfer back; breathing twice per loop.";;
 jump) D="one-shot standing jump, 16 frames: stand, anticipation, crouch (hold), launch, take-off stretch, rise x2, apex hang (120 ms), fall x2, landing contact (35 ms), absorb, squash, recover overshoot onto toes, settle dip, end.";;
esac
Q="You are a senior 2D/3D game animator and strict animation critic (Pokemon overworld / Octopath / Sea of Stars / PMD sprite standards; Richard Williams mechanics; the 12 principles). These frames are a PREVIEW of a MOTION FILE for a chibi girl sprite (~3 heads tall: big head with a bob haircut + back bun + big red bow; red short kimono-dress with big bell sleeves, a dark obi, flared short skirt, thigh-high navy socks). ${RENDER_NOTE:-The figure is drawn with crude capsules/spheres (this is NOT the final art: the face is two dots, the bangs/side locks/back hair are drawn as rods, sleeves as dark-red blobs, the skirt as 8 panels).} Judge ONLY THE MOTION: poses, timing, weight, arcs, overlap/follow-through, secondary motion (hair, bun, bow lobes, sleeves, skirt are spring-simulated), joints, foot contact. Action: ${D} ${X}
The owner rejected the previous version as: 'stiff and unnatural, the joints look off, need more dynamic movement, more movement details across the whole body, bouncing parts.' Style target: appeal and readability over realism - exaggerated, bouncy, snappy, clear key poses.
Images: (1) frames in the SE game view (30 deg elevation ortho), numbered with display time; (2) the same frames from the E side view; (3) an onion skin of all frames (E view) to show arcs.
Answer in <= 250 words. First line exactly 'SCORE: N/10' (overall motion quality for a game sprite, be strict: 5 = usable but stiff, 7 = good game quality, 9 = AAA). Then scores 1-10 for: key poses, timing/spacing, weight & bounce, overlap/follow-through, secondary motion, joints/contacts, appeal. Then the TOP 5 concrete fixes, each with frame numbers, body part, direction and amount (degrees / fraction of a step / ms)."
run_opus() {
  zsh -ic "claude-as be_system --dangerously-skip-permissions --model claude-opus-5-5 -p \"$Q  Use the Read tool to view these three images (absolute paths): $SE  $EV  $ON . Do not modify any files.\"" > $C/${T}_${A}_opus.txt 2>/dev/null
}
run_argon() {
  cd /Users/waylonhuang/Documents/other/pixelart/swordswoman && .venv/bin/python tools/gemini.py ask "$Q Do not inflate: list concrete issues vs animation principles." $SE $EV $ON > $C/${T}_${A}_argon.txt 2>&1
}
run_opus & run_argon & wait
for w in opus argon; do
  if ! grep -q "SCORE" $C/${T}_${A}_${w}.txt; then echo "retry $w"; run_$w; fi
  echo "$A $w: $(grep -m1 SCORE $C/${T}_${A}_${w}.txt) ($(wc -c < $C/${T}_${A}_${w}.txt) bytes)"
done
