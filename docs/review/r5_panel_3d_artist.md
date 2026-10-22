# r5 Panel: 3D Artist / Animator (jump × proportions)

## Which set animates best
- **A** animates best. The 8.6 leg shows a knee in crouch and land, and QA passes at 2 px.
- **B** has the strongest launch and apex. Crouch and land collapse: `pelvis_drop` 3.0/3.4 uses 65-74% of the 4.6 leg (A: 35-40%), so the head sits on the boots, the crouch arms hide behind the body, and the brim covers the eyes on land.
- **E** is weakest. The bell coat hides the legs on every frame. QA fails at 6 px.
- **Verdict:** B works as hero, but it needs B-specific keys.

## Is the 3D model working as reference?
Yes. Pixel frames use the same primitives and camera, and the joint overlay lands on the joints in every cell. There is no pose drift. The differences are style only (face decals, scarf, hat crown).

**One real problem: QA treats chains as pose.** I edited only the crouch arms, and launch height still moved from S50/N48 to S47/N42. Frames sample exactly on keys, so only the pom and scarf chains carry history between frames. The pom's lag runs along the depth axis: it shows as up on screen in S and down in N. B's 3 px fail and E's 6 px fail are mostly this. **Fix:** measure the height delta on body primitives only.

## B tuning (tested)
Replacing `anim.frames` copies all 12 frames, so later jump.json edits would skip B. Instead, add **`anim_offsets`**: per-frame overrides merged onto the base frame, about 10 lines in build.py.
```json
"anim_offsets": {
  "dip":    {"pelvis_drop": 1.0},
  "crouch": {"pelvis_drop": 2.2, "head": {"tilt": -14},
             "arm_L": {"raise": -55, "spread": 40}, "arm_R": {"raise": -52, "spread": 40}},
  "apex":   {"arm_L": {"spread": 72}, "arm_R": {"spread": 68},
             "leg_R": {"hip": -4, "knee": 10, "ankle": 30}},
  "land":   {"pelvis_drop": 2.0, "squash": 0.82, "head": {"tilt": -8},
             "arm_L": {"spread": 60}, "arm_R": {"spread": 60}}
}
```
- **Result:** crouch mittens sit outside the body, apex mittens clear the head sideways, a boot dangles below the hem, and the eyes survive the land.
- **Keep:** launch and rise arms at 145-150° with spread about 30. The overhead mittens keep the silhouette top steady across facings; wider spreads made it worse, up to 6 px.
- **Keep:** launch stretch at 1.16. Its pom whip is B's best stretch read.
- **Expect:** QA stays red at 5 px until the chain-free metric lands.
