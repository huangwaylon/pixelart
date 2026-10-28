#!/bin/zsh
# finalize.sh : polished set -> metrics, sheets, GIFs (S2_gridsheet r1 polish)
set -e
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
R=hybrid/S2_gridsheet/r1; O=${R}/polished; PY=.venv/bin/python; G=hybrid/gifs/S2_gridsheet_r1_polished
${PY} tools/hybrid/metrics.py ${O} --guide-dir hybrid/guide/p2/cells --json ${O}/metrics.json > ${O}/metrics.txt 2>&1 || true
${PY} tools/hybrid/sheets.py set ${O} --out ${R}/polished_set.png --zoom 3 > /dev/null
${PY} tools/hybrid/gifs.py all ${O} --out-dir ${O}/_gifs --slow 4 > /dev/null
${PY} tools/hybrid/gifs.py compare ${R}/sprite ${O} --labels pre,polished --out-dir ${O}/_gifs --zoom 3 > /dev/null || true
cp ${O}/_gifs/turntable_4x_grey.gif ${G}_turntable.gif
cp ${O}/_gifs/turntable_4x_grass.gif ${G}_turntable_grass.gif
cp ${O}/_gifs/dirs8_4x_grey.gif ${G}_dirs8.gif
cp ${O}/_gifs/walk_SE_4x_grey.gif ${G}_walk.gif
cp ${O}/_gifs/walk_SE_slow_4x_grey.gif ${G}_walk_slow.gif
cp ${O}/_gifs/slash_SE_4x_grey.gif ${G}_slash.gif
cp ${O}/_gifs/slash_SE_slow_4x_grey.gif ${G}_slash_slow.gif
cp ${O}/_gifs/jump_E_4x_grey.gif ${G}_jump.gif
cp ${O}/_gifs/jump_E_slow_4x_grey.gif ${G}_jump_slow.gif
for s in walk_SE slash_SE jump_E; do cp ${O}/_gifs/compare_${s}_3x.gif ${G}_compare_${s}.gif 2>/dev/null || true; done
echo finalized
