# ANIM_CUT strand: current task (lead, round 3)
Continue from NOTES.md (pixel cutout part-rig; char-map parts; tools/compose.py; Opus artists via tools/artist.sh). r1 crit avg 4.6; r2 changes in progress.
Rules: never Read images >1000px; keep each response/tool call short; delegate big grids to Opus artists (account bni_requests) who write files directly.
1. Simplify parts to the locked Level D design (v2/design/DESIGN_SPEC.md, v2/design/turnD/): no lapel lines, no blush, mitten hands, flat 2-tone hair, flat bow, obi kept, 2px katana.
2. SE actions to quality: idle, walk, run, jump, dash, slash (+ _ns no-katana for idle/walk/run/jump/dash). Lively/bouncy/energetic: squash & stretch, anticipation, overlap (bow/hair/hem lag), hit-stop, impact timing. Smears: clean tapered crescent for slash (placed along the actual blade path), dash afterimage that reads as the character (not a solid blob) + speed lines, dust. Fix r1 issues (slash arc misplaced, dash ghost blob).
3. Optional pose reference: v2/hy3d/keys/<action>_SE/ (rigged 3D key poses) when available.
4. Iterate crit rounds (Argon + Opus via tools/crit.sh) until both >=7 per action. Then E direction, then mirror W.
5. GIFs: v2/anim_cut/gifs/<action>_<dir>[_ns].gif (6x, #6e6e6e) + sheets. Write DONE with scores when SE+E are >=7.

## LEAD REVIEW (2026-10-26 10:20) of sheets run_SE / slash_SE / jump_SE — address these first
- Identity consistency is GOOD (the point of this approach). Keep it.
- Head: boxy rectangle with a flat top-left corner; make it rounder (chibi skull dome, bob flares at the jaw). The face reads as frontal; shift the features toward the SE side.
- Arms: the red mitten sleeves read as boxing gloves. Make them smaller and tapered, with a skin-tone hand dot.
- Run: the legs barely change between reach and push, and the katana is a horizontal spear poke. Hold it trailing low behind, angled down-back. Give a real stride: back leg extended, front knee up on the air frames, a body bob of 2-3 px, and the arms pumping.
- Slash: the orange circle smear is disconnected from the blade, too big, and the wrong colour. The smear must start where the blade is on the coil and end where it is on impact, hugging the blade path: a thick-to-thin crescent in white/pale steel with a light blue-grey edge, not orange. Impact must show the blade extended forward-down AFTER the arc, with the body twisted into it. A 1-frame white flash + hit-stop is good.
- Jump: the katana stays rigidly diagonal across the body in every frame. Let it swing with the arm (raised on the launch, trailing on the fall). Add more stretch on the launch and more squash on the land (2-3 px wider, 3-4 px shorter).
- After fixing, re-crit and post the new sheet paths in NOTES.md.

## LEAD NOTE (10:40)
anim_redraw's run (v2/anim_redraw/sheets/run_SE_v3.png) has much better leg and body poses than ours, using your stand_SE head as its master. Look at it: copy its stride, lean and trailing-blade poses into your leg/arm library, or treat Gemini poses as pose references for your parts. When you round the head part, write the new head path in NOTES.md so anim_redraw can re-stamp from it.
