#!/bin/bash
# mkprompt.sh VIEW ROUND [extra-notes-file] -> prints prompt for Opus pixel artist
n=$1; r=$2; X=$3; M=/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/design/m48
case $n in
S) F="S = facing the viewer straight on (front), symmetric, camera 30 deg above: we see the top of the skull above the bow line; the bun is only a sliver/notch behind the bow; both eyes, face sits low in the head; obi and hem are slight downward curves.";;
E) F="E = TRUE right-facing profile (she faces screen-right), camera 30 deg above: ONE eye only (near eye, on the right side of the face), the face edge/cheek is the right edge of the head, small nose bump optional; bob covers the ear; bun at the BACK (screen-left) of the head, bow on the crown just in front of the bun, seen from the side (one loop + knot visible, ribbon edge-on); only the near arm visible as a sleeve block hanging over the body side with a mitten at the hem; legs: near leg in front, far leg slightly behind (both visible as a 2-leg stack or offset by 1-2px).";;
NE) F="NE = 3/4 BACK view, she faces away toward the upper-right, camera 30 deg above: no eyes; a sliver of cheek/jaw skin may show on the right edge of the head; the bun is the round knob at the centre-back of the crown, the bow sits on the crown just beyond it (shifted toward the left as in the 3D render); hair bob from behind (clean blunt bottom edge), obi seen from behind, both sleeves, legs and boots from behind.";;
N) F="N = straight BACK view, symmetric, camera 30 deg above: no face; the round bun is centred on the back of the crown, overlapping the bow knot; the bow is ONE bow (centre knot + two solid flat loops) seen from behind/above; the top of the skull hair is visible above the bow; hair bob from behind with clean blunt bottom edge; obi band across the back, sleeves, legs, boots from behind.";;
esac
cat <<P
You are a professional pixel artist. Draw ONE 48px pixel-art master sprite of a chibi swordswoman as a 64x64 CHAR-MAP text file, view $n (no katana).
$F

Files (read them all; PNGs are images):
- ANCHOR (style + proportion authority, view SE): $M/work/SE_anchor.txt (char-map) and $M/work/SE_anchor_8x.png. Copy its palette use, outline style, eye construction (dark lash row of '#', then 'w'+'i' / 'iIi' / 'III' 3x3 eye under it), bow construction (flat E/e/R loops, r/# underside, 1px '#' outline), hair (flat 2-tone H base + h shadow side, NO noise), mitten hands, skin, obi, boots, and pixel density exactly.
- DESIGN reference for this view (what she looks like from this side): $M/work/ref_$n.png
- CAMERA/ANGLE authority (3D render at exactly 30 deg elevation; follow it for facing, bow/bun placement, foreshortening): $M/work/mat_$n.png
- Rough auto-probes (noisy, for placement only): $M/probe/${n}_u.txt (design) and $M/probe/${n}_mat.txt (3D render).
- Palette legend (char hex role): $M/work/legend.txt. '.' = transparent. Use ONLY these chars. Do not use p (blush), j, u, U. k only for katana.
$( [ -n "$X" ] && echo "- FEEDBACK from the previous round you MUST fix: $(cat $X)" )
$( [ -f $M/work/${n}_r$((r-1)).txt ] && echo "- Your previous version: $M/work/${n}_r$((r-1)).txt (start from it; fix the feedback, keep what is good)." )

HARD proportion lock (same as the anchor so all views match; head-size drift must be <=1px):
- bow topmost pixel row 10-11; skull/hair outline top row 16 (+-1; for S/N the skull top may show above the bow knot); hair+head block 23 cols wide incl. outline (+-1), rows 16-35; chin/hair bottom row 35; neck/collar row 36.
- body: sleeves+torso rows 36-46, obi band rows 41-43, skirt hem outline row 50, legs rows 51-55, boots rows 55-58, bottom outline row 59 = ground row (feet on row 59 like the anchor). Body centred on column 30.
Rules: clean selective dark '#' outline (1px, no doubled lines, no jaggies: stairs regular); no orphan or noise pixels; every cluster deliberate (>=2px except eye glints/single highlight accents); hair = flat 2-tone clusters; bow flat with a 1px '#' outline so it separates from hair AND dress; light comes from upper-left (light ramp e/2/H on left, shadow R/h on right); mitten hands (2x2-ish skin blob with '1' shadow); boots readable (d/D with # outline, 2 separate feet).

Process: write the char-map to $M/work/${n}_r$r.txt (exactly 64 lines x 64 chars). Self-check with:
  /Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python $M/tools/cm.py render $M/work/${n}_r$r.txt $M/work/${n}_r${r}_8x.png --s 8 --bg
  /Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python $M/tools/cm.py lint $M/work/${n}_r$r.txt
then Read the 8x png, compare side by side with the anchor 8x png and the references, and fix until it is clean and on-model. Finish by replying with ONE short line.
P
