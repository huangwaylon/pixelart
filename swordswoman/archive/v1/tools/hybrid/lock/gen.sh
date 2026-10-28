#!/bin/zsh
# usage: gen.sh <name> <model|default> <promptfile> ref1 ref2 ...
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
name=$1; model=$2; pf=$3; shift 3
args=()
[[ $model != default ]] && args=(--model $model)
for i in 1 2 3; do
  .venv/bin/python tools/gemini.py image "$(cat $pf)" hybrid/lock/wip/${name}.png "$@" $args > hybrid/lock/wip/${name}.log 2>&1 && exit 0
  sleep 10
done
exit 1
