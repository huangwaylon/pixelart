#!/bin/zsh
# S3 r1 polish: render every key from the hand-typed cels -> hybrid/S3_editchain/r1/polished/, then sheet, GIFs, metrics.
set -e
R=hybrid/S3_editchain/r1; P=$R/polished
mkdir -p $P/src $P/guide
for d in S SE E NE N NW W SW; do .venv/bin/python tools/hybrid/s3pol/cel.py tools/hybrid/s3pol/cels/turn_$d.cel $P/turn_$d.png; done
for a in walk_SE slash_SE jump_E; do .venv/bin/python tools/hybrid/s3pol/anim.py tools/hybrid/s3pol/anims/$a.py $P > /dev/null; done
cp tools/hybrid/s3pol/cels/*.cel tools/hybrid/s3pol/anims/*.py $P/src/
cp $R/sprite/guide/*.png $P/guide/
.venv/bin/python tools/hybrid/metrics.py $P --guide-map $R/guide_map.json --json $R/metrics_polished.json > $R/metrics_polished.txt 2>&1 || true
.venv/bin/python tools/hybrid/sheets.py contact $P --out $R/polished_sheet.png --cols 4 | tail -1
.venv/bin/python tools/hybrid/sheets.py set $P --out $R/polished_set_3x.png --zoom 3 | tail -1
.venv/bin/python tools/hybrid/sheets.py dirs $P --out $R/polished_dirs8.png --bg grass | tail -1
rm -rf $R/gifs_polished_tmp; .venv/bin/python tools/hybrid/gifs.py all $P --out-dir $R/gifs_polished_tmp --slow 4 | tail -1
mkdir -p hybrid/gifs
for f in turntable_4x_grey turntable_4x_grass turntable_1x_grass walk_SE_4x_grey walk_SE_4x_grass walk_SE_slow_4x_grey slash_SE_4x_grey slash_SE_4x_grass slash_SE_slow_4x_grey jump_E_4x_grey jump_E_4x_grass jump_E_slow_4x_grey dirs8_4x_grass; do
  [ -f $R/gifs_polished_tmp/$f.gif ] && cp $R/gifs_polished_tmp/$f.gif hybrid/gifs/S3_editchain_r1_polished_$f.gif; done
.venv/bin/python tools/hybrid/gifs.py compare $R/sprite $P --labels r1,polished --out-dir $R/gifs_polished_tmp/cmp --zoom 3 | tail -1
for f in $R/gifs_polished_tmp/cmp/*.gif; do cp $f hybrid/gifs/S3_editchain_r1_polished_${f:t}; done
ls hybrid/gifs | grep -c S3_editchain_r1_polished
