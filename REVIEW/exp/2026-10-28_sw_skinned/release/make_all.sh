#!/bin/zsh
# make_all.sh (I, round 4): one command for the whole review set.
#   zsh release/make_all.sh            -> release/out/<build_id>/ (+ release/out/latest), GATES.md, hub entry; PANEL=1 also runs the critic panel
# env: DIRS="SE E S" (default: every view in rig/align.json), ACTS="walk run" (default: every action in release/actions.json with a motion file),
#      JOBS=6 (parallel clips), FORCE=1 (rebuild even if release/out/<build_id> is complete), PANEL=1 (run release/panel.sh at the end)
# build_id = YYYYMMDD_<sha1[:7] of every input file: rig, align, textures, motion files, R/P/F code, release code>.
# Blender passes are cached by input hash in release/work/cache/ (gitignored); per-frame outputs live in release/out/<build>/work/ (gitignored).
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
PY=/Users/waylonhuang/Documents/other/pixelart/.models/pixtools/venv/bin/python
R=$EXP/release; cd $R || exit 1
PLAN=($($PY $R/rl.py plan)); BID=$PLAN[1]; CLIPS=($PLAN[2,-1])
B=$R/out/$BID
echo "BUILD $BID  clips: $CLIPS"
if [ -f $B/GATES.md ] && [ -z "$FORCE" ]; then echo "build $BID already complete (FORCE=1 to redo)"; else
  mkdir -p $B/work; t0=$(date +%s)
  print -l $CLIPS | xargs -P ${JOBS:-6} -I{} zsh -c 'c={}; '"$PY $R/rl.py"' clip '"$BID"' ${c%%:*} ${c##*:}' 2>&1 | grep -E "^CLIP|Traceback|Error" | tee $B/work/clips.txt
  $PY $R/rl.py assemble $BID 2>&1 | grep -v Warn
  $PY $R/rl.py gates $BID 2>&1 | grep -v Warn | tail -3
  echo "built in $(( $(date +%s) - t0 )) s"
fi
ln -sfn $BID $R/out/latest
[ -n "$PANEL" ] && zsh $R/panel.sh $BID
$PY $R/rl.py hub $BID 2>&1 | tail -5
echo "MAKE_ALL_DONE $BID"
