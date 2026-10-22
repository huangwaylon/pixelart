# r11 review round 1: Art Director

Method: Pillow strips in /tmp/ad_r11/ comparing rest frames across all clips in 8 directions, contact sheets for S/E/N/W at 3-10x, and a palette diff against idle. carry_throw was reviewed after its 22:37 rebuild.

## Character identity: PASS
- Head, bow, fringe, scarf side and outline match in every clip.
- Head top is at y=23 and feet sit on the pivot.
- The only extra colours are the snow ramp and the rope colour, both on props.

## Per clip

**idle: CHANGES.**
- In E the eye cel flickers. f3 shows a white bar, f4 shows white over dark, and f5 uses the `determined` cel, which moves the eye 1-2 px. Use one smile cel throughout. Engine: add a `closed` blink cel to face.py.
- In E f1-f7 a 1 px dark-teal scarf-tip speck wanders over the coat at the hip. Clamp it or hide it behind the torso.

**walk: APPROVE.**

**run: CHANGES.**
- In E/W the eye vanishes on down_L (f1) and down_R (f5), so the profile reads as a back view. The cause is spine.tilt 15 with head.tilt -6.
- Fix: set head.tilt to -10 on both frames, keeping the net forward tilt at 5° or less.

**jump_sc, land, fall: APPROVE.**

**climb: CHANGES.**
- The arms flap sideways at shoulder height, so she looks like she is waving.
- Fix on f1/f5: arm raise +25-30 and spread -15 so the hand clears the bow; spine lean 4-6 toward the wall.
- In NE f4 to f5 the bow jumps. Check head.turn continuity.

**climb_top: APPROVE.**

**throw: APPROVE.**

**pick_up, carry_idle, carry_walk: CHANGES (crate only).** The poses are good.

**carry_throw: CHANGES.**
- f1 to f2 drops the arms from overhead to chest in 60 ms, and in S they foreshorten to nothing. Fix: arm raise to 140 on release and 115 on follow.
- f0 dip: the crate hides the top of the head and the bow in S/N, which breaks "props never clip head". Fix: head.tilt from -14 to -8, or raise the carry offset by 1.5.

## Crate (all 4 carry clips)
1. **Proportions.** Radii [7.2, 3.68, 4.0] make it 14 px wide in S but a 9 px brown post in E/W, so it reads like a sign. Fix: radii [5.5, 3.7, 5.5].
2. **Material.** `prop_snow` on the whole body reads as ice. Fix: body `prop_wood` plus a thin `prop_snow` cap (y radius 1.2).
3. **Rope.** In E/W the rope line runs down through the hair to the eye line. Fix: offset it ±1.5 in z behind the head, or clip it above the head.
4. **One spec.** Move the prop spec to one shared definition used by all 4 clips.

## Next
Rebuild idle, run, climb, carry_throw and the crate clips, then run round 2.
