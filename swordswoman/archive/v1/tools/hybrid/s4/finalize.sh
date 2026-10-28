#!/bin/zsh
# finalize.sh <pass_dir> : copy a build pass into hybrid/S4_textured3d/r1/{sprite,hires}, run metrics,
# contact sheet and GIFs.
set -e
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
P=${1:?pass}; R=hybrid/S4_textured3d/r1; PY=.venv/bin/python
mkdir -p ${R}/sprite ${R}/hires hybrid/gifs
for f in ${P}/base/*.png; do n=${f:t:r}; cp ${f} ${R}/sprite/${n}.png; cp ${P}/hires/${n}.png ${R}/hires/${n}.png; cp ${P}/hires/${n}.png ${R}/sprite/${n}_hires.png; done
mkdir -p ${R}/guide; cp ${P}/guide/* ${R}/guide/
${PY} tools/hybrid/metrics.py ${R}/sprite --guide-dir ${R}/guide --json ${R}/metrics.json > ${R}/metrics.txt 2>&1 || true
${PY} tools/hybrid/sheets.py set ${R}/sprite --out ${R}/sheet.png --zoom 3
${PY} tools/hybrid/sheets.py contact ${R}/sprite --out ${R}/contact.png --guide-dir ${R}/guide
${PY} tools/hybrid/gifs.py all ${R}/sprite --out-dir ${R}/_gifs --slow 4 > /dev/null
G=hybrid/gifs/S4_textured3d_r1
cp ${R}/_gifs/turntable_4x_grey.gif ${G}_turntable.gif
cp ${R}/_gifs/turntable_4x_grass.gif ${G}_turntable_grass.gif
cp ${R}/_gifs/walk_SE_4x_grey.gif ${G}_walk_SE.gif
cp ${R}/_gifs/slash_SE_4x_grey.gif ${G}_slash_SE.gif
cp ${R}/_gifs/slash_SE_slow_4x_grey.gif ${G}_slash_SE_slow.gif
cp ${R}/_gifs/jump_E_4x_grey.gif ${G}_jump_E.gif
cp ${R}/_gifs/dirs8_4x_grass.gif ${G}_dirs8_grass.gif 2>/dev/null || true
echo finalized
