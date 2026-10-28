#!/bin/zsh
# runface.sh VIEW X0 Y0 TAG ACCOUNT : Opus face pass (brief_face3) on art/f<VIEW>
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96; v=$1; x0=$2; y0=$3; t=$4; acc=$5; D=$R/art/f$v; mkdir -p $D/$t; cp $D/*.txt $D/*.png $D/$t/ 2>/dev/null
typeset -A K; K=(S "front_left (left eye in the image) and front_right (right eye)" SE "front_left (near eye, left in the image) and far (far eye, right, at the cheek edge)" E "front_left (the one visible eye; same block as the front views, face front is on the right)")
B=""; for k in $(python3 -c "import json;print(' '.join(json.load(open('$R/eye_spec.json'))['kinds_by_view']['$v']))"); do B="$B
$k:
$(python3 -c "import sys; sys.path.insert(0,'$R/tools'); import eyetmpl as E; print('\n'.join(E.kind_tmpl('$k','neutral')))")"; done
b=$(sed "s#DIR#$D/$t#g; s#X0#$x0#g; s#Y0#$y0#g; s#VIEWCODE#$v#g" $R/art/brief_face3.md)
b=${b//BLOCKS/"View $v uses: ${K[$v]}.$B"}
zsh -ic "claude-as $acc --dangerously-skip-permissions --model claude-opus-5-5 -p \"\$(cat)\"" <<<"$b" > $D/$t/log.txt 2>&1
echo "$v$t: $(tail -1 $D/$t/log.txt | cut -c1-220)"
