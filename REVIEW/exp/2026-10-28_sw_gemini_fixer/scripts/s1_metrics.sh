#!/bin/zsh
cd ${0:A:h}/..
PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
FX=/Users/waylonhuang/Documents/other/pixelart/.models/pixel-art-fixer/venv/bin/python
MT=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools/metrics.py
$PY -I $MT work/ref/master_SE work/ref/master_S work/ref/master_E /Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/masters/EC0_SE_96 work/base/*_r96.txt work/base/*_r96L2.txt --json work/base/metrics_r96.json 2>&1 | grep -v Warn > work/base/metrics_r96.txt
$FX -I scripts/s3_identity.py work/base/identity.json work/base/*_r96L2.txt > work/base/identity.txt
