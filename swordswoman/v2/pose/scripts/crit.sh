#!/bin/zsh
# crit.sh CRITDIR [opus_account] : CRITDIR has ask.txt + imgs.txt (space-separated abs paths). Runs Argon + Opus in parallel -> argon.md, opus.md
C=$1; ACC=${2:-bni_requests}; cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
B=v2/pose/crit/prompt_base.txt; IM=$(cat $C/imgs.txt)
{ cat $B; echo; cat $C/ask.txt; } > $C/full_prompt.txt
{ cat $C/full_prompt.txt; echo; echo "Images to Read (in this order):"; for f in $(echo $IM); do echo $f; done; echo "Do not run any commands other than Read on these images; do not write files."; } > $C/opus_prompt.txt
( .venv/bin/python tools/gemini.py ask "$(cat $C/full_prompt.txt)" $(echo $IM) > $C/argon.md 2>&1 ) &
( zsh -ic "claude-as $ACC --dangerously-skip-permissions --model claude-opus-5-5 -p 'Read the file $PWD/$C/opus_prompt.txt and follow its instructions exactly. Your final answer is the critique text.'" > $C/opus.md 2>&1 ) &
wait
