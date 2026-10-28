#!/bin/zsh
# Critiques: Gemini Argon + Opus on the key boards. Writes critique/*.md and fails on empty output.
E=/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_snowpeak_hires
mkdir -p $E/critique
P="You are a strict senior pixel-art director. Do NOT inflate. Image 1: a 48x64-cell isometric chibi sprite (34 px tall), idle frame, 8 directions, at 4x nearest. Row 1 'N' = the SHIPPED native pixel pass (custom raycaster at sprite resolution, 3x3 supersampling). Rows 2-5 = the SAME 3D model/pose/camera rendered at 8x resolution then downscaled to 48x64 by: VM = majority material then majority shading band; KC = k-centroid per cell then palette lock; PF = Retro Diffusion pixel-art-fixer forced grid then palette lock; KCE = KC plus interior lines from hi-res normal/depth discontinuities. All rows then went through the same rule-based fix chain (face decals, outline/sel-out, despeckle). Image 2: same at 1x. Image 3: walk cycle SE, 8 frames, rows N | KC | PF | KCE. Tasks: (1) For EACH of VM, KC, PF, KCE give an explicit A/B verdict vs N: better / same / worse, plus a 1-10 score for N and each. (2) List concrete pixel problems by row+direction (e.g. 'PF SE: 2px light streak across fringe'): stray pixels, broken clusters, banding, noise, line breaks, walk-strip flicker. (3) Does high-res rendering fix any of these known issues: flat beige coat slab, teal mitten islands mid-coat in SE/SW, stub legs, blob hands, small bow in S, fringe ridges? yes/no each. (4) Ship recommendation: keep N or switch to which method. Terse; numbers first."
IMGS=($E/boards/00_key_S4_hd2_idle_8dir_4x.png $E/boards/00_key_S4_hd2_idle_8dir_1x.png $E/boards/01_S4_hd2_walk_SE_strip_4x.png)
if [[ "$1" == "gemini" ]]; then
  cd /Users/waylonhuang/Documents/other/pixelart/swordswoman
  .venv/bin/python tools/gemini.py ask "$P" $IMGS > $E/critique/gemini_argon.md 2> $E/critique/gemini_argon.err
fi
if [[ "$1" == "opus" ]]; then
  zsh -ic "claude-as be_system --dangerously-skip-permissions --model claude-opus-5-5 -p \"Read these images with your Read tool: ${IMGS[1]} ${IMGS[2]} ${IMGS[3]} . Then answer: $P\"" > $E/critique/opus.md 2> $E/critique/opus.err
fi
f=$E/critique/$([[ "$1" == "gemini" ]] && echo gemini_argon || echo opus).md
[[ -s $f ]] || { echo "EMPTY critique $f"; exit 3; }
wc -c $f
