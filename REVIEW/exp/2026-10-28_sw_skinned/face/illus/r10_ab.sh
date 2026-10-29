#!/bin/zsh
# r10_ab.sh : A/B on R's current renderer: round-9 set (out_r9) vs round-10 set (out_r10); ends with out = out_r10
cd /Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/face/illus
rm -rf r9/r9c r9/r10c
rm -rf out; cp -R out_r9 out; touch out/*/*.png; zsh r9_test.sh r9c
rm -rf out; cp -R out_r10 out; touch out/*/*.png; zsh r9_test.sh r10c
/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python r9_eval.py r9c r10c
echo AB_DONE
