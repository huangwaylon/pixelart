# R1 review: Game Director (JUMP, build 913fde08dfa6)

**Verdict: FAIL. Fix and resubmit.**

## Acceptance criteria
1. Timing: **FAIL.** 850 ms is over both 720 and the locked 840. Airborne at 130 ms. No input-lock value in the JSON.
2. Feet on pivot: **FAIL.** 0.417 px slide; 0 is required.
3. Cell clip: **FAIL.** SW f3 hits y=63 (launch stretch 1.22 plus toes-down ankle).
4. Palette: 24 colours, PASS. Orphans: **FAIL**, 1010.
5. Face at 3x: **FAIL at 26°.** The hat brim hides the eyes in S/SE/SW crouch and land.
6. Greyscale on snow: **NOT RUN.** I expect the cream hat to vanish.
7. Determinism: not reported. 8. Playtest: pending.

## Metadata
Per-frame fields are complete. Missing: `buildHash` (rename `buildId`) and `inputLockEnd_ms`.

## Timing: cuts demanded, target 740 ms
Air (f3-f8, 420 ms) stays, including the 110 ms apex hold. Cuts:
- f1 dip 50 -> 40
- f2 crouch 80 -> 50 (airborne at **90 ms**)
- f10 rebound 60 -> 50
- f11 settle 80 -> 60
- f12 ready 100 -> 60

Input lock then ends at 570 ms. This overrides the locked 840/130 for touch responsiveness. Log it in DECISIONS.

## Readability
- **1x:** a blob, which is fine because 1x never ships.
- **3x on phone:** the arcs and apex arm spread read well. The face is lost in crouch/land frames and is only 1-2 px of eye in SE/SW.

## Camera vote: **18°** for the character
At 18° the eyes and blush read in all front facings, and the hat stops swallowing the head. World tiles stay 2:1, and the engine absorbs the small foot offset.

## Must-fix, in priority order
1. Re-render at 18°.
2. Apply the timing cuts and add `inputLockEnd_ms` and `buildHash`.
3. Zero foot slide (snap IK to the integer pivot).
4. SW f3 clip: cap launch stretch at 1.15 and keep a 2 px margin.
5. Standing height 41 px ±1 in all directions (currently 41-45).
6. Orphans to 0.
7. Greyscale-on-snow check. Darken the hat's outer ramp if it fails.
8. Determinism report (double-build byte diff).
