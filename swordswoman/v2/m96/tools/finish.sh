#!/bin/zsh
# finish.sh SRC_DIR OUT_DIR : re-runnable finishing pass on polished masters: eye isolation (eyeiso.py) + cleanup.py, then gates
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman; PY=$R/.scratch/pixtools/venv/bin/python; M=$R/v2/m96
S=$1; O=$2; mkdir -p $O; cp $S/EC0_*_96.{txt,json} $O/
for v in S SE E; do python3 $M/tools/eyeiso.py $O/EC0_${v}_96 $v; done
for v in S SE E NE N; do $PY -I $M/tools/cleanup.py $O/EC0_${v}_96 $v; done
for v in S SE E; do python3 $M/tools/eyecheck.py $O/EC0_${v}_96.txt $v | head -1 | cut -c1-140; done
$R/.venv/bin/python $R/v2/qc/qc_gate.py masters $O --out - 2>&1 | grep -E "^QC|^   - " | cut -c1-200
$PY -I $M/tools/m96.py gate $O | cut -c1-175
