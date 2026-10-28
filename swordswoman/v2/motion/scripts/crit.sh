#!/bin/zsh
# crit.sh ACT TAG [EXTRA_NOTE] -> motion/crit/<TAG>_<ACT>_{argon,opus}.txt  (critics: Argon via tools/gemini.py, Opus via claude-as)
A=$1; T=$2; X=${3:-}
M=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/motion; P=$M/prev/$T
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
MS_SE=$(python3 -c "import json;f=json.load(open('$P/${A}_SE/frames.json'))['frames'];print(', '.join(x['name']+' '+str(x['ms'])+'ms' for x in f))")
Q="You are a senior game animator (Pokemon BW / Octopath / SF3 sprite standards, Richard Williams mechanics). These are 3D MOTION GUIDES for a 96 px isometric pixel-art girl (30 deg ortho camera; a pixel artist redraws every frame on top, the face/head detail is redrawn later, so judge MOTION, not rendering). Action: ${A} (frames: ${MS_SE}). Images: one critic sheet per view (SE, then E). Each sheet: row 1 = OLD motion (stiff, rigid parts, for comparison), row 2 = NEW motion at the true 1x game pixel size (shown x2), row 3 = NEW 2x shaded preview. New version adds whole-body mechanics and spring secondary motion of hair (side locks, back hair), ribbon tails (thin red strands hanging from the bow), bow and skirt hem. ${X}
Score the NEW motion 1-10 on: natural, whole-body, fluid, appealing, secondary motion convincing, readable at 1x; then OVERALL (1-10). Then list the top 3 concrete fixes (which frame, which body part, which direction, how much). Be strict and brief (<=150 words). Format: first line 'OVERALL: N'."
.venv/bin/python tools/gemini.py ask "$Q" $P/${A}_SE/crit.png $P/${A}_E/crit.png > $M/crit/${T}_${A}_argon.txt 2>&1 &
zsh -ic "claude-as nsystem4 --dangerously-skip-permissions --model claude-opus-5-5 -p \"$Q  Read these two images with the Read tool: $P/${A}_SE/crit.png and $P/${A}_E/crit.png (also available: per-frame data $P/${A}_SE/frames.json with head_xf and secondary spring states). Do not modify any files.\"" > $M/crit/${T}_${A}_opus.txt 2>&1
wait
grep -m1 -i "OVERALL" $M/crit/${T}_${A}_argon.txt | head -1 | sed "s/^/$A argon: /"; grep -m1 -i "OVERALL" $M/crit/${T}_${A}_opus.txt | head -1 | sed "s/^/$A opus: /"
