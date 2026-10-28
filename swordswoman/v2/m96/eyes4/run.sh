#!/bin/zsh
# eyes4/run.sh VARIANT : spec variant -> eyes4/<V>/m (masters) + eyes4/<V>/h (heads) + gates + sheet
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman; M=$R/v2/m96; V=$1; O=$M/eyes4/$V
python3 $M/eyes4/setspec.py $V >/dev/null
zsh $M/tools/faceround.sh $M/snap/v11_preface2/masters $O/m 2>&1 | tail -6
python3 $M/tools/stamp.py heads $O/m $O/h >/dev/null
for f in $O/h/{S,SE,E}_*.txt; do python3 $M/tools/eyecheck.py $f $(basename $f | cut -d_ -f1) --anchor $M/heads/anchor.json; done > $O/eyecheck.txt; echo "eyecheck OK $(grep -c '^OK' $O/eyecheck.txt) FAIL $(grep -c '^FAIL' $O/eyecheck.txt)"; grep '^    ' $O/eyecheck.txt | cut -c1-220 | sort | uniq | head -8
$R/.venv/bin/python $R/v2/qc/qc_gate.py stamps $O/h --masters $O/m --out - 2>&1 | grep -E "^QC|^   - " | cut -c1-200 | head -8
$R/.venv/bin/python $M/tools/eyesheet.py $M/snap/v13_preeyefix/heads $O/h $O/eyes.png >/dev/null
