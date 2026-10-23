# r13 Cut-scene poses B: shy, shiver, recoil, cheer (Pixel Artist 3)

**Files:** `art/hand/S4/poses/{shy,shiver,recoil,cheer}.pix` (96x160).
**Renders:** `00_REVIEW/r13_anime_pixel/poses/` (`<pose>.png`, `<pose>_x4.png`, `poses_B_x3.png`, `poses_B_silhouette_x2.png`, `poses_lineup_x3.png` with all 8).

**Base:** the approved turnaround (front for shy, shiver and cheer; 3/4 for recoil) with the arms taken off and redrawn. Mittens have thumbs. The faces are `head_small` expressions at x+26. Tilts are done by hand-shifting feature bands 1 px; nothing is rotated.

| pose | expr | line of action | gesture | secondary |
|---|---|---|---|---|
| shy | embarrassed | inward curl: head bowed and tilted, torso curls 1-2 px | elbows tucked, mittens clasped under the chin | knees in, pigeon toes, heel up 3, hem +1, curtain swings |
| shiver (approved) | worried | compact, head sunk 2 px | hugging herself | jitter echo, ticks, breath puff |
| recoil | surprised | reverse C: head back 4, hips forward 1, front knee up | both palms open at the chest | 2 tapering ponytail locks, hem +2, locks trail |
| cheer | laugh | Y-line hop, head tilted toward the fist | fists up, 9 px sleeves with shoulders | solid lifted curtains, scarf tail flies, free foot tucked, hem flares |

## Round 2 (review 1)
- **Recoil:** redrawn. The arch and hands are as above. The lifted leg has thigh, knee and boot volume with a pointed toe. The planted boot has a toe. The duplicate ponytail is deleted.
- **Cheer:** thin strokes replaced by solid locks; the hop now reads.
- **Shy:** knees in, head tilted down.
- **Tilted heads:** recoil uses `three_quarter_tiltR_surprised` (tips back), shy `front_tiltR_embarrassed` (bowed), cheer `front_tiltL_laugh`.
- **Head_small bust-review fix:** the 3/4 bow tail is now hair, with a 2x3 knot, two short tails and a far-loop tip. Recoil uses it.

## Round 4 (review 3)
- **Recoil:** the ponytail is ONE tapered lock from the nape (64,20), arcing back and down to (84,34), with nothing above y16. The planted-boot heel outline (x52-53, y135-140) and the cuff edge (x30-31, y44-48) are restored.
- **Cheer:** fists moved 2 px out, with a 1 px gap from the bows. The lifted locks moved out and are trimmed to a 1 px gap from the sleeves. The scarf tip is outlined. Cuff outlines are back.
- **Shy:** the clasp is dropped 2 px, clear of the scarf. The head is re-pasted from the fixed `front_tiltR_embarrassed`.
- **No auto clean-up.** Sleeve, band and lock outlines now take their lit or dark side from the edge normal, so stair-steps don't flip colour. The remaining strays are fixed pixel by pixel in each script.

## Gemini triage (owner H)
- **Recoil:** the lower trailing lock is shortened and now ends tucked at y36, so there is one sweep and no second claw.
- **Shy and shiver:** the hem sags 1 px at the centre (the bottom edge drops to y87 across x37-56) and the corners are rounded by 1 px. Shiver's automatic clean-up is gone too; its strays are now fixed by hand.

**Checks:** 3+ viewed passes each, plus a silhouette pass. 25-29 colours per file. The only orphans are catchlights, the nose, FX and the AD-approved knot highlight.
