# r7: jump_v2 (H1v2_B_final)

`data/animations/jump_v2.json` has 14 frames and runs 800 ms (rev 2). Airborne at 110 ms. Events: `takeoff` on f3, `land` on f10. f11-f14 are cancelable.

**QA:** PASS. Height delta 2 px, foot slide 0.26 px, 0 orphans.

**Patch:** the frame names avoid the H1 `anim_patch` keys, so the patch does not apply. Values are tuned for B (pelvis_drop at most 2.0).

| # | frame | ms | z | intent |
|---|-------|----|---|--------|
| 1 | tuck_in | 40 | 0 | Small dip with a smile. Knees together, head rolls. |
| 2 | scrunch | 70 | 0 | Knock-kneed crouch (spread -8), squash 0.82, coy spine twist. Face tilted up, mittens pulled back. |
| 3 | spring | 50 | 3 | Reverse-C stretch at 1.15 with pointed toes. Mittens beside the head. |
| 4 | rise | 60 | 11 | Banzai opens up. Legs fold unevenly. |
| 5 | float_up | 60 | 17 | Lean and turn build. Right arm starts down. |
| 6 | peak | 70 | 20 | One hand up, other arm out. Right heel kicked back. Lean 9, turn 10, head roll -13. |
| 7 | peak_hold | 60 | 20 | Moving hold: the same pose pushed a little further. |
| 8 | fall | 60 | 15 | Arms go high and wide like a parachute. Smile. |
| 9 | reach | 60 | 8 | Stretch, tiptoe legs reaching down. |
| 10 | touchdown | 60 | 0 | Squint face ("><"), squash 0.82, knees together. Face stays visible. |
| 11 | hop | 50 | 3 | Small happy hop: heels flick up, fists at shoulder height. |
| 12 | plop | 40 | 0 | Soft second contact. |
| 13 | settle | 60 | 0 | Head tilted 12°, mittens together in front. |
| 14 | ready | 60 | 0 | Eases back to rest. |

## Why it is cuter and more expressive
- **Feminine shapes:** knees together and hands kept close at both ends, with a head tilt or roll on almost every frame.
- **Asymmetric apex:** one hand up, one heel back, plus spine lean and turn. This gives a curved line of action instead of a symmetric V.
- **Two-beat landing:** touchdown, hop, then plop. The extra bounce gives follow-through, and the pom and scarf get a second flick.
- **Readable faces:** head tilt counters the spine tilt in both squashes, so the brim never covers the eyes.
- **All 8 directions:** arm spread is at least 36, so the mittens clear the big head from N, NE and NW.
- **Timing:** quick anticipation, a sharp spring, 130 ms of hang at the peak, a fast fall, then a playful 210 ms recovery.

## rev 2 (designer feedback)
- **Face in profile:** the net head yaw is now about 0 in frames 2 and 4-8. Spine turn is capped at 6 and head turn counters it, for example spine +6 against head -6. Spine lean is capped at 5 and head roll at -8 on the airborne frames, with spring and rise near 0. Larger leans and rolls tipped the face into the hair in E. The apex now gets its asymmetry from the arms and heel kick. Checked on C5_buns_ribbon: the face stays visible in E and W on frames 3-8.
- **Softer descent:** fall z 15 -> 16, reach z 6 -> 8, reach 50 -> 60 ms, total 800 ms. The last air frames now fall at a steady 8 px per 60 ms instead of speeding up, so long chains flare to the sides on touchdown instead of flipping up (checked on C1_twintails).
- QA passes on H1v2_B_final, C5_buns_ribbon and C1_twintails.
