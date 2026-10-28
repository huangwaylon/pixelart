#!/bin/zsh
# try.sh VIEW CROPFILE X0 Y0 : paste crop into work/EC0_VIEW_96 (PROTECT env = protected boxes) -> temp; fidelity gate vs master0,
# eye-spec check (eyecheck.py), compare png (ref | work | yours) at CROPFILE_cmp.png
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman; PY=$R/.scratch/pixtools/venv/bin/python; M=$R/v2/m96
v=$1; f=$2; x0=$3; y0=$4; T=/tmp/m96try_$$_$RANDOM; mkdir -p $T
$PY -I $M/tools/paste.py $M/work/EC0_${v}_96 $f $x0 $y0 $T/EC0_${v}_96 >/dev/null && cp $M/work/EC0_${v}_96.json $T/
echo "GATE vs the ORIGINAL auto sprite (cumulative, info):"; $PY -I $M/tools/m96.py gate $T $v | cut -c1-120
echo "DELTA vs the CURRENT sprite (your crop only; must satisfy ssim_b >= -0.0015, dE <= +0.06, sil >= -0.002, lint O1/S4/O3 not higher):"; M96_BASE=$M/work $PY -I $M/tools/m96.py gate $T $v
if [ -n "$EYECHECK" ]; then echo "EYE SPEC CHECK:"; python3 $M/tools/eyecheck.py $T/EC0_${v}_96.txt $v neutral | cut -c1-400; fi
n=$(wc -l < $f); w=$(head -1 $f | tr -d '\n' | wc -c); $PY -I $M/tools/cmp.py $x0 $y0 $((x0+w)) $((y0+n)) ${f%.txt}_cmp.png 8 $(dirname $f)/ref_hi.png $M/work/EC0_${v}_96 $T/EC0_${v}_96 >/dev/null; echo "compare image: ${f%.txt}_cmp.png (ref_hi | current | yours)"; rm -rf $T
