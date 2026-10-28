#!/bin/zsh
# End-to-end test of tools/hybrid.  Run from anywhere; writes only under hybrid/_pipeline_test/.
set -e
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
PY=.venv/bin/python; T=hybrid/_pipeline_test
echo "== 1. regression: docs/palette_v1_vs_v2_terrain.png from concept/chibi_iso_v5.png"
$PY tools/hybrid/pixelize.py --regress
echo "== 2. pixelize with guides (round-9 iso renders -> their own 64 cells; Gemini sheet -> SE guide)"
for d in S SE E N NW; do
  $PY tools/hybrid/pixelize.py renders/model_round_9/iso_$d.png --guide renders/model_round_9/iso_${d}_64 --out $T/guide_test/turn_$d.png
done
mkdir -p $T/guide_test/guide; for d in S SE E N NW; do cp renders/model_round_9/iso_${d}_64.png $T/guide_test/guide/turn_$d.png; done
[[ -f hybrid/lock/wip/dir_SE_a.png ]] && $PY tools/hybrid/pixelize.py hybrid/lock/wip/dir_SE_a.png --pick 1 \
   --guide renders/model_round_9/iso_SE_64 --out $T/gem_test/turn_SE.png
$PY tools/hybrid/pixelize.py concept/chibi_iso_v5.png --guide none --height 56 --out $T/nog/turn_SE.png
echo "== 3. pixgrid round trip + palette lock"
mkdir -p $T/pixgrid
$PY tools/hybrid/pixgrid.py fromimg $T/nog/turn_SE.png --out $T/pixgrid/rt.pix
$PY tools/hybrid/pixgrid.py topng $T/pixgrid/rt.pix --out $T/pixgrid/rt.png
$PY tools/hybrid/pixgrid.py diff $T/nog/turn_SE.png $T/pixgrid/rt.png
printf 'legend:\nZ = #123456\ngrid:\nKRZ\n' > $T/pixgrid/bad.pix
if $PY tools/hybrid/pixgrid.py stats $T/pixgrid/bad.pix >/dev/null 2>&1; then echo "FAIL: off-palette accepted"; exit 1; else echo "palette lock OK (off-palette rejected)"; fi
echo "== 4. draw helpers"
$PY tools/hybrid/make_fixture.py
rm -rf $T/fixture_smear; cp -r $T/fixture $T/fixture_smear
$PY tools/hybrid/draw.py $T/fixture_smear/slash_SE_k1.png --out $T/fixture_smear/slash_SE_k1.png --preview 6 \
   "smear 66,80 30,16 190 345 6 tones=w,P,p taper=lead"
$PY tools/hybrid/draw.py new --new 32x32 --out $T/draw/arcs.png --preview 12 "arc 16,16 12 0 90 K" "arc 16,16 12,6 180 360 R" \
   "line 0,31 31,20 w" "curve 2,2 16,10 30,2 p" "streak 2,26 20,24 3 tones=w,p" "speed 30,14 -1,0 3 6 2 P"
echo "== 5. metrics"
$PY tools/hybrid/metrics.py $T/fixture_smear --json $T/fixture_metrics.json
echo "== 6. sheets + gifs"
$PY tools/hybrid/sheets.py contact $T/guide_test --out $T/sheets/contact_guide_test.png --cols 3
$PY tools/hybrid/sheets.py dirs $T/fixture --out $T/sheets/dirs8.png
$PY tools/hybrid/sheets.py set $T/fixture_smear --out $T/sheets/set.png --zoom 3
$PY tools/hybrid/gifs.py all $T/fixture_smear --out-dir $T/gifs --jump-z
$PY tools/hybrid/gifs.py compare $T/fixture $T/fixture_smear --labels r9,smear --out-dir $T/gifs
echo "SELFTEST OK"
