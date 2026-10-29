#!/bin/zsh
# r9_ab.sh : A/B on the same renderer version: base (out_r7) then enhanced (out_r9); `out` is pointed at each set in turn, ends on out_r9
cd /Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/face/illus
rm -rf out; cp -R out_r7 out; touch out/*/*.png; zsh r9_test.sh baseB
rm -rf out; cp -R out_r9 out; touch out/*/*.png; zsh r9_test.sh r9b
/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python r9_eval.py baseB r9b
echo AB_DONE
