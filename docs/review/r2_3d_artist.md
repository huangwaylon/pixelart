# R2 review: 3D Artist / Animator (jump)

## Verdict: REQUEST CHANGES (chains only; the poses are approved)

**Poses and timing.** The R1 pose edits landed. Launch now reads as a reverse-C, and apex has an open V with the mittens clear of the head. The asymmetric tuck reads in S, N and the diagonals, the fall arms are uneven, and the land squash is strong. Total is 770 ms. Rise and rise_high are still close in silhouette, but with the z arc they work. The motion is now dynamic and expressive.

**Overlap: the flick works, the settle fails.** I measured tip offset from the pre-jump rest state at t=-5, in px.
- Lags are good: braids and scarf trail on rise, then float up on fall and drop. At land the tips flick up 13-21 (braids y +6.6, scarf +8.2). That is the slam we wanted.
- They don't settle. At ready (t=700) the offsets are: pom 4.8, braids 8, scarf 15. At t=770 the scarf is still 12-15, with the tails flared sideways (visible in the S/N ready cells). This will pop into idle. At 5 ms steps, damping 0.02-0.035 is too low.

I simulated the fix below. The land flick stays at 13-19, and at ready (t=700) the offsets are pom 0.6, braids 1-2, scarf_front 2.0, scarf_back 4.6. At t=770: braids 0.3, scarf_front 1.4, scarf_back 2.2 (it snags on the back collider, so it is a minor residual).

## Fixes: data/character.json chains
1. scarf_front + scarf_back: damping 0.02 -> 0.10, stiffness 18 -> 40
2. braid_L + braid_R: damping 0.03 -> 0.10, stiffness 110 -> 180
3. pom: damping 0.035 -> 0.10, stiffness 140 -> 200

## Note (code, not JSON)
In `rig.py`, `Animation.channels_at` goes straight from rest (t<0) to the dip key at t=0. The anchors jump in one 5 ms step, so frame 1 already shows a 3-5 px chain jerk. Ease rest -> dip over the 40 ms before t=0.
