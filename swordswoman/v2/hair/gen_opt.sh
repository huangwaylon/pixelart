#!/bin/bash
# gen_opt.sh ID view : view=front|iso_SE ; makes opt/ID_view.png
cd /Users/waylonhuang/Documents/other/pixelart/swordswoman; id=$1; v=$2; o=v2/hair/opt/${id}_$v.png; [ -f $o ] && exit 0
case $id in
A) H="TWIN TAILS: long glossy dark twin tails tied high on each side of the head with two big red ribbon bows, tails falling past the shoulders to mid-back with a soft outward curve, soft wispy rounded bangs, short side locks framing the cheeks";;
B) H="SIDE PONYTAIL: long dark hair gathered into one big fluffy side ponytail on her left side tied with one big red bow, soft swept side bangs, long side lock framing the face on the other side";;
C) H="HIME CUT: long straight glossy dark hair to the waist, straight soft bangs, chin-length straight side locks (hime cut) framing the cheeks, a big red bow on the back of the head visible above the crown";;
D) H="ODANGO: two round buns (odango) on top of the head on each side, each with a short twin tail falling to the shoulders, small red ribbon bows at each bun, soft rounded bangs, side locks framing the cheeks";;
E) H="HALF-UP: long soft wavy dark hair to mid-back, the top half pulled back in a half-up style held by one big red bow at the back of the head (bow loops visible on both sides of the head), soft side-parted bangs, side locks framing the face";;
F) H="FLUFFY BOB + BRAIDS: fluffy rounded chin-length bob with soft inward curls, two thin side braids hanging in front of the ears to the collarbone tied with tiny red ribbons, and a big red bow on top of the head, soft wispy bangs";;
G) H="HIGH PONYTAIL: long dark ponytail tied high on the back of the head with a big red bow, ponytail falling to the waist with a lively curve, soft wispy bangs and long side locks framing the face, a small ahoge";;
H) H="LOW TWIN TAILS / LYRA-STYLE PIGTAILS: two fluffy short pigtails tied low behind the ears that flare outward, with red ribbons, a small red bow hair clip on one side, soft bangs, side locks";;
esac
F="a cute anime girl, Japanese anime style, Pokemon trainer character design (Ken Sugimori style), very large sparkling anime eyes with highlights, small nose, small smiling mouth, soft round cheeks, gentle friendly expression"
O="same outfit as the reference: red short kimono-dress with wide short sleeves, one grey-lavender obi sash, slender legs, dark short boots, small hands. NO sword, no weapon, empty hands"
if [ $v = front ]; then
P="Character design sheet: $F. Hairstyle: $H. Dark brown-black hair with glossy highlights. $O. Use the reference image ONLY for the body proportions (slim, about 3.5 heads tall), outfit and flat cel-shaded colours, but redesign the hair and face to be much cuter and more feminine. FRONT view, neutral standing pose facing the viewer, arms slightly away from the body. Single full-body figure on a plain white background, no text."
R="v2/design/turnE/front.png"
else
P="Draw the EXACT same character as the FIRST image (same cute anime face with large eyes, same hairstyle: $H, same outfit, same proportions and flat cel style and colours) in this view: 3/4 front view, body and face turned toward the lower-RIGHT of the picture, seen from a camera 30 degrees ABOVE her (top of the head visible, obi and hem curve downward like ellipses). The SECOND image shows ONLY the camera angle; do not copy its hair or face. NO sword. Single full-body figure on a plain white background, no text."
R="v2/hair/opt/${id}_front.png v2/design/turnE/iso_SE.png"
fi
for t in 1 2 3 4; do .venv/bin/python tools/gemini.py image "$P" $o $R > /dev/null 2>&1; [ -f $o ] && exit 0; sleep 30; done
echo FAIL $id $v
