# r9: jump_sc (semi-chibi jump)

`data/animations/jump_sc.json`: 14 frames, 840 ms, airborne at 120 ms. `takeoff` on f3, `land` on f10, f11-f14 cancelable.
**QA (S0_semichibi_base):** PASS. Foot slide 0.26 px, 0 penetrations, 0 orphans. 6 builds.

| # | frame | ms | z | drop/squash | intent |
|---|---|---|---|---|---|
| 1 | dip | 40 | 0 | 1.0/0.96 | Knees in, smile |
| 2 | coil | 80 | 0 | 3.2/0.90 | Deep knock-kneed crouch, arms back, face up |
| 3 | spring | 50 | 3 | 1.14 | Arms swing forward-up, toes pointed |
| 4 | rise | 60 | 12 | 1.10 | Arms split: up-out and forward |
| 5 | float_up | 60 | 18 | 1.03 | Front knee lifts, back heel folds |
| 6 | peak | 70 | 22 | 0.98 | S-curve: legs one way, spine lean 5 the other, head roll back; heel kick |
| 7 | peak_hold | 70 | 19 | 0.99 | Pose pushed slightly further |
| 8 | fall | 60 | 11 | 1.02 | Lean and roll reverse; hair swings |
| 9 | reach | 60 | 4 | 1.06 | Hair flourish: lifts behind her; tiptoes |
| 10 | touchdown | 70 | 0 | 3.0/0.90 | Knees together, squint, arms low-out |
| 11 | hop | 50 | 3 | 1.06 | Small hop, fists at chest |
| 12 | plop | 50 | 0 | 1.4/0.93 | Soft second contact |
| 13 | settle | 60 | 0 | 0.3 | Head tilt, hands together |
| 14 | ready | 60 | 0 | - | Back to rest |

## Notes
- **Arms:** no overhead arms. Side-on arms sit on the head in E/W. One arm goes diagonal (up-forward-out), the other low-out or forward. On every airborne frame, a hand stays clear of head and torso in all 8 views.
- **Faces:** net head yaw is 0. Spine turn is at most 6 and the head counters it; lean and roll stay at 9 or less. Coil and touchdown use head tilt -21 to -22, so the beret brim never covers the eyes.
- **Feet:** knees-in plus a deep drop pushes the ankles outwards. Spread is -7 on the dip and -6 on the deep frames, which keeps the slide at 0.26 px.
- **Hair:** the locks are heavy and cannot float at the apex. The descent 22 → 19 → 11 → 4 → 0 puts the lift on f8-f9 and settles it by touchdown. v1 flipped hair over the head at f10.
- **Limits:** the skirt and coat are rigid. Bent knees mostly read as a lower hem.
