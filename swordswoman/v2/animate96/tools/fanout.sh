#!/bin/zsh
# fanout.sh PHASE [GUIDES]   96 px pipeline fan-out (35 clips = 7 acts x 5 views). Run from anywhere.
#   PHASE prep1  : prep the 5 idle clips            PHASE draw1 : draw them (pool 9)      PHASE post1 : post + gate idle -> read PIVOT drift per view
#   PHASE prep2  : prep the other 30 clips          PHASE draw2 : draw them (pool 9)      PHASE post2 : post + gate all 30
# GUIDES = v2/hy3d/frames_H (default) or v2/hy3d/frames_H2 once "FRAMES H2 READY" is in v2/g96/NOTES.md.
# DX per view (post96 --dx) = -(gate PIVOT drift of the idle rest frame); SE measured +2 in the pilot. Edit DX below after post1.
T=/Users/waylonhuang/Documents/other/pixelart/swordswoman; V2=$T/v2; PY=$T/.venv/bin/python; FF=$V2/anim_cut/tools/ff_redraw.py
ROOT=${A96_ROOT:-$V2/animate96/fan}; G=${2:-$V2/hy3d/frames_H}
typeset -A PX DX; PX=(S 62 SE 61 E 68 NE 70 N 65); DX=(S 0 SE 2 E 0 NE 0 N 0)
VIEWS=(S SE E NE N)
poses() { case $1 in walk) echo $V2/mocap/poses_mocap.json;; throw) echo $V2/throw/poses_throw.json;; *) echo $V2/unarmed/poses_unarmed.json;; esac }
prep() {  # prep ACT VIEW
  local a=$1 v=$2 alias=smile=cheerful,squash=blink_closed,hurt=pain rk="" hb=()
  case $a in idle) alias=smile=neutral,squash=blink_closed,hurt=pain; rk=up; hb=(--head-bob 1);; walk) hb=(--head-bob 2);; esac
  $PY $FF prep $a $v --root $ROOT --guides $G/${a}_$v/s96 --cell 128 128 --pivot $PX[$v] 124 --gpivot 96 152 --gscale 4 \
    --poses $(poses $a) --stamps $V2/m96/heads --palette $V2/pixelize/palette.json --master $V2/m96/masters/EC0_${v}_96.txt \
    --expr-alias $alias --head-lock $hb --qc gate,eye --lint-rel --rules $V2/animate96/RULES96.txt --rest-keys "$rk"
}
post() {  # post ACT VIEW
  $PY $V2/animate96/tools/post96.py clean $ROOT/${1}_$2 --dx $DX[$2] --sock-thin && \
  $PY $V2/animate96/tools/post96.py out $ROOT/${1}_$2 --outdir $V2/animate96/gifs && \
  $PY $V2/animate96/tools/post96.py qc $ROOT/${1}_$2 --quiet | head -12
}
ACTS2=(walk run jump dash hurt throw)
case $1 in
  prep1) for v in $VIEWS; do prep idle $v; done ;;
  draw1) $PY -u $V2/animate96/tools/run96.py $ROOT 9 ${VIEWS/#/idle_} 2>&1 | tee -a $ROOT/draw1.log ;;
  post1) for v in $VIEWS; do post idle $v; done ;;
  prep2) for a in $ACTS2; do for v in $VIEWS; do prep $a $v; done; done ;;
  draw2) cl=(); for a in $ACTS2; do for v in $VIEWS; do cl+=(${a}_$v); done; done
         $PY -u $V2/animate96/tools/run96.py $ROOT 9 $cl 2>&1 | tee -a $ROOT/draw2.log ;;
  post2) for a in $ACTS2; do for v in $VIEWS; do post $a $v; done; done ;;
  *) sed -n 2,6p $0 ;;
esac
