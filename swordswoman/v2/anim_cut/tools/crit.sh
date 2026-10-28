#!/bin/zsh
# crit.sh TAG PROMPTFILE img1 [img2...]  -> crit/TAG_gem.txt, crit/TAG_opus.txt (parallel)
ROOT=/Users/waylonhuang/Documents/other/pixelart/swordswoman
TAG=$1; PF=$2; shift 2
P="$(cat $PF)"
OUT=$ROOT/v2/anim_cut/crit
cd $ROOT
( .venv/bin/python tools/gemini.py ask "$P
Be a harsh pixel-art director. Gemini tends to overrate: list concrete pixel problems with coordinates/regions, then scores /10." "$@" > $OUT/${TAG}_gem.txt 2>&1 ) &
IMGS="${(j: :)@}"
( zsh -ic "claude-as bni_requests --dangerously-skip-permissions --model claude-opus-5-5 -p \"\$(cat <<'XX'
$P
Images (Read them): $IMGS
You are a harsh senior pixel-art director. Name concrete pixel problems (coordinates/regions), give scores /10, answer in <=350 words. Do not modify any files.
XX
)\"" > $OUT/${TAG}_opus.txt 2>&1 ) &
wait
echo done $TAG
