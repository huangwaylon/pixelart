# v2/pixel_E: E (side view) strand notes

Method: the pixel strand's pipeline (`v2/pixel/NOTES.md`), adapted in `tools/redraw_E.py`.
- Gemini redraws from [master @8x, anim-strand 4x shaded guide scaled to master height].
- No chaining.
- Then snap to 128², lock the palette, and clean.
- Guides come from `v2/anim/guides/<action>_E/` (`fNN_shade4x.png` plus `frames.json`).

## Step 1: E master
- r1 (2026-10-26 00:48): 4 Gemini candidates generated from SE_katana + idle_E f00 (`work/master_k/`).
  - v1 is the best true side profile: bun at the back, one eye, katana down and back.
  - Saved as `master/E_katana_r1.png` (h=90, 16 colours, 3 orphans).
  - v2 and v3 drifted to a 3/4 view; v0 pulled the bow back.
- r1 critiques: the first attempt failed (Argon empty, Opus 502 floodgate). Rerun on resume.
