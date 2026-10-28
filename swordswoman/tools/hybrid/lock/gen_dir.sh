#!/bin/zsh
# usage: gen_dir.sh <DIR> <tag> [model] [stylefirst|guidefirst]
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
d=$1; tag=$2; model=${3:-default}; order=${4:-stylefirst}
mkdir -p hybrid/lock/prompts/dir
.venv/bin/python tools/hybrid/lock/dir_prompt.py $d $order > hybrid/lock/prompts/dir/${d}_${tag}.txt
if [[ $order == guidefirst ]]; then
  refs=(hybrid/guide/p3d_iso/white/${d}.png concept/chibi_iso_v5.png)
else
  refs=(concept/chibi_iso_v5.png hybrid/guide/p3d_iso/white/${d}.png)
fi
tools/hybrid/lock/gen.sh dir_${d}_${tag} $model hybrid/lock/prompts/dir/${d}_${tag}.txt $refs hybrid/lock/wip/face_v1.png refs/1.png
