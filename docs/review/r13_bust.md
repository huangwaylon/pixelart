# r13 dialogue busts, rounds 3-5 (lead pixel artist)

Sources: `art/hand/S4/bust/` (`bust_base.pix` + 10 `extends`/`patch` files). Hand-typed runs: `pipeline/tools/r13_bust/`. Outputs: `00_REVIEW/r13_anime_pixel/bust/` (sheets x3/x1, `*_x6`, spritesheet + JSON, `compare_C_vs_base_x3.png`).

## Round 3 fixes (review 2)
1. **Bow:** the balloon loop, leaf loop and bar tail are gone. Redrawn from the head_small / turnaround 3/4 bow at about 1.8x:
   - one near teardrop loop at x78-92, y7-30, top arc 5 px, drooping lowest at the back
   - a 4x10 pinched knot at x75-78, y12-21, with a teal_2 glint, a teal_0 bottom row and no K on the loop side
   - a 4x5 teal_0 pocket creased to the knot; teal_2 on the top arc only; bottom 3 rows in shadow
   - one tail at y22-44, tapering 4 to 3 px, drifting back 3 px, with a V-cut tip
   - the upper hair now gathers into the knot, and the ponytail root fills under the loop, so the bow sits on the head
2. **Scarf:** C's roll re-pasted at +10,+5 (11 rows, a rib every 4 px, e on the top two rows, b underneath instead of K). The near side is 1 px higher, and the tail is C's 9 px cable.
3. **Neutral:** flat mouth (L at x42-43, v at (44,51)); the blush is one pale t row at y45.
4. **Surprised:** an "o" made of an L ring with P inside.
5. **Side locks:** the outer edge bows out 1 px at y40-50, and the 1 px stripes are merged into 2 px clumps.

Up to 25 colours per file. `pixgrid stats` shows only catchlights, the knot glint, the AD-specified neutral mouth pixel and FX.

## Round 4 (review 3, bow only)
- The long tail is gone. Ponytail hair fills the area.
- Near loop: x79-93, y6-24, pinched to the knot height. Highlight is on the top arc; there is a pocket and a shadowed underside.
- Knot: x75-78, y13-20, with outline notches.
- Far loop (review 4): a 5x6 b/c wedge at x70-74, y10-15, opening into the knot at x75. The boxed tip at y4-10 is gone.
- Two short splayed V-cut tails: near 4 px, y21-33, drifting right; far 3 px, y21-30, drifting left.
- At 1x it reads as a ribbon bow. The faces did not change, so the round 3 blind tests still apply.

## Round 5 (Gemini triage, L items 1-8)
- Hair: no interior K at x76-77. The x70 and x31-32 seams end at y44/y48 as tapered splits. The crown stair is one 2 px split. The curtain tapers from x84 to x80.
- Coat: far shoulder in 6 px, near shoulder in 3 px. Placket and buttons moved 2 px left. oat_1 shadow right of the scarf tail and under the roll.
- Nose: skin_1 at (45,46).
- Angry vein: a 7x7 red_1 cross with a crn_1 lower-right edge.
- Embarrassed blush: the outer 3 px of each group dropped 1 px to follow the cheek.
- Blind test: 10/10 (7 high, 3 medium).

## Blind tests (fresh agents, unlabeled 1x+2x)
| Round | Score | Confidence | Change after |
|---|---|---|---|
| 1 | 10/10 | 7 high, 3 medium | Thicker determined brows |
| 2 | 10/10 | 6 high, 4 medium | |

Neutral scores **medium**, not high. Testers pick it by elimination against determined and worried, which are the other faces with no blush.
