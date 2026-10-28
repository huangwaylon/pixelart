#!/bin/zsh
# Re-runnable pixelization (one command per view). Usage: make_top.sh [top1|top2] [views...]
#   top1 = E2 (k-centroid + face pass) @ 96 px figure (128 cell);  top2 = E2 @ 80 px figure (112 cell)
#   palette: v2/pixelize/palette.json (locked 16 + socks D/d). Sources: v2/hair/turnE_final (SE = iso_SE_fixed.png).
#   Single view on a new illustration: .scratch/pixelize/pixeloe/venv/bin/python -I v2/pixelize/tools/pz.py EC0 <VIEW> 96 --src new.png --pal v2/pixelize/palette.json --out DIR
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
PY=.scratch/pixelize/pixeloe/venv/bin/python
T=${1:-top1}; shift; V=(${@}); [ ${#V} -eq 0 ] && V=(S SE E NE N); H=96; [ $T = top2 ] && H=80
mkdir -p v2/pixelize/$T
for v in $V; do $PY -I v2/pixelize/tools/pz.py EC0 $v $H --pal v2/pixelize/palette.json --out v2/pixelize/$T; done
$PY -I v2/pixelize/tools/sheet.py v2/pixelize/$T S SE E NE N
