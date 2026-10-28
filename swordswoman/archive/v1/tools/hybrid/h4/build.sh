#!/bin/zsh
# S3 r2 merged production build: lock2 heads -> cels/anims -> sprites -> metrics, sheets, GIFs.
#   tools/hybrid/h3/build.sh [TAG]      (TAG default r2 -> hybrid/S3_editchain/r2, GIFs hybrid/gifs/S3_editchain_r2_*)
set -e
setopt null_glob
TAG=${1:-r2}
R=hybrid/S3_editchain/$TAG
.venv/bin/python tools/hybrid/h3/heads.py > /dev/null
rm -rf $R/sprite; mkdir -p $R
.venv/bin/python tools/hybrid/h3/build.py $R
mkdir -p $R/sprite/guide $R/lock2
cp hybrid/S3_editchain/r1/sprite/guide/*.png $R/sprite/guide/
cp hybrid/lock2/head_*.png hybrid/lock2/heads.json $R/lock2/ 2>/dev/null || true
# metrics on the standard set (bonus frames are measured separately)
STD=($R/sprite/turn_*[^x].png $R/sprite/walk_SE_k?.png $R/sprite/slash_SE_k?.png $R/sprite/jump_E_{crouch,apex,land}.png)
mkdir -p $R/std; rm -f $R/std/*.png; cp $STD $R/std/; mkdir -p $R/std/guide; cp $R/sprite/guide/*.png $R/std/guide/
.venv/bin/python tools/hybrid/metrics.py $R/std --guide-map hybrid/S3_editchain/r1/guide_map.json --json $R/metrics.json > $R/metrics.txt 2>&1 || true
.venv/bin/python tools/hybrid/h3/gate.py $R > $R/gate.txt; cat $R/gate.txt
.venv/bin/python tools/hybrid/sheets.py set $R/std --out $R/set_3x.png --zoom 3 | tail -1
.venv/bin/python tools/hybrid/sheets.py dirs $R/std --out $R/dirs8.png --bg grass | tail -1
.venv/bin/python tools/hybrid/sheets.py contact $R/std --out $R/contact.png --cols 4 | tail -1
.venv/bin/python tools/hybrid/h3/sheet.py $R
rm -rf $R/gifs_tmp; .venv/bin/python tools/hybrid/gifs.py all $R/std --out-dir $R/gifs_tmp --slow 4 | tail -1
.venv/bin/python tools/hybrid/gifs.py anim $R/std --out-dir $R/gifs_tmp --only slash_SE --ms 220,50,180,260 | tail -1
mkdir -p hybrid/gifs
for f in $R/gifs_tmp/*.gif; do cp $f hybrid/gifs/S3_editchain_${TAG}_${f:t}; done
.venv/bin/python tools/hybrid/h3/bonus_gif.py $R hybrid/gifs/S3_editchain_${TAG}
ls hybrid/gifs | grep -c S3_editchain_${TAG}_
