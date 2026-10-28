#!/bin/zsh
# panel.sh <build_id> (I): critic panel on a release build -> release/out/<build>/panel/{ad,anim,game}_opus.txt, argon.txt, synth.txt,
# then PANEL.md (+ panel_scores.json).  Opus = claude-opus-5-5 via claude-as (3 roles), Gemini Argon (asked for concrete issues only).
EXP=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned
B=$EXP/release/out/$1; P=$B/panel; mkdir -p $P
ACTS=($(python3 -c "import json;print(' '.join(json.load(open('$B/manifest.json'))['actions']))"))
DIRS=$(python3 -c "import json;m=json.load(open('$B/manifest.json'));print(' '.join(list(m['actions'].values())[0]['dirs']))")
SHEETS=(); PVS=(); STRIPS=()
for a in $ACTS; do SHEETS+=($B/$a/${a}_sheet.png); [ -f $B/$a/${a}_preview_sheet.png ] && PVS+=($B/$a/${a}_preview_sheet.png); STRIPS+=($B/$a/${a}_strip1x.png); done
MASTER=$B/masters_ref.png
GATES=$(sed -n '/^| clip/,/^\*\*Totals/p' $B/GATES.md | tr '\n' ' ' | tr '"' "'" | head -c 3500)
CTX="Character: 'swordswoman', a chibi girl game sprite (~3 heads tall, 96-px-tall master art in a 128 px cell): dark-brown bob with bangs + side locks, back bun, big red bow; red short kimono-dress with big bell sleeves, a lavender/dark obi, flared short skirt, red sock-top band and black thigh-high socks, boots. She is rendered from a skinned 3D rig through a pixel-art conversion; the face is hand-drawn pixel parts placed on 3D head anchors. Owner direction: whole-body lively bouncy motion, hair/bow/skirt/sleeves bouncing, elegant confident feminine posing (never slouched), faces must follow the head and be expressive per action, legs/limbs must never vanish or detach, GIFs loop smoothly. Actions: ${ACTS} ; directions: ${DIRS} (S = facing camera, E = profile facing screen-right, N = back). The team: R = rig/mesh/skirt+head geometry/camera+alignment per direction; M = motion (poses, timing, spring secondary, expression cues per frame); P = pixel conversion (outline, shading, limb shapes, temporal flicker, smear frames, GIF writing); F = face parts (eyes, brows, mouth, blush, expressions, placement on the head)."
FMT="Answer in <= 350 words. First line exactly 'SCORE: N/10' (be strict: 5 = usable but flawed, 7 = good shippable game quality, 9 = AAA). Then 1-10 sub-scores for each criterion listed. Then 'ISSUES:' = the 6 most important concrete problems, most important first, each as one line: '[OWNER R|M|P|F] action direction frames: problem -> concrete fix'. No praise padding."
AD="You are the ART DIRECTOR of a 2D pixel-art game (Octopath / Sea of Stars / Pokemon overworld standards). $CTX Judge: (1) on-model vs the m96 master sprites (first image = the approved masters per direction; mirrored W/SW/NW), (2) pixel quality: clean outlines, no orphan pixels/jaggies, readable shading, consistent palette, silhouette, (3) consistency of the design across directions, (4) face rendering quality. Criteria to sub-score: on-model, outline/cleanliness, shading/form, silhouette, face. $FMT"
AN="You are the ANIMATION DIRECTOR (Richard Williams mechanics, 12 principles, PMD/Pokemon/Sea of Stars sprite animation). $CTX Judge: liveliness, bounce, whole-body motion and overlap (hair, bow, skirt, sleeves), posing elegance/confidence/femininity, no slouch, weight and timing per action, faces follow the head and are expressive per beat. Pixel contact sheets show every frame (frame number + ms); smooth-preview sheets show the same motion in 3D. Criteria to sub-score: key poses/appeal, timing/spacing, bounce/weight, secondary motion, posture (no slouch), face acting. $FMT"
GD="You are the GAME DIRECTOR shipping this sprite in a top-down/3-4 view action RPG. $CTX Judge: readability at 1x (the *_strip1x images are TRUE in-game size: rows = directions, columns = frames; also look at the 3x contact sheets), consistency across the directions (does she look like the same character, same size and ground line, same timing, no direction noticeably worse), action readability (can a player tell walk/run/idle/jump/dash/hurt apart at a glance), timing feel. The gate table from our automated checks is: $GATES . Criteria to sub-score: 1x readability, direction consistency, action clarity, timing/feel, ship-readiness. $FMT"
opus() { # role out images...
  local Q=$1 O=$2; shift 2
  for t in 1 2; do
    zsh -ic "claude-as be_system --dangerously-skip-permissions --model claude-opus-5-5 -p \"$Q  Use the Read tool to view these images (absolute paths): $* . Do not modify any files.\"" > $O 2>/dev/null
    grep -q "SCORE" $O && break; echo "retry $O"
  done
}
argon() {
  (cd /Users/waylonhuang/Documents/other/pixelart/swordswoman && for t in 1 2; do
    .venv/bin/python tools/gemini.py ask "You are a strict panel of three: art director, animation director, game director. $CTX Images: first = approved m96 master sprites per direction; then pixel contact sheets (3x) per action; then smooth-preview sheets per action. Do not inflate scores and do not praise: list concrete issues. $FMT Give one SCORE line per role as 'SCORE AD: N/10', 'SCORE ANIM: N/10', 'SCORE GAME: N/10' (the first line must still be 'SCORE: N/10' = overall)." $MASTER $SHEETS $PVS > $P/argon.txt 2>&1
    grep -q "SCORE" $P/argon.txt && break; echo "retry argon"; done)
}
opus "$AD" $P/ad_opus.txt $MASTER $SHEETS &
opus "$AN" $P/anim_opus.txt $SHEETS $PVS &
opus "$GD" $P/game_opus.txt $STRIPS $SHEETS &
argon &
wait
for f in $P/ad_opus.txt $P/anim_opus.txt $P/game_opus.txt $P/argon.txt; do echo "$(basename $f): $(grep -m1 SCORE $f) ($(wc -c < $f) bytes)"; done
python3 - $B <<'EOF'
import json, re, sys, os
B = sys.argv[1]; P = B + '/panel'; sc = {}
for k, f in (('Opus AD', 'ad_opus'), ('Opus anim', 'anim_opus'), ('Opus game', 'game_opus'), ('Argon', 'argon')):
    t = open(f'{P}/{f}.txt').read() if os.path.exists(f'{P}/{f}.txt') else ''
    m = re.search(r'SCORE:\s*([\d.]+)\s*/\s*10', t); sc[k] = f'{m.group(1)}/10' if m else 'n/a'
json.dump(sc, open(f'{B}/panel_scores.json', 'w')); print(sc)
EOF
echo PANEL_RAW_DONE
