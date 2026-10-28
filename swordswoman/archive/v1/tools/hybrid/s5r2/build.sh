#!/bin/zsh
# S5 r2 build: turns (S3 r2 cels, reused) + Gemini-acted retraced action keys -> sprite/, metrics, sheet, GIFs.
set -e
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
R=hybrid/S5_pixelnative/r2; P=.venv/bin/python
mkdir -p $R/sprite $R/hires $R/work hybrid/gifs
$P tools/hybrid/s5r2/turns.py $R/sprite
for a in slash_SE jump_E walk_SE; do $P tools/hybrid/s5r2/retrace.py $a > /dev/null; done
# Gemini hi-res pose refs next to each acted sprite (and in hires/)
for f in $R/sprite/*_hires.png; do b=${f:t}; cp $f $R/hires/${b%_hires.png}.png; done
$P tools/hybrid/metrics.py $R/sprite --json $R/metrics.json > $R/metrics.txt 2>&1 || true
$P tools/hybrid/sheets.py contact $R/sprite --out $R/contact.png --cols 4 | tail -1
$P tools/hybrid/sheets.py set $R/sprite --out $R/sheet.png --zoom 3 | tail -1
$P tools/hybrid/sheets.py dirs $R/sprite --out $R/dirs8.png --bg grass | tail -1
rm -rf $R/gifs_tmp; $P tools/hybrid/gifs.py all $R/sprite --out-dir $R/gifs_tmp --slow 4 --jump-z | tail -1
for f in turntable_4x_grey turntable_4x_grass turntable_1x_grass walk_SE_4x_grey walk_SE_4x_grass walk_SE_1x_grass walk_SE_slow_4x_grey slash_SE_4x_grey slash_SE_4x_grass slash_SE_1x_grass slash_SE_slow_4x_grey jump_E_4x_grey jump_E_4x_grass jump_E_1x_grass jump_E_slow_4x_grey dirs8_4x_grass; do
  [ -f $R/gifs_tmp/$f.gif ] && cp $R/gifs_tmp/$f.gif hybrid/gifs/S5_pixelnative_r2_$f.gif; done
ls hybrid/gifs | grep -c S5_pixelnative_r2
