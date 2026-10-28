#!/bin/zsh
# S3 r3: build kit frames (lock3) + hand cels -> hybrid/S3_editchain/r3/sprite (+ bonus/), metrics
set -e
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
R=hybrid/S3_editchain/r3; W=$R/wip
.venv/bin/python tools/hybrid/h4/heads.py > /dev/null
.venv/bin/python tools/hybrid/h4/build.py $W/kit > /dev/null
.venv/bin/python tools/hybrid/h4/hand/walk_SE.py $W/walk
.venv/bin/python tools/hybrid/h4/hand/bonus_SE.py $W/bonus
rm -rf $R/sprite; mkdir -p $R/sprite/bonus
for n in turn_S turn_SE turn_E turn_NE turn_N turn_NW turn_W turn_SW slash_SE_k0 slash_SE_k1 slash_SE_k2 slash_SE_k3 jump_E_crouch jump_E_apex jump_E_land; do cp $W/kit/sprite/$n.png $R/sprite/; done
cp $W/walk/walk_SE_k?.png $R/sprite/
cp $W/bonus/*.png $R/sprite/bonus/
[ -d $W/walk8 ] && mkdir -p $R/sprite/bonus/walk8 && cp $W/walk8/*.png $R/sprite/bonus/walk8/ || true
[ -f $R/post.py ] && .venv/bin/python $R/post.py $R/sprite || true
cp -r hybrid/S3_editchain/r2/std/guide $R/sprite/guide
.venv/bin/python tools/hybrid/metrics.py $R/sprite --guide-map hybrid/S3_editchain/r1/guide_map.json --json $R/metrics.json > $R/metrics.txt 2>&1 || true
tail -5 $R/metrics.txt
