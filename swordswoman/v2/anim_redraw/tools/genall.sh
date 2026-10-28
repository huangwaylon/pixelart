#!/bin/bash
# genall.sh N "act groups" ... -> runs gen64 sequentially
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman; n=$1; shift
for x in "$@"; do set -- $x; .venv/bin/python v2/anim_redraw/tools/gen64.py $1 --groups $2 --n $n --mine --sword --tag ${3:-s} > /tmp/ar_g64_$1.log 2>&1; echo $1 $(grep -c ^ok /tmp/ar_g64_$1.log) $(grep -E "FAIL|ERR" /tmp/ar_g64_$1.log | head -2); done
