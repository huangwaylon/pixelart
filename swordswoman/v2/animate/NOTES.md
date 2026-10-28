# ANIMATE strand (pilot) NOTES
Task: walk/run/slash SE (katana master SE_k) from A=hy3d/frames, B=hy3d/frames_mocap -> 6 clips, FX, gifs, crit. Write PILOT_DONE at end.
- step0 (fresh): read harness/masters/fx. Harness gaps: fixed workdir anim_cut/ff/<act>_<dir> (A/B collide), single stamp (no per-key expression), keys.json ms ignored. Patching ff_redraw.py (backup ff_redraw.py.bak_animate): --root, per-frame 'stamp' in frames.json, ms from keys.json.
- step1 22:20: prepped 6 clips -> animate/work/{A,B}/<act>_SE (frames.json has per-key expr+stamp, abs src). Driver animate/tools/run_draw.py (global pool, phase1 = f00 of all clips). Launching draw jobs=9, log animate/work/draw1.log
- step2 22:22: wrote animate/tools/post.py (clean: restamp expr head + deboil 1-frame blips -> cNN.txt; out: FX composite gif/strips; sheet A vs B; review strip). Draw running (bg).
- step3 STOPPED by lead (masters' proportions rejected; rebuild first). Killed run_draw.py (no claude-as/lint children left). Had 16/38 frames drawn (all f00 + walk_A all + run_A f01,f03), all lint-OK in 0-2 fix rounds (f00 ~3-8 min, others ~1.5-3.5 min). Deleted animate/work/ (frames on rejected masters). No GIFs, no critique, PILOT_DONE not written.
STATE FOR RESUME: tools kept -> animate/tools/run_draw.py (global pool driver, phase1 f00 of all clips; MASTER hardcoded masters/SE_k.txt), animate/tools/post.py (clean/out/sheet/review; untested on real frames). Re-run: prep 6 clips (cmd in step1 below), re-add per-key expr+stamp and abs src to frames.json, then run_draw.py 9 A/walk A/run A/slash B/walk B/run B/slash.
  prep: ff_redraw.py prep <act> SE --root animate/work/<A|B> --guides hy3d/<frames|frames_mocap>/<act>_SE/s48 --gpivot 48 76 --gscale 4
HARNESS PROBLEMS (ff_redraw.py; patched, backward-compatible, original at anim_cut/tools/ff_redraw.py.bak_animate):
  1. workdir hardcoded anim_cut/ff/<act>_<dir> -> A/B sources collide. Added --root / FF_ROOT.
  2. one stamp for all frames -> no per-key expression. Added per-frame 'stamp' in frames.json (used by draw_one + assemble lint). prep still doesn't fill it (done by hand from poses*.json expression).
  3. keys.json ms ignored unless --ms. prep now reads keys.json ms.
  4. frames.json 'src' is relative to the caller's cwd (artist may not resolve it) -> should be abspath.  [FIXED by HARNESS: abs src; --poses/--stamps fill per-frame expression+stamp; KEY INTENT + blade arc (if guide JSON has blade) in prompt; post.py --sole/--cell/--fx-dy (default offset 0: manifest ground_y = sole row 61 under nominal pivot 62). See HARNESS_NOTES.md]
  5. prompt never names the expression/key intent or blade arc; FX cell offsets use feet row 62 vs harness pivot 61 (1px mismatch).
  6. guide slash A blade is clipped at cell edges x=0/x=63 (smear/impact); mocap B slash blade stays near body, impact tip higher than smear (weak arc).
