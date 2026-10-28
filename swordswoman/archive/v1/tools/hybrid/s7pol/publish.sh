#!/bin/zsh
# S7 r3 polish publish: polished/ -> metrics, sheets, GIFs (hybrid/gifs/S7_fxkit_r3_polished_*)
set -e
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
R=hybrid/S7_fxkit/r3; P=$R/polished; V=$R/polwork/R
.venv/bin/python tools/hybrid/s7pol/polish.py
rm -rf $V; mkdir -p $V/sprite
cp $P/*.png $V/sprite/; cp $P/bonus/*.png $V/sprite/
.venv/bin/python tools/hybrid/metrics.py $P --json $R/metrics_polished.json > $R/metrics_polished.txt 2>&1 || true
cp $R/metrics_polished.json $V/metrics.json
.venv/bin/python tools/hybrid/h3/sheet.py $V; cp $V/sheet.png $R/polished_sheet.png
.venv/bin/python tools/hybrid/sheets.py set $P --out $R/polished_set_3x.png --zoom 3 | tail -1
.venv/bin/python tools/hybrid/sheets.py dirs $P --out $R/polished_dirs8.png --bg grass | tail -1
.venv/bin/python tools/hybrid/s7/strip.py $P $R/polished_strip_1x_3x.png
T=$R/polwork/gifs_tmp; rm -rf $T
.venv/bin/python tools/hybrid/gifs.py all $P --out-dir $T --slow 4 | tail -1
.venv/bin/python tools/hybrid/gifs.py compare $R/sprite $P --labels r3,polished --out-dir $T/cmp --zoom 3 | tail -1
mkdir -p hybrid/gifs; setopt null_glob; rm -f hybrid/gifs/S7_fxkit_r3_polished_*
for f in $T/*.gif; do cp $f hybrid/gifs/S7_fxkit_r3_polished_${f:t}; done
for f in $T/cmp/*.gif; do cp $f hybrid/gifs/S7_fxkit_r3_polished_beforeafter_${f:t}; done
.venv/bin/python tools/hybrid/h3/bonus_gif.py $V hybrid/gifs/S7_fxkit_r3_polished
ls hybrid/gifs | grep S7_fxkit_r3_polished_
