#!/bin/zsh
# crit48.sh ACT VER "context" [account] : Argon + Opus on sheets/<act>_SE_<ver>.png -> crit/<act>_<ver>_{argon,opus}.txt
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman; A=$R/v2/anim_redraw; P=$R/.venv/bin/python
act=$1; ver=$2; ctx=$3; acc=${4:-be_system}
S=$A/sheets/${act}_SE_${ver}.png
ms=$($P -c "import json;print([f['ms'] for f in json.load(open('$A/work48/$act/plan_$ver.json'))['frames']])")
Q="You are a harsh senior pixel-art animation director at a game studio. Critique this 48px chibi swordswoman '$act' animation, SE (front 3/4) view, 64x64 cell. Contact sheet: $S (top: frames at 3x, left-to-right then top-to-bottom, 0-based; bottom strip: same frames at 1x). Frame durations ms: $ms. Context: $ctx. Goals: lively, bouncy, energetic, impactful timing, smears/FX on fast actions; simple readable silhouette; clean pixel art (no orphan/noise pixels, no jaggies, no pillow shading, consistent palette & proportions frame to frame, feet pinned/grounded, no shimmer in static areas). Reply in <=12 lines: 'SCORE x/10' (honest; 7 = shippable indie quality), then the top 6 concrete problems naming frame numbers and body part / pixel area, then the 3 most valuable fixes."
$P $R/tools/gemini.py ask "$Q" $S > $A/crit/${act}_${ver}_argon.txt 2>&1 &
zsh -ic "claude-as $acc --dangerously-skip-permissions --model claude-opus-5-5 -p '$Q Use the Read tool on the sheet PNG.' < /dev/null" > $A/crit/${act}_${ver}_opus.txt 2>&1 &
wait
for f in argon opus; do echo "== $f"; grep -v -e "can't change option" -e "Saving session" $A/crit/${act}_${ver}_$f.txt | head -16; done
