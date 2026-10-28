#!/bin/zsh
# make_rig.sh SPEC.json NAME  -> v2/hy3d/rigs/NAME/{parts/ (glbs+pivots.json+skel.txt+spec_solved.json), rig_parts.blend, rest_{SE,E,S}/f00_{matid,shade}.png}
# Re-proportions partsAB4f (AB4 + facefix head) with SPEC (multipliers and/or "targets"), then builds the rigid-parts rig blend.
set -e
H=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hy3d; SPEC=$1; NAME=$2; O=$H/rigs/$NAME
mkdir -p $O
/Users/waylonhuang/Documents/other/pixelart/.models/hy_omni/venv/bin/python -I $H/scripts/reproportion_solve.py $SPEC $H/partsAB4f $H/best/skel.txt $O/parts 2>&1 | grep -E "iter|final|measure|reproportioned" | tail -3
echo '{"rest": {"rest": {}}}' > $O/rest_keys.json
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P $H/scripts/rig_parts.py -- $O/parts $O/parts/skel.txt $O/rest_keys.json $O rest SE,E,S 2>&1 | grep -E "^DONE|Error" || true
echo "rig: $O/rig_parts.blend  parts: $O/parts"
