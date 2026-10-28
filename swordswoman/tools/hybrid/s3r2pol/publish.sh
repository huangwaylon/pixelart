#!/bin/zsh
# S3 r2 polish publish: polished/ -> metrics, gate, sheets, GIFs (hybrid/gifs/S3_editchain_r2_polished_*)
set -e
R=hybrid/S3_editchain/r2; P=$R/polished; V=$R/polwork/R
.venv/bin/python tools/hybrid/s3r2pol/polish.py
rm -rf $V; mkdir -p $V/sprite
ln -s ../../polished $V/std
cp $P/*.png $V/sprite/; cp $P/bonus/*.png $V/sprite/; cp -r $P/guide $V/sprite/guide
for f in $V/sprite/*.png; do .venv/bin/python -c "from PIL import Image;import sys;Image.open(sys.argv[1]).resize((512,512),Image.NEAREST).save(sys.argv[1][:-4]+'_4x.png')" $f; done
.venv/bin/python tools/hybrid/metrics.py $P --guide-map hybrid/S3_editchain/r1/guide_map.json --json $R/metrics_polished.json > $R/metrics_polished.txt 2>&1 || true
cp $R/metrics_polished.json $V/metrics.json
.venv/bin/python tools/hybrid/h3/gate.py $V > $R/gate_polished.txt; cat $R/gate_polished.txt
.venv/bin/python tools/hybrid/h3/sheet.py $V; cp $V/sheet.png $R/polished_sheet.png
.venv/bin/python tools/hybrid/sheets.py set $P --out $R/polished_set_3x.png --zoom 3 | tail -1
.venv/bin/python tools/hybrid/sheets.py dirs $P --out $R/polished_dirs8.png --bg grass | tail -1
.venv/bin/python tools/hybrid/sheets.py contact $P --out $R/polished_contact.png --cols 4 | tail -1
T=$R/gifs_polished_tmp; rm -rf $T
.venv/bin/python tools/hybrid/gifs.py all $P --out-dir $T --slow 4 | tail -1
.venv/bin/python tools/hybrid/gifs.py anim $P --out-dir $T --only slash_SE --ms 220,50,180,260 | tail -1
.venv/bin/python tools/hybrid/gifs.py compare $R/std $P --labels r2,polished --out-dir $T/cmp --zoom 3 | tail -1
mkdir -p hybrid/gifs; setopt null_glob; rm -f hybrid/gifs/S3_editchain_r2_polished_*
for f in $T/*.gif; do cp $f hybrid/gifs/S3_editchain_r2_polished_${f:t}; done
for f in $T/cmp/*.gif; do cp $f hybrid/gifs/S3_editchain_r2_polished_beforeafter_${f:t}; done
.venv/bin/python tools/hybrid/h3/bonus_gif.py $V hybrid/gifs/S3_editchain_r2_polished
ls hybrid/gifs | grep S3_editchain_r2_polished_
