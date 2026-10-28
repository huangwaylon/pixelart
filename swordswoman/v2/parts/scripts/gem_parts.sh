#!/bin/zsh
# gem_parts.sh [part ...] -> v2/parts/B/gem/<part>_<view>.png  (Gemini edit of the locked turnD views: keep ONLY one part)
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
G=(.venv/bin/python tools/gemini.py image); T=v2/design/turnD; O=v2/parts/B/gem
BASE="This is one view of a character turnaround of a chibi girl. Redraw ONLY the %s, isolated as a single separate object on a pure flat white background. Keep EXACTLY the same viewpoint, size, position and angle as in the reference image, and the same flat cel-shaded style, colours and dark outline. Remove everything else (%s). Fill in any surfaces that were hidden by the removed parts so the part is complete and solid. No cast shadow, no ground, no text, no extra objects."
declare -A W O_
W[head]="head: the black bob hair with blunt bangs, the face with the big blue eyes, the small hair bun at the back of the crown and the big red bow tied on top. Cut it cleanly at the neck just under the chin and hair"
O_[head]="the neck, body, dress, arms, legs and boots"
W[torso]="upper body only: the red kimono-dress bodice from the base of the neck down to just below the dark obi belt band, including the obi band. NO arms and NO sleeves: cut cleanly at the shoulders and show plain rounded red shoulder caps. NO head: show only a short skin neck stump. NO skirt below the obi"
O_[torso]="the head, hair, bow, both arms and sleeves, the flared skirt, legs and boots"
W[skirt]="flared red A-line skirt part of the dress only, from just below the dark obi belt down to the flared hem, as one separate rigid bell-shaped piece (open at the bottom)"
O_[skirt]="the head, hair, bow, torso, obi, arms, sleeves, legs and boots"
W[leg]="ONE leg only: the %s, a bare pale leg from the top of the thigh at the hip down to the foot, wearing the simple dark short rounded boot. Show the whole thigh as if the dress were removed"
O_[leg]="the head, hair, bow, dress, skirt, torso, arms, and the other leg"
W[arm]="ONE arm only: the %s, the wide red bell sleeve with the darker red inside opening and the small round skin-coloured mitten hand, hanging at the same A-pose angle. Cut it cleanly at the shoulder with a rounded top"
O_[arm]="the head, hair, bow, torso, dress, skirt, legs, and the other arm"
job() { p=$1; v=$2; ref=$3; which=$4
  w=${W[$p]}; [[ $w == *%s* ]] && w=$(printf "$w" "$which")
  pr=$(printf "$BASE" "$w" "${O_[$p]}")
  [[ -s $O/${p}_$v.png ]] || $G[@] "$pr" $O/${p}_$v.png $T/$ref.png > $O/${p}_$v.log 2>&1; }
for p in ${@:-head torso skirt leg arm}; do
  a=leg; [[ $p == arm ]] && a=arm; job $p front front "$a on the LEFT side of the image (her right $a)" &
  job $p left left "$a nearest to the viewer" &
  job $p back back "$a on the RIGHT side of the image (her right $a)" &
done
wait
