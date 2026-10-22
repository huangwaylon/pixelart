# H1_B_final pixel review: E / W profiles (jump, 24 frames)

Reviewer: pixel-EW. Every change went through `pipeline.override` with a recorded reason (overrides/variants/H1_B_final/jump/{E,W}/NN.json). The base reviewed is the post-fringe-fix sheet (editor/jump_sheet_base.png, 11:59:40). Previews: out/variants/H1_B_final/pixelreview/fixed/{E,W}_NN.png.

**Main finding:** in f1-f9 and f11 the generator drew no eye in either profile. The face decal was dropped because its 3D anchor projects onto the silhouette edge, not onto a skin pixel. In f10 and f12 the eye was stamped, but it ate the face front: the eye fused with the outline, there was no nose, and the dark doubled at the jaw. So the profile read as a faceless back of the head, and the eye popped in only on f10 and f12 (flicker). Each frame now uses one profile eye vocabulary, mirrored E to W (Gen 3 convention: right = mirrored left):
- determined: a 1x2 outline column
- joyful: a `^` arc (.E./E.E)
- neutral/smile: a 1x2 outline column with a snow_3 catchlight on its top-back side
- squint: a chevron pointing forward (`>` for E, `<` for W)

The eye always sits 1 px behind the face front, so a 1 px skin nose stays. Its top row is one skin row below the cuff, which matches the fringe fix. Mouth and blush are left off in profile (style doc: mouth usually omitted; there is no room on a 4-6 px face). E and W eye columns satisfy x_W = 47 - x_E on every frame, on the same rows.

## E
- E f1: 2 px fixed. Added the determined eye at (31,26),(31,27). The face had no eye. Body, mitten (2x3 at back), boots and outline are clean.
- E f2: 2 px fixed. Added the determined eye at (33,29),(33,30). The mauve cuff underside and back mitten are purposeful.
- E f3: 3 px fixed. Added the joyful ^ at (28,22),(27,23),(29,23). The scarf tail tapers to 1 px over 1 row at the tip, which is accepted as the tail end.
- E f4: 5 px fixed. (28,20),(29,20) skin hole inside the cuff band set to oat_1, so the cuff is continuous. Added the joyful ^ at (28,22),(27,23),(29,23), which holds the eye steady from f3. The mitten (red_1/crn_1, 2x3) beside the 1 px scarf edge is accepted as a 3D overlap.
- E f5: 3 px fixed. Added the joyful ^ at (28,23),(27,24),(29,24).
- E f6: 5 px fixed. Cuff skin hole (29,21),(30,21) set to oat_1. Added the joyful ^ at (29,23),(28,24),(30,24).
- E f7: 5 px fixed. Cuff skin hole (29,21),(30,21) set to oat_1. Added the neutral eye: catchlight (29,23), eye (30,23),(30,24). The bob edge under the chin is accepted (it comes from the 3D model and matches W).
- E f8: 4 px fixed. Added the neutral eye: catchlight (29,22), eye (30,22),(30,23). (20,32) was an outline dent in the back contour; set to char_1.
- E f9: 3 px fixed. Added the squint `>` at (32,29),(33,30),(32,31). The lav_1 back highlight clusters (5 px and 4 px) are purposeful (upper-left light).
- E f10: 7 px fixed. The generated squint was fused into the face edge. Rebuilt the `>` at (30,24),(31,25),(30,26). Nose restored at (31,24),(32,25) as skin_1. (31,26) set to skin_0, and (33,25) set to outline so the jaw edge is a single pixel.
- E f11: 5 px fixed. Cuff skin hole (29,22),(30,22) set to oat_1. Added the smile eye: catchlight (29,24), eye (30,24),(30,25).
- E f12: 6 px fixed. Replaced the generated 2x3 eye that ate the face front. Catchlight at (29,23), eye at (30,23),(30,24). Nose (31,24) and (30,25) set to skin_1, and (30,26) to skin_0. The doubled dark at the jaw is gone.

