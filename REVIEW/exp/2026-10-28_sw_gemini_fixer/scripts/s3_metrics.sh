#!/bin/zsh
# fidelity (metrics.py, pixtools venv) + identity (s3_identity.py) for step-2 outputs
cd ${0:A:h}/..
PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
FX=/Users/waylonhuang/Documents/other/pixelart/.models/pixel-art-fixer/venv/bin/python
MT=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools/metrics.py
$PY -I $MT work/ref/master_SE work/proc/a*_r96.txt work/proc/a*_r96L2.txt work/proc/a*_nat.txt work/proc/EC0_c_*.txt --json work/proc/metrics.json 2>&1 | grep -v Warn > work/proc/metrics.txt
$FX -I scripts/s3_identity.py work/proc/identity.json work/proc/a*_r96.txt work/proc/a*_r96L2.txt work/proc/b*_r96.txt work/proc/b*_r96L2.txt work/proc/EC0_c_*.txt > work/proc/identity.txt
for m in hn gh; do
  $FX -I scripts/s3_identity.py work/proc_$m/identity.json work/proc_$m/[bc]_*.txt > work/proc_$m/identity.txt
done
