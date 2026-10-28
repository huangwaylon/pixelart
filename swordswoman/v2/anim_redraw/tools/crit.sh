#!/bin/zsh
# crit.sh ACT VER "context" : crit sheet (3x, 4 cols) -> Argon + Opus(be_system) in parallel -> crit/<act>_<ver>_{argon,opus}.txt
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman; A=$R/v2/anim_redraw; P=$R/.venv/bin/python
act=$1; ver=$2; ctx=$3; W=$A/work/${act}_SE/$ver
S=$A/crit/${act}_${ver}_sheet.png
$P $A/tools/csheet.py $S 3 $W/f??.png --cols 4 >/dev/null
ms=$($P -c "import json;print([f['ms'] for f in json.load(open('$A/work/${act}_SE/plan_$ver.json'))['frames']])")
Q="You are a harsh senior pixel-art animation director (game studio). Critique this chibi swordswoman SE (front 3/4) '$act' animation. Frames are left-to-right, top-to-bottom in the contact sheet $S (3x nearest upscale; each frame is 80x104 px at 1x). Frame durations ms: $ms. GIF: $A/gifs/${act}_SE_${ver}.gif. Context: $ctx. Goals: lively, bouncy, energetic animation with impactful timing and smears on fast actions; simple readable silhouette; clean pixel art (no orphan/noise pixels, no jaggies, no pillow shading, consistent palette & proportions frame to frame, feet pinned, no shimmer in static areas). Reply in <=12 lines: SCORE x/10 (honest; 7 = shippable indie quality), then the top 6 concrete problems naming frame numbers (0-based) and body part/pixel area, then the 3 most valuable fixes."
$P $R/tools/gemini.py ask "$Q" $S > $A/crit/${act}_${ver}_argon.txt 2>&1 &
zsh -ic "claude-as be_system --dangerously-skip-permissions --model claude-opus-5-5 -p '$Q Use the Read tool on the sheet PNG (do not open the GIF).'" > $A/crit/${act}_${ver}_opus.txt 2>&1 &
wait
grep -v "can't change option" $A/crit/${act}_${ver}_argon.txt | head -20; echo ----; grep -v "can't change option" $A/crit/${act}_${ver}_opus.txt | head -20
