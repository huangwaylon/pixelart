idle: NEW nat/prop/read/energy = 6/8/5/3 ; OLD = 6 ; fixes: the blade sticks out flat to the left at waist height, which disagrees with every other action where it hangs down-right. Re-key it to hang low on the right. Add 1px of torso and shoulder bob on f3 (300ms) so the breathing shows at 1x.

walk: NEW nat/prop/read/energy = 6/8/5/3 ; OLD = 5 ; fixes: the stride is too small to read from behind. Push the leg split and add a 1px head bob on f0 and f3. On f3 and f4 the blade swings to near-vertical, so lock the wrist so it stays at a steady down-right angle.

run: NEW nat/prop/read/energy = 4/8/3/2 ; OLD = 6 ; fixes: the blade shrinks to a 6–8px stub across all frames. Cheat the wrist so the blade angles down and out and reads longer. Add a forward lean and a bigger leg split with a clear airborne frame on f2 and f5. Right now it reads as a jog.

jump: NEW nat/prop/read/energy = 5/8/5/4 ; OLD = 7 ; fixes: the apex (f3–f4) only rises about 4px and the legs stay straight. Raise the body 6–8px and tuck the knees. On the f6 landing crouch the blade flips to point down-left, so keep it pointing down-right.

dash: NEW nat/prop/read/energy = 4/8/3/4 ; OLD = 7 ; fixes: on f3 the head and torso roll sideways into a blob that reads as falling. Replace it with a low forward lean that keeps the head upright. f1 and f2 have the feet together, so key a wide push-off stride.

slash: NEW nat/prop/read/energy = 5/8/3/4 ; OLD = 7 ; fixes: from f3 to f5 the blade stays vertical overhead, so it reads as a raise, not a cut. It's also hidden on f2 (the 40ms hit frame) and gone on f6. Add a horizontal smear on f2 and swing the blade across and down on f3, so the blade shows on every frame.

overhead: NEW nat/prop/read/energy = 7/8/6/6 ; OLD = 7 ; fixes: this is the best NEW action, with a clear windup on f0 and a good smear on f3. f2's smear is too small and clipped behind the head, so lengthen it or merge it into f3. The f1 windup is under-extended, so raise the blade higher behind the head.

hurt: NEW nat/prop/read/energy = 6/8/5/5 ; OLD = 6 ; fixes: f1 is arms-out with no recoil, so add a 2–3px backward or upward body shift and tilt the head back. The f2 hunch reads well. Keep it, but cut it to about 120ms for a snappier recovery.
