# r11 review round 2: Art Director

Method: I re-ran the /tmp/ad_r11 strips on the 23:0x builds, compositing `<clip>_prop.png` per `frame.prop.layer`. I cross-checked the official contact sheets and ran a palette diff.

## Identity across clips: PASS
- Head, bow, fringe, scarf side and outline match at rest in all 8 directions.
- Every body frame has 16 colours or fewer, all from the shared palette.
- Props read as one family: wood crate with snow cap, and the snowball.

## Round-1 items
- **idle E eye flicker:** FIXED. The eye is constant and f5 uses a real blink cel. The hip speck is gone.
- **run E/W eye lost on f1/f5:** FIXED. Eye ink is present on every frame. The catchlight drops on the down frames, which is acceptable.
- **climb waving arms / NE bow jump:** FIXED. The hands reach ear height and the bow stays continuous.
- **carry_throw dip clipping the head:** FIXED. Clearance now matches carry_idle.
- **carry_throw release arm drop:** PARTLY FIXED. The arms read in E/N, but in S f2 they still drop to shoulder height.
- **Crate proportions and material:** FIXED. It reads as a box in E/W (about 10x9 px), with a wood body, slats and a snow mound.
- **One shared crate spec:** FIXED (`{"ref": "crate"}`).
- **Rope over the face in E/W:** NOT FIXED.

## Remaining issues
1. **Rope draws over the head (engine, the one blocker).**
   - The prop strip is a single layer tagged `front` for the whole crate. So the rope that is meant to sit behind the head still paints a dark bar from the crate through the hair to the eye line in E/W/SE/SW.
   - It shows in carry_idle, carry_walk, pick_up f6-f8 and carry_throw f0-f1, including the official contact sheets.
   - Fix: give each prop part its own layer (rope `back` in side and diagonal views, body `front`), or depth-test the prop against the body before splitting it out.
2. **carry_throw S f2.** Reduce release spine.tilt from 14 to about 6, so the arms read above the head instead of foreshortening.

## Verdicts
- **APPROVE:** idle, walk, run, jump_sc, fall, land, climb (chibi reach accepted), climb_top, throw.
- **CHANGES (rope layer only):** pick_up, carry_idle, carry_walk.
- **CHANGES (rope layer and S release):** carry_throw.

Once rope parts get a back layer, the carry clips need no animation changes, and I expect to approve them on sight.
