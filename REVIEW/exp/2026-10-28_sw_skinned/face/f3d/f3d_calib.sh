#!/bin/zsh
# f3d_calib.sh : re-calibrate the face layout on R's current head/face_uv (UV-coded texture through render_motion.py at rest S) -> uvfit.json
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
T=$EXP/face/tex3d; mkdir -p $EXP/face/f3d/out/calR
mv $T $T.keep; mkdir -p $T; cp $EXP/face/f3d/tex/face_uvcode_mid.png $T/neutral.png
for v in ${=1:-S SE E}; do KINDS=guide $B -b $EXP/rig/rig.blend -P $EXP/render/render_motion.py -- rest $v $EXP/face/f3d/out/calR --no-post 2>&1 | grep -E "rror"; done
rm -rf $T; mv $T.keep $T
for v in ${=1:-S SE E}; do $PY $EXP/face/f3d/f3d_fit.py $v 2>&1 | grep -v Warn; done
