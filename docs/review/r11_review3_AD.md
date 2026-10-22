# r11 review round 3: Art Director

Method: 23:2x builds, back + body + front composited, 8-direction strips, rope zoomed 14x in E/W. No build run.

## Identity across clips: PASS
- Head, bow, outline, scarf side and palette are unchanged. Every body frame has 16 colours or fewer.
- The oat crate separates well from the hair. It is near the coat colour, but the hair separates them.

## Round-2 items
- **carry_throw S f2 release arms:** FIXED. The hands rise beside the head.
- **carry_throw double crate / spawn frame:** FIXED.
- **run eye and lean:** FIXED. There is eye ink on all 8 E frames.
- **idle exit pop:** FIXED. It is within 1 px of the end frames.
- **Rope over the head in E/W:** NOT FIXED.

## Blocker: the rope in side views
- carry_idle E f0 and carry_walk E f3 each show two dark rope lines running about 10 px from the crate down through the hair to the eye row. wpC describes a 2-3 px stub.
- pick_up E f7 runs past the eye. W/SE/SW and carry_throw f0 show the same.
- Cause: in E/W the tuck point (±3.5, 5.0, -1) is on the side nearest the camera, outside the head volume, so the depth split correctly keeps it in front.
- Fix (preferred): `hide: ["rope"]` per direction in E/W/SE/SW/NE/NW. The crate then reads as balanced on the head, as in S.
- Fix (alternative): move the tuck point to x ±1.5, z -3, inside the hair cap.
- S/N are fine: the stubs read as the crate resting on her head.

## Minor (non-blocking)
- carry_throw f1 push: with the rope hidden, the crate floats 2-4 px above the head. At 70 ms it reads as launch. Optionally lower the prop by y -2.

## Verdicts
- **APPROVE:** idle, walk, run, jump_sc, fall, land, climb, climb_top, throw.
- **CHANGES (side-view rope only):** pick_up, carry_idle, carry_walk, carry_throw (f0).

No animation changes are needed. I will approve the carry clips on a visual check of E/W once the rope is fixed.
