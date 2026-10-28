#!/bin/zsh
# rj.sh JOBS.json OUTDIR [PARTS_DIR]  -> render jobs with the pose rig
P=${3:-/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pose/rig/parts_ph}
MOCAP=1 ELBOW=${ELBOW:-1} RIG_LIB_PATH=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/mocap/scripts/rig_lib.py /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P /Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/mocap/scripts/render_jobs.py -- $P $P/skel.txt $1 $2 2>&1 | grep -E "calib|ALLDONE|Error|rror:" | head -5
