#!/bin/zsh
# faceround.sh IN_DIR OUT_DIR : face round 2 pass (faithful face) on finished masters with the PREVIOUS neutral face
# (default IN = snap/v11_preface2/masters): tools/face2build.py (clean old marks -> GEO contour px -> new anchor -> neutral
# cat-eye face; eye round: arched lid + outer flicks per eye_spec) + gates; then heads: stamp.py heads OUT_DIR heads. (Round-1 version: snap/v11_preface2 + handfix.py.)
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman; M=$R/v2/m96; I=${1:-$M/snap/v11_preface2/masters}; O=$2; mkdir -p $O
$R/.venv/bin/python $M/tools/face2build.py $I $O
for v in S SE E; do python3 $M/tools/eyecheck.py $O/EC0_${v}_96.txt $v --anchor $M/heads/anchor.json | head -1 | cut -c1-120; done
$R/.venv/bin/python $R/v2/qc/qc_gate.py masters $O --out - 2>&1 | grep -E "^QC|^   - " | cut -c1-200