## W
- W f1: 2 px fixed. Added the determined eye at (16,26),(16,27), mirroring E f1.
- W f2: 2 px fixed. Added the determined eye at (14,29),(14,30).
- W f3: 3 px fixed. Added the joyful ^ at (19,22),(18,23),(20,23). The near mitten (2x3) is clean.
- W f4: 8 px fixed. Cuff skin hole (18,20),(19,20) set to oat_1. Added the joyful ^ at (19,22),(18,23),(20,23). The near mitten was a 1 px red sliver, so (25,29..31) went from ink to red_1. It is now 2x3, in the same place as in f3.
- W f5: 4 px fixed. Added the joyful ^ at (19,23),(18,24),(20,24). (22,27) was a 1 px scarf spike poking into the bob's lower edge; set to hair_1.
- W f6: 3 px fixed. Added the joyful ^ at (18,23),(17,24),(19,24). The cuff here already has the correct "front rises" shape. The (20,37) inner outline dot under the scarf tip is a valid overlap line, so it stays.
- W f7: 5 px fixed. Cuff skin hole (17,21),(18,21) set to oat_1. Added the neutral eye: eye (17,23),(17,24), catchlight (18,23).
- W f8: 4 px fixed. Added the neutral eye: eye (17,22),(17,23), catchlight (18,22). (27,32) back-contour dent set to char_1, mirroring E f8. The 1x3 oat_2 sleeve cuff is accepted.
- W f9: 3 px fixed. Added the squint `<` at (15,29),(14,30),(15,31). The (16,33) chin-over-scarf inner line is valid.
- W f10: 7 px fixed. Generated squint fused with the outline. Rebuilt the `<` at (17,24),(16,25),(17,26). Nose (16,24),(15,25) and (16,26) set to skin_1, and (14,25) to outline. Mirrors E f10.
- W f11: 5 px fixed. Cuff skin hole (17,22),(18,22) set to oat_1. Added the smile eye: eye (17,24),(17,25), catchlight (18,24).
- W f12: 5 px fixed. The generated eye was fused with the outline and its catchlight was jammed against the outline. Rebuilt with eye (17,23),(17,24) and catchlight (18,23). Nose (16,24), plus (17,25),(17,26), set to skin_1.

Totals: 0/24 approved as generated (every frame needed the eye). 24/24 frames fixed: 101 px (E 50, W 51).
- Eyes added (f1-f9, f11): 56 px
- Cuff holes: 14 px
- Mitten/spike: 4 px
- Outline dents: 2 px
- f10/f12 eye rebuild and face-edge restoration: 25 px

Accepted as generated (3D-driven, not fixed): the scarf tail lies on the near side in W and the far side in E, so the red masses don't mirror; W hair and face are darker and flatter than E because the light is fixed upper-left; the bob shows under the chin in f7.

## Generator-level issues
1. **Profile eye dropped or fused (24/24 frames).** In `pipeline/face.py:apply_face` the anchor is tested with `skin[yi,xi]`, and `_stamp` writes the full 2x3 pattern at the projected point. In profile the anchor lands on or next to the outline. Fix: when `facing` is low or only one eye is visible, (a) clamp the anchor to `front_skin_x - 1` (1 px nose margin) and to `skin_top + 1`, searching inward along the row for a skin pixel instead of rejecting; (b) use a profile pattern set: determined `["E","E"]`, neutral/smile `["CE",".E"]` (mirrored for screen-left facing), joyful `[".E.","E.E"]`, squint the existing `>`/`<`; (c) never stamp into the outermost skin column. The overrides here are the reference pixels.
2. **Skin holes inside the hat-cuff band (E f4/6/7/11, W f4/7/11).** The cuff's lower edge rasterises with a 2 px cuff "tip" in front of skin. Fix: after material rasterisation, run a pass so any skin run in a row that has hatcuff on both sides (within 3 px) becomes hatcuff. Or compute the cuff's lower edge as a monotone curve per facing.
3. **1 px outline dents on the back contour (E/W f8).** Fix: in the outline pass, fill any outline pixel whose row neighbours on both vertical sides sit at x±1 further out with the adjacent interior material (single-pixel concavity removal).
4. **1 px mitten sliver / scarf spike (W f4, W f5).** These apply rule 3 (min feature width 2) and rule 2 (no ≤2 px protrusions) only after compositing. Fix: per-material, widen any 1-px-wide accent column (mitten, scarf) to 2 px over the adjacent coat shadow; remove 1-px accent spikes that intrude into a hair mass.
