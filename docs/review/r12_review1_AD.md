# r12 review 1: Art Director

Big step up from r10. **No group approved yet.**

## Model sheet: CHANGES
1. **3/4 face is the front face shifted.** Eyes are equal width, nose and mouth centred, no far-cheek contour. In three_quarter:
   - far eye 6 px, near eye 8 px
   - features 2 px toward the facing side
   - 1 px cheek/nose bump on the left silhouette (y38-41)
   - jaw tapers under the far eye
2. **Sel-out zipper.** The shadow-side skirt diagonal alternates outline/mauve per pixel: front x56-65 y72-93, 3/4 x153-161, back x251-253. Fix in `illustrate.py`: choose colour per edge run from the segment normal.
3. **Lit coat edge is lavender**, lost on snow and the dialogue box. Use mauve, darker than the fill.
4. **No brows on the sheet**, though the busts have them. Make brows canonical.
5. **Missing:** head and bow turnaround.

## 3/4 bust + 10 expressions: CHANGES
- **Brows read as a bang scallop at 1x.** Make them 2 px with an ink core, clear of the bang notches. Angry far brow: a steep 3 px diagonal.
- **Smile vs neutral: 6 px apart.** Upturned 4-5 px mouth, lower lids up 1 row.
- **Sad = worried at 1x.**
  - sad: drooping lids, tear on the lower lid, corners down.
  - worried: iris hard to one side, wobble mouth, sweat drop.
- **Angry vs determined: 61 px apart.** Angry needs a clenched tooth row. `fx_anger` (2x2 near x56 y21) is lost in the hair: enlarge it and move it to open space.
- **Blush on every face**, so embarrassed doesn't stand out. Remove it from neutral, determined, angry and surprised.
- Surprised, laugh and content: good.

## Front bust: CHANGES
- **Smile = neutral** (6 px, x46-49 y54-55). Mouth is a faint smudge. Use a 4 px plum curve and a 3 px flat line.
- **Gaze drift:** sclera on the left of both eyes, so she looks right. Mirror the sclera only on eye_R, keep the catchlight upper-left.
- Brow fix as above.
- **Missing:** the 16-colour stress bust.

## 8 poses: CHANGES
- **Heads on-model: pass.** Within 1-2 px of the 3/4 panel.
- **Orphans:** about 20 per pose are the hem zipper (cheer x57-69 y69-95, recoil x58-69 y73-95, idle x57-65 y72-92). Then check:
  - cheer: bow tip (77,3-4), hair x63-75 y17-56
  - recoil: x59-66 y17-35
- **Mittens vs scarf:** shiver's crossed arms are one teal mass. Give mittens their own slot, or add a 1 px oat cuff and teal_0 sel-out at the contact.
- **Joints:**
  - cheer: knees fuse into one boot wedge. Redraw: 2 px tights gap, cuffs visible.
  - wave: back knee needs a kneecap break.
  - point: 40 px straight tube. Add an elbow taper and a 1x2 finger.
- Idle, recoil, hands_on_hips: good at 1x.

## Re-review gate
- sel-out fixed globally
- 3/4 face turned
- all 10 expressions pass a blind 1x label test
- under 10 orphans per image
- missing deliverables added
