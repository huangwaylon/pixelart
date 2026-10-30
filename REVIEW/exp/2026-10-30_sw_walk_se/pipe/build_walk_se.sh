#!/bin/zsh
# build_walk_se.sh -- DESIGN_LOCK walk SE build (deterministic; ~1 min).  pipe/out/walk_SE/: f00..f07.png, walk_SE_4x.gif,
# walk_SE_strip1x.png, gates.json (+ compare/).  Exit 1 if a blocking gate fails.  Steps (NOTES.md):
#   1a rig copy (sleeves, waist, flat face, bow, part ids, eye vertices)   1b spring re-bake (10 bones) + posture gate
#   1c 8x passes   2-4 lock chain (colour, vector outline, overlap lines, face)   5 gates   6 compare (round 10, gold frames)
set -e
H=${0:A:h}; cd $H
SK=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
W=$H/work/walk_SE; O=$H/out/walk_SE; mkdir -p $W $O
[ -f face_calib.json ] || $PY calib_face.py                                                     # step 4 calibration (once)
$B -b $SK/rig/rig.blend -P make_rig_lock.py -- $H/rig_lock.blend $H/face_calib.json 2>&1 | grep -E "^LOCK|Error"   # 1a
$PY bake_walk_lock.py $H/walk_lock.json | grep -E "BAKED|seam"                                   # 1b
$B -b rig_lock.blend -P render_lock.py -- $H/walk_lock.json SE $W 2>&1 | grep -E "LOCK_RENDERED|Error"            # 1c
$PY lock_chain.py $W/walk_SE.json $O                                                             # 2-4
$PY export.py $O $W/walk_SE.json
$PY gates.py $O $W/walk_SE.json $H/walk_lock.json $O/walk_SE_4x.gif | tee $O/gates.txt              # 5
$PY compare.py $O                                                                                # 6
grep -q "^GATES PASS" $O/gates.txt
