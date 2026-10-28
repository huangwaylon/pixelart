# ANIM_REDRAW strand: current task (lead, round 3)
Continue from NOTES.md (Gemini redraw from master + guide, snap/quant/clean, head stamp, procedural blade, FX via tools/fxs.py). Opus was redrawing the SE master to Level D2 as a text grid (master/).
Rules: run long generation jobs in the foreground (or wait on them) so they get cleaned up; never Read images >1000px.
1. Finish the Level D SE master (v2/design/DESIGN_SPEC.md, v2/design/turnD/). Lock head stamp + procedural blade.
2. SE actions: idle, walk, run, jump, dash, slash with smears/afterimages/dust/flash/hit-stop; lively, bouncy timing. Strict cleanup: palette lock, no orphans/jaggies, kill inter-frame shimmer in static regions, feet pinned.
3. Optional pose guides: v2/hy3d/keys/<action>_SE/ (rigged 3D keys) when available, else v2/anim/guides.
4. Crit each action with Argon + Opus (account be_system), >=3 rounds. GIFs: v2/anim_redraw/gifs/<action>_SE.gif (5-6x, #6e6e6e) + sheets. Write DONE with scores when SE set is done.

## LEAD REVIEW (10:40) of sheets/run_SE_v3.png
- The best run so far in the project: real stride, lean, trailing katana, speed lines, dust. Keep this direction (48px, master = anim_cut hand-pixeled head).
- Frames 4 and 8 (right column): the head turns away and the face is mostly hidden, reading NE. Re-stamp the locked SE head there.
- The head silhouette is still boxy (flat top-left corner). Round the skull dome. Coordinate via the master: if anim_cut rounds the head part, re-stamp from it.
- Next: apply the same pipeline to walk, jump, dash and slash at 48px. The hybrid is promising: Gemini for body and leg poses, plus locked hand-pixeled head and blade parts.
