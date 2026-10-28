#!/bin/zsh
# Render the guide STANDARD TEST SET + idle/walk/run/slash sequences (8 dirs) for one review pass.
#   tools/hybrid/render_guide_set.sh <pass> [res] [passes]
#   e.g. tools/hybrid/render_guide_set.sh p2 1024 clay,id,line,depth,mask,smear_mask,joints
# Poses: hybrid/guide/poses/src/ta (tools/hybrid/anim/ta_poses.py + pose_preview.py). One Blender job at a time.
set -e
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
P=${1:?pass}; RES=${2:-1024}; PASSES=${3:-clay,id,line,depth,mask,smear_mask,joints}
B=/Applications/Blender.app/Contents/MacOS/Blender
TA=hybrid/guide/poses/src/ta
OUT=hybrid/guide/${P}
rg() { $B -b --factory-startup -P tools/hybrid/render_guides.py -- --res ${RES} --passes ${PASSES} --out ${OUT} "$@" > /tmp/rg_${P}.log 2>&1 || { tail -30 /tmp/rg_${P}.log; exit 1; }; }
rg --pose ${TA}/turn.json --anim turn --dirs all
rg --anim-json ${TA}/anim_walk_SE_keys.json --dirs SE
rg --anim-json ${TA}/anim_slash_SE_keys.json --dirs SE
rg --anim-json ${TA}/anim_jump_E_keys.json --dirs E
for a in idle walk run slash; do rg --anim-json ${TA}/anim_${a}.json --dirs all; done
echo "rendered -> ${OUT}"
