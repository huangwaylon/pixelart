#!/bin/sh
# External art critique by Gemini 4 Argon via `pi` (read-only, no session).
#   pipeline/tools/gemini_critique.sh <name> "<context/question>" img1.png [img2.png ...]
# Writes docs/review/gemini/<name>.md
set -e
pipeline/tools/gemini_auth.sh || exit 1
name="$1"; ctx="$2"; shift 2
files=""
for f in "$@"; do files="$files @$f"; done
sys="You are a veteran Japanese pixel-art (dot-e) art director and animator who has shipped GBA/DS-era and modern \
hand-pixelled games. You give blunt, specific, actionable critique. Always: (1) overall verdict in one line, \
(2) top 5 problems ranked by impact, each with the exact location (image, view/frame, approximate pixel x,y or region) \
and a concrete pixel-level fix (what to draw, how many px, which colour role), (3) what is working and must be kept, \
(4) one stretch suggestion to raise appeal. Judge appeal, readability at 1x, silhouette, line quality (jaggies, \
pixel-perfect curves, orphans), shading, colour, anatomy, consistency across views, and animation principles where relevant."
out="docs/review/gemini/$name.md"
{ echo "# Gemini 4 Argon critique: $name"; echo; echo "_Context:_ $ctx"; echo; echo "_Images:_ $*"; echo; } > "$out"
perl -e "alarm 420; exec @ARGV" pi -p --model apple-gemini/gemini-4-argon --no-session --no-context-files --no-tools \
   --append-system-prompt "$sys" $files "$ctx" >> "$out" 2>&1
echo "wrote $out"
