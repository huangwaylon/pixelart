# r13 Gemini triage (AD)

## Bust (L)
- **Hair tubes: ACCEPT.** Seams run full length: `hair_1` x31-32 (y31-60), `plum_0` x70, and an interior K at x77 (y41-60). The `hair_hi` angel ring at y16-20 already exists. The "dither" is a 1px `hair_1` stair at x64-72, y14-20.
- **Shoulders: ACCEPT.** The coat spans x2-91, wider than the hair (x22-84), and the far side is the wider one. Placket shift: 2px. Scarf thickening: REJECT (the ring is 13 rows). Collar trim: REJECT (the collar is hidden).
- **Nose: PARTIAL.** It exists (`skin_0` 45,45-46) but is weak.
- **Scarf shadow: ACCEPT.** It goes right of the tail.
- **Angry vein: PARTIAL.** A 5x5 `red_1` at x56-60, y18-22 has low contrast on hair.
- **Blush: PARTIAL.** It is a flat band at y45-47. Keep `red_2`.
- **Neutral = base, jaw: REJECT.** Base is the neutral, and the jaw is a monotonic run.

## Turnaround (T)
- **Back: PARTIAL.** The curtain width is approved, so narrowing it is REJECTED. But its 5-point sawtooth (y60-74) breaks the bible's "blunt slight-V", and the ponytail tip (45-46,60) loses its edge.
- **Hem: ACCEPT.** The front bottom is flat at y85 and the corners drop at y86. Pleats: REJECT.
- **Catchlights: REJECT.** `snow_3` is at (41,20) and (53,20).

## Poses
- **Torsos, recoil leg, point "finger": REJECT.** These are bible and Anim Dir decisions ("one foot up", "index out").
- **Recoil hair: PARTIAL.** The lower lock (x65-72, y25-45) runs parallel to the sweep: two claws.
- **Breath puff / nose flush: REJECT.** Shiver has a puff, and a flush would clash with embarrassed.

## Fix list
**L (bust_base, then re-apply to all 10)**
1. Recolour K x77 to `hair_1`. End the x70 seam at y44 and x31-32 at y48 as tapered splits.
2. Merge the crown stair into one 2px `hair_1` split.
3. Taper the right curtain edge from x84 (y45) to x80 (y67), 1-1-2.
4. Far shoulder in 6px (x2 to x8 at y91, steeper). Near shoulder in 3px. Placket and buttons from x46 to x44.
5. `oat_1` at x64, y73-95, and on y73, x36-54.
6. Nose: `skin_1` at (46,46).
7. Angry: 7x7 `red_1` cross at x55-61, y16-22, with a `crn_1` lower-right edge.
8. Embarrassed: drop the outer 3px of each blush group 1px.

**T**
1. Hems (front/3-4/back): trim down 1px across x37-56 (y86). Round the corners by 1px.
2. Same hem fix on idle, wave, point and hands_on_hips.
3. Back: blunt slight-V hem at the same width (2px centre drop). The ponytail gets a `plum_0` edge to a tip at y62, with a `hair_1` cast shadow.

**H**
1. Recoil: shorten the lower lock to end tucked at y36.
2. Hem fix on shy and shiver.
