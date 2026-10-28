#!/bin/zsh
# render.sh PREFIX glb...   -> PREFIX_{vcol,ids,explode}_{front,side,back,se}.png
B=/Applications/Blender.app/Contents/MacOS/Blender; S=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/parts/scripts/render_parts.py
p=$1; shift
for m in vcol ids explode pose; do $B -b --factory-startup -P $S -- ${p}_$m $m 512 "$@" >/dev/null 2>&1 || echo FAIL $m; done
