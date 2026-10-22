# r11 Review 3: Animation (S4_halfup_bow)

Checked the current builds. Nothing rebuilt.

## Round-2 items
| clip | item | status |
|---|---|---|
| throw | release arm readable in S/N | FIXED. raise -220 / spread 60 lifts the hand above the shoulder line, and the streak reads in S and N. |
| throw | snow streak on release/follow | FIXED. It is on the prop front layer for f5-f6. |
| throw | NW release | ACCEPTED as is. The arm points away from the camera, but the 3 px streak by the bow, the counter arm, the body turn and the spawned snowball carry the read. |
| carry_throw | double crate on spawn | FIXED. `throw_release` is on f3, `spawn_anchor_frame: push`, and the sheet shows the crate on dip/push and gone from f3. |

## Verdicts
**APPROVE:** idle, walk, run, jump_sc, fall, land, climb, climb_top, pick_up, carry_idle, carry_walk, throw.

**carry_throw: CHANGES (new, small).**
- **Problem:** the crate floats on push. With the ropes hidden, the crate on push sits 2-4 px above the mittens in E, NE, N, NW, W and SE (arms raise 152, offset y 19.2). It reads as already released, a frame early. f3 then spawns the projectile back at that same anchor, so the crate seems to hang in place for 130 ms.
- **Fix (pick one):**
  - (a) Add `"offset": [0, 17.4, 1.2]` to the push frame prop, so the crate bottom sits on the mittens. Keep `hide: ["rope"]`.
  - (b) Raise the push arms 152 -> 164, elbow 8 -> 4, so the hands stay under the crate.
- Either way, the runtime should give the projectile its launch velocity on the spawn tick, with no hold.

## New observation (not animation)
The crate wood is now `pom` (oat). It shares its value with the coat body. It still separates from the coat because it sits above the head and has its own outline, but in E/W it is close in value to the coat front. Art should confirm whether this is intended.

## Round 4 confirmation
**carry_throw: APPROVE.**
- **Push offset:** the push prop offset `[0, 17.4, 1.2]` is in the data and the build (rebuilt 23:30), with the rope still hidden.
- **Contact:** in the contact-sheet composite (back + body + front), the crate bottom outline now touches the hair top in S, SE, E, NE, W and SW, so it reads as held.
- **N/NW nit:** about 1-2 px of gap remains in N and NW, which is acceptable for a 70 ms frame. If it gets polished later, push offset y 17.4 -> 17.0 in N/NW only, or for all directions if clearance QA still passes.
- **Spawn:** the crate shows on dip/push and is hidden from f3, which is where the projectile spawns.
- **Status:** no animation blockers remain in the r11 action set.
