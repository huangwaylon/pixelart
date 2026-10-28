# v2/heads: shared ROUND CHIBI SKULL head set (owner: anim_redraw strand)
## r1 (2026-10-26)
- Lead/panel: all heads read as boxy helmets. Target: domed crown, hair bulging past temples, cheeks tapering to a soft chin, bun always, bow on top, SE eyes/identity, ~23px wide.
- Format = anim_cut cm.py char-maps; head part pivot = neck, anchors bow/bun; bun behind, bow in front. tools/preview.py composes by anchors -> png/<view>_<v>_{1x,6x}.png, png/<view>_<v>_full.txt, png/sheet.png.
- Opus (be_system, foreground) prompt: prompt_r1.txt.
## r1 result (2026-10-26)
- SE head 23x20 (squash 25x18), pivot neck (13,18) [lean (12,17) = head +1x +1y; squash (14,16)]; anchors bow (9,3) bun (8,-4) [squash bow (10,3) bun (9,-4)].
- E head 22x20 (squash 24x18), pivot (13,18) [lean (12,17); squash (15,16)]; anchors bow (11,2) bun (4,-2) [squash (12,2)/(5,-2)].
- bun anchors have NEGATIVE y (bun centre sits above the head grid, peeking over the knot). Bow anchor is set slightly back of centre so the front dome stays visible (matches iso_SE/iso_E refs).
- bun 7x7 pivot (3,3) both views; SE bow 17x8 pivot (9,7) (anim_cut bow + e lights), bow_squash 19x7 (10,6); E bow = pinched bow-tie 13x7 (6,5), bow_squash 15x6 (7,4) (the boxy E loops read as "red ears").
- Variants derived by crit/gen_se.py / crit/gen_e.py from head_neutral (re-run after editing neutral; squash is hand-drawn). cm.py lint "orphans" left = intentional glints/mouth/diagonal outline steps.
## r2 (2026-10-26) - after crit r1 (argon 5.5, opus 4: "ball with a face window")
- Generators: tools/r2_se.py (SE: hair silhouette from per-row outline extents + old master m48 face pasted pixel-exact, rows 17-25/cols 13-23 -> rows 11-19/cols 10-20), tools/r2_e.py (imports r2_se helpers). Re-run both, then preview.py. tools/r2_view.py S names... = 1:1 zoom vs old master -> png/r2_view.png.
- SE 25x22 pivot (14,19) bow (13,4) bun (8,-4); lean 26x23 = +1x whole head + 1 extra fringe row (face 1 lower), same pivot (14,19), bow (14,4) bun (9,-4); squash 27x20 pivot (15,17) bow (14,3) bun (9,-4). Bangs shelf = outlined ledge overhanging the far-cheek strand by 1px; bob tips hang 2 rows below the chin both sides.
- E 22x22 pivot (15,19) bow (11,3) bun (4,-1); lean 23x23 (15,19)/(12,3)/(5,-1); squash 24x20 (16,17)/(12,2)/(5,-2).
- Bows: SE 17x8 pivot (8,7) two loops + knot (squash 19x7 (9,6)); E 12x7 (6,6) far loop dark behind, near loop bright (squash 14x6 (7,5)). Buns 7x7 (3,3); se/bun_squash 7x6.
- r1 crit: Argon 5.5, Opus 4 (featureless ball, face window tiny, SE bow = headband slab, E bow front-facing, lean invisible). r2 prompt_r2.txt: restore full old face, egg/teardrop silhouette with bob tips, 2-loop SE bow, foreshortened E bow, visible lean.
- r2 crit: Argon 6, Opus 6 (dome+temple bulge OK; bow sits in a trench, bun snowman on loop, claw bob hooks, flat face bottom, eyes smaller than master/no glints, E nose spike + back wall, lookup milky eyes, bow/bun drift in squash). r3 prompt_r3.txt.
## r3 (2026-10-26) - after crit r2 (argon 6, opus 6)
- Hand-drawn se/head_neutral.txt + e/head_neutral.txt (no longer r2_se/r2_e generated). Variants: tools/r3_build.py (re-run after editing a neutral, then preview.py). tools/show.py NAME... prints png/NAME_full.txt with rulers.
- SE 25x21 pivot (14,19) bow (13,2) bun (3,1): master eyes pixel-exact (wii/iIi/III + wi/iI/II, lash ###22##22) under a straight bangs shelf + a skin brow row (33 33); chin skin rows 11,9,6,2; bob tips blunt (left 6px, right 3px) 1 row below the chin; bow raised so the dome shows between loop and knot; bun tucked behind the left loop, low on the back-top-left (master layout).
- SE lean 25x21 pivot (13,18) bow (14,2) bun (4,1) = whole head +1,+1 and crown rows 0-7 +1x more (tilt). lookup 25x21 same anchors (dome row 7 removed: bangs/brows/eyes/chin up 1 as a block, tips repeated to the old bottom). squash 27x19 pivot (16,17) bow (15,2) bun (4,1). blink = closed lids (2px line + outer flick).
- E 22x21 pivot (15,19) bow (13,2) bun (4,-1): egg back arc (no col-0 wall > 5), 2px nose bump, mouth notch, soft chin; e/bow 13x7 pivot (5,6) = dark far loop behind + bright knot + near loop (squash 13x6 (4,5)). lean pivot (14,18) bow (14,2) bun (5,-1) (top 5 rows tilted); lookup = neutral anchors; squash 24x19 (17,17)/(14,2)/(5,-1).
- bun_squash (both views) pivot (3,2) and bow_squash: top 1px lower than neutral, same anchors relative to the crown.
- r3 crit: Argon 5.5, Opus 5 (identity back; SE chin = 2px peg with transparent voids, right hair wall vertical, bow on flat top line, bun merges, blink reads angry, E face front vertical wall + flat bar bow, E nape boxy corner). r4 prompt_r4.txt.
## r4 (2026-10-26) - after crit r3 (argon 5.5, opus 5); prompt_r4.txt
- Hand-drawn se/head_neutral.txt + e/head_neutral.txt; variants: tools/r4_build.py (re-run after editing a neutral, then preview.py). tools/runs.py = outer-outline straight-run + hole report (all files: max run 3 L/R/T/B, 0 holes). tools/zoom.py NAME... -> png/zoom.png (12x + 2x + 1x).
- SE 26x22 pivot (16,20) bow (13,2) bun (3,1): 3px dome peak under the knot, right wall bulges to col 25 at lash/eye rows, chin skin 10,8,6,3 (outline 1-1-1-2-3), bob tips hug the jaw (left tip lowest, rounded hem), sheen ring on the crown, flat blink lids. lookup 26x21 (dome row 8 out, same anchors/pivot); lean 26x23 pivot (15,20) bow (14,2) bun (4,1); squash 28x20 pivot (17,18) bow (14,2) bun (4,1).
- SE bow 17x8 (8,7) loops taper (no 5px walls), knot top raised; bow_squash 19x7 (9,6). Buns 7x7 (3,3) / squash 7x6 (3,2), jj rim top-left (shared by E).
- E 23x23 pivot (16,21) bow (10,3) bun (4,0): back arc 3-3-2-2-1-1-1 into a nape tip, face front forehead/eye/1px nose/lips/chin (no wall >3), eye = lash(3px w/ back flick) + 4 iris rows wi/iI/iI/II. lookup 23x22 same anchors; lean 23x24 (15,21)/(11,3)/(5,0); squash 25x21 (18,19)/(11,3)/(5,0).
- E bow 12x9 pivot (5,8): bright near loop rising above the bun, dark small far loop behind, knot at the bottom; bow_squash 12x8 (5,7).
- r4 crit: Argon 5, Opus 6 (round + soft chin OK; reads mushroom/afro, back mass too big, face-side bob too short, eyes lost w glints/small, blush clutter, E bow = V/claw, E eye squiggle, stair-steps, squash flat top). r5 prompt_r5.txt.
## r5 (2026-10-26) - after crit r4 (argon 5, opus 6); prompt_r5.txt; final polish, in place
- Hand-drawn se/head_neutral.txt + e/head_neutral.txt; variants: tools/r5_build.py (then preview.py, runs.py). bow_squash/bun_squash removed (both views): squash reuses bow/bun 1px lower so loops stay up.
- SE 24x23 pivot (14,20) bow (11,2) bun (2,2): back mass pulled in 2px (rounded bottom, tip tapers down to chin level), face-side bob 3px strand ending in a tapered tip 2 rows below the jaw; flat bangs shelf (no hair dip at the eye), master eyes pixel-exact incl. w glints, no blush, mouth = one '1' on the 3/4 centreline; j = top-left rim only (no streak). lean 24x24 (13,20)/(12,2)/(3,2) crown rows 0-3 tilted; lookup 24x22 same anchors; squash 26x21 (15,18)/(12,3)/(3,3); blink 24x23 flat lids on the w row (both eyes).
- E 23x22 pivot (16,21) bow (10,2) bun (3,0): eye = lash ### + wii + iI (3x3 almond), nose 1 row under, no blush, bangs overhang 1px; lean 23x23 (15,21)/(11,2)/(4,0); lookup 23x21; squash 25x20 (18,19)/(11,3)/(4,1) (cheek +1 wide).
- e/bow 13x9 pivot (6,8): big bright near loop rising above the bun, small far loop behind-left, knot; e/bun 8x7 pivot (4,4) (bigger/higher, bottom overlaps the skull outline = no double line). se/bun 7x7 (3,3) now overlaps the skull by 1 more row.
- runs.py: all outer runs <=3 except the 4px top of the round E bun; 0 holes.
- r5 crit: Argon 6, Opus 6 -> FINAL = r5 (ties r2, has the chin/glint/E-bow fixes). README.md + READY written.
- r6 = r5 + bangs-row skin -> hair (brows 33 kept), lash touches the bangs like the master: Argon 5, Opus 6 (both: still a bit 'hairball with face window'). FINAL.
