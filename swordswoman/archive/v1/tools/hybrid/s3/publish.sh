#!/bin/zsh
R=hybrid/S3_editchain/r1
.venv/bin/python tools/hybrid/metrics.py $R/sprite --guide-map $R/guide_map.json --json $R/metrics.json > $R/metrics.txt 2>&1
.venv/bin/python tools/hybrid/sheets.py contact $R/sprite --out $R/sheet.png --cols 4 | tail -1
.venv/bin/python tools/hybrid/sheets.py set $R/sprite --out $R/set_3x.png --zoom 3 | tail -1
.venv/bin/python tools/hybrid/sheets.py dirs $R/sprite --out $R/dirs8.png --bg grass | tail -1
rm -rf $R/gifs_tmp; .venv/bin/python tools/hybrid/gifs.py all $R/sprite --out-dir $R/gifs_tmp --slow 4 | tail -1
mkdir -p hybrid/gifs
for f in turntable_4x_grey turntable_4x_grass turntable_1x_grass walk_SE_4x_grey walk_SE_4x_grass walk_SE_slow_4x_grey slash_SE_4x_grey slash_SE_4x_grass slash_SE_slow_4x_grey jump_E_4x_grey jump_E_4x_grass jump_E_slow_4x_grey; do
  cp $R/gifs_tmp/$f.gif hybrid/gifs/S3_editchain_r1_$f.gif; done
ls hybrid/gifs | grep S3_editchain_r1 | wc -l
