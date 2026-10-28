# G96 notes
- 12:42 start: fresh instance, created g96/
- step1: wrote g96/scripts/meas96.py (96px class grids + sections for masters and rig renders; masters' eye/chin/bowcut manual in g96/master_manual.json). Patched throw/scripts/rig_lib.py (backup rig_lib.py.bak_g96): SOCKS=1 -> knee ball takes leg colour at the knee.
- step2: cal96.py (repro_h -> render_cal 4x -> 2x2 majority 128 cell -> meas96), check96.py, search96.py (greedy, as rigcal search.py). s0 (= rig G state + sock) 84 fails; manual s1 (head 0.98, FIG_PX 46, sock .75, boots.top .33, skirt h 1.25, spread 1.9) 45 fails. Starting search srch1.
- srch1 (7 rounds): 45 -> 38 fails (slow; structural misfits). work/srch1/best.json
- manual tests (tryv.py): abd sign: smaller abd = arms out; a5f2 (abd 5, flare 2) 37 fails
- knee now = master manual crease row vs rig projected knee joints (render json). L4 manual variant (thin legs prof .15/.19/.13/.16, boots sx .65 sz .6, spread 1.0, hands .55, skirt w .8, abd -10).
- LEAD MSG: user wants hair knot/bun/bow CENTRED on the head (midline, back-top); masters being regenerated; keep bow excluded from crown; re-measure head region after 'FINAL SET v2 (centred bow)' in v2/hair/NOTES.md.
- repro_h: bow/bun forced onto the head midline (x centred) + spec bow.dy/dz, bun.dy/dz offsets (back-top placement).
- meas96: rig hem = skirt part bottom; obi = largest contiguous obi block; rig bow+bun (group 10) = B (excluded from crown, as knot). M2 state (work/t5/M2.json: thin legs, socks .83, flare 1.8, abd 0, shin .95 thigh 1.3) = 38 fails; many residuals are master view inconsistencies (S face/eye 6px lower than SE/E; crown->chin S 34 SE 31 E 25).
- srch2 (7 rounds from M2): 38 -> 29 fails (work/srch2/best.json); crown now low because the bun (knot) is excluded while old masters show offset knot -> head region waits for centred-bow masters.
- 13:16 new centred-bow masters in pixelize/top1 (13:10) -> re-checking master manual rows
- master_manual.json redone for centred-bow masters (S eye 53 chin 61 knee 104; SE 54.5/62/103; E 51.5/59/103; bowcuts). crown rule (both): first row with non-bow run >= 50% head width.
- vs new masters: srch2 best + sock .9 + skirt h 1.2 (work/t7/b3.json) = 31 fails. Starting srch3.
- srch3 8 rounds: 31 -> 22 fails (work/srch3/best.json). Lead: clean up processes/temp as I go; ps check before final.
- fixed-PPU calibration (scripts/render_cal96.py PPU_FIX; state env PPU replaces FIG_PX), skirt.flarez, arms.flarez keys; meas fixes (bow-colour blends, sock blend noise). e1 (work/t11/e1.json) 24 fails. srch4 from e1.
- RIG H built: hy3d/rigs/H/{parts (repro_h, spec_solved.json), rig_parts.blend + rest_S/SE/E (rig_lib MOCAP=1 ELBOW=1 SOCKS=1), PROPORTIONS_H.json, calib_state.json, check/check_<V>.png + residuals.txt/json} (copies g96/residuals.*). State g96/work/H2_state.json (bow dz -.3 dy -.15 = back-top, centred). Fails S 8 SE 9 E 6 (NE 8, N 7 checks) - not all within +-1: remaining = master view inconsistencies (S head narrow 26 vs N 31; S/SE/E face rows), SE 3/4 sleeves/skirt/thigh merge, E foot.
RIG H READY (hy3d/rigs/H; PPU 26.304/96-cell = 52.608/192-cell; render env MOCAP=1 ELBOW=1 SOCKS=1 PARTS=v2/hy3d/rigs/H/parts)
- step3: frames driver g96/scripts/frames_H.py (192 cell, pivot 96,152, PPU_FIX 52.608, 4x=768 px; patched throw/scripts/render_jobs.py env CELL1/PIV1/PPU_FIX, backup .bak_g96)
- frames idle_SE: 6 frames (3s)
- frames idle_S: 6 frames (2s)
- frames idle_E: 6 frames (3s)
- frames idle_NE: 6 frames (2s)
- frames idle_N: 6 frames (2s)
- frames walk_S: 6 frames (3s)
- frames walk_SE: 6 frames (3s)
- frames walk_E: 6 frames (3s)
- frames walk_NE: 6 frames (3s)
- frames walk_N: 6 frames (3s)
- frames run_S: 6 frames (3s)
- frames run_SE: 6 frames (3s)
- frames run_E: 6 frames (3s)
- frames run_NE: 6 frames (3s)
- frames run_N: 6 frames (3s)
- frames jump_S: 8 frames (3s)
- frames jump_SE: 8 frames (3s)
- frames jump_E: 8 frames (3s)
- frames jump_NE: 8 frames (3s)
- frames jump_N: 8 frames (3s)
- frames dash_S: 5 frames (2s)
- frames dash_SE: 5 frames (2s)
- frames dash_E: 5 frames (2s)
- frames dash_NE: 5 frames (2s)
- frames dash_N: 5 frames (2s)
- frames hurt_S: 4 frames (2s)
- frames hurt_SE: 4 frames (2s)
- frames hurt_E: 4 frames (2s)
- frames hurt_NE: 4 frames (2s)
- frames hurt_N: 4 frames (3s)
- frames throw_S: 8 frames (6s)
- frames throw_SE: 8 frames (6s)
- frames throw_E: 8 frames (7s)
- frames throw_NE: 8 frames (8s)
- frames throw_N: 8 frames (8s)
- step3 done: 35 clips (idle run jump dash hurt = unarmed/poses_unarmed.json, walk = mocap/poses_mocap.json, throw = throw/poses_throw.json; katana 0) -> hy3d/frames_H/<act>_<dir>/s96/ (fNN_matid/shade/sil.png at 4x = 768 px, frames.json with ms/pivot/head_centre/head_top/hip/pts/expression, keys.json, preview.gif/sheet.png/onion.png via hy3d/scripts/post.py; throw: ball block in 192-cell px). Game-res GIFs g96/gifs/<act>_<dir>.gif (128 cell, 3x). No frame touches the 192 cell border (rows 31..166). Re-run: .venv/bin/python -I v2/g96/scripts/frames_H.py [ACTS] [VIEWS] (skips done; delete a clip dir to redo).
- cleanup: temp work dirs/renders deleted; kept work/*.json states, srch*/best.json. Patched shared scripts (env-gated, backups *.bak_g96): throw/scripts/rig_lib.py (SOCKS=1 knee colour), throw/scripts/render_jobs.py (CELL1/PIV1/PPU_FIX).
FRAMES H READY
ff_redraw params (s96 guides, 128 master cell, masters' bottom row 124):
  ff_redraw.py prep ACT DIR --guides v2/hy3d/frames_H/<act>_<DIR>/s96 --cell 128 128 --pivot PX 124 --gpivot 96 152 --gscale 4
  PX (master feet x): S 62, SE 61, E 68, NE 70, N 65 (64 is fine as a generic value; prep snaps the feet row for standing frames anyway)
  guide geometry: 192 cell at 1x, pivot (96,152), PPU 52.608 px/unit, in-game 128 cell = crop x32..160 y32..160 (pivot 64,120). Sock matid sRGB ~(38,42,71) (with the 18-colour palette nearest_char maps it to d).

## Recal to polished masters
- start 2026-10-27 17:29:27 (fresh instance)
- step1a: meas96.py now reads m96/masters (env G96_MASTERS/G96_MANUAL to reproduce H: pixelize/top1 + master_manual_H.json; backup scripts/meas96_H.py); red sock-cuff band (rows>=93) -> sock. master_manual.json redone from polished masters (old -> master_manual_H.json): eye S52 SE53 E52, chin 61 all, knee S103 SE101 (sock 'd' highlight start) E104 (bump), bowcut S50 SE51 E63 NE64 N64. Master sections: sole 125, shoulder S63 SE62 E64, waist 76.5, hem 91 (N90), socktop 95 (NE93 N94), ankle 114, head w S28 SE33 E31 NE31 N29.
- step1b: rig H vs polished masters (g96/work2/h0): fails S 9 SE 8 E 6 (NE 9, N 8). cal run ~3 s. Starting search g96/work2/s1 (from H state, 5 views, W_CHECK .3).
- s1 stopped after 5 rounds (371 -> 289, fails 23 -> 18; work2/b1.json). Finding: polished masters' knot/bun is hair-coloured (only red bow/ribbons excluded) -> meas96.rig now keeps the rig bun's hair class (G96_BUNB=1 = old rule); repro_h: bow.scale/bun.scale keys (backup repro_h_H.py). Rig head too wide in S (+5) while SE/E ok -> wx down / wz up; rig bow sits too low from N (rows 42-50 vs master 36-45) -> bow forward+up.
- added search params bow/bun dy,dz,scale + _pose.abd_se (SE-only calib arm pose, cal96.py; backups cal96_H.py/search96_H.py). Start b2 = b1 + bow dz -.15 dy -.04 scale .7 (bow forward/up/smaller: master bow ~22 px wide in S vs rig 33). Search s2 (20 rounds, NPAR 16).
- meas96 rig eye = largest contiguous block of rows with >=2 eye px (fringe blend noise had put spurious 'e' rows at the hairline -> rig eye read 2-3 px high); rig eyes are ~6 rows tall vs master 4 -> eyes.scale/dy searched. New head.sq (repro_h: diagonal xz bulge; masters' head widths S28/N29 vs SE33/E31 are not reachable by an ellipsoid). search96: MULT (multi-scale steps), SOFT (sub-threshold term). b4 = s2 best + eyes dy .06 scale .8. Search s3 (MULT=1,3 SOFT=1).
- CAMERA GEOMETRY: rig face front sits ~13 px (96 px figure) in front of the neck axis -> under the 30 deg ortho camera the eye projects ~6 px lower in S than in E (SE ~4); masters keep one eye line (S52 SE53 E52) -> S/SE face rows prioritised, E eye/chin accepted (documented). E knee re-read as 103 (joint between back notch 102-103 and front bump 104-105).
- SE calib arm pose keys (cal96): abd_se/abd_se_r (abduction far/near), flex_se/flex_se_r (flexion) - the SE master holds the far arm forward-out and the near arm out from the skirt; calib only. SE armpit dropped from the SE section set (near sleeve overlaps torso; master 3-run row = far-hand fingers). search96 SKIP env (E.eye). b6 = b5 + head wx1.0 wz.98 sq.12, eyes dy.1, boots sx1.1 toe.6, SE arms (flex_se -35, flex_se_r 20, abd_se_r -20): fails S4 SE7 E4. Search s4 (MULT 1,3 SOFT 1 SKIP E.eye).
- s4 (6 rounds): 14 -> 6 fails (S armpit-3 knee-2, SE wband-7, E knee-3 ankle-4 whem-2). E ankle = camera geometry of the flared boot rim (front rim z-offset projects lower in S) -> new boots.ramp (repro_h; -0.08 = straight shaft top) fixes it. b8 = s4 best + ramp -.08 + thigh +.06 shin -.04 (knee down). Search s5.
- s5 (7 rounds): 5 fails left (S armpit-3 wfoot-2, SE knee+1.1 wband-7, E knee-1.3) + E.eye. Armpit: rig sleeve leaves the torso ~3 rows above the master's (master sleeve hugs to the obi) -> c4 (arms.shoulder_x .9, torso.width 1.28, arms.dy .03) fixes it; b10 = c4 + torso.waist .5. Search s6.
- SE thighs: masters' SE thighs touch (band 15) while socks stay apart; rig legs were near-frontal (cheat 41) with a uniform gap -> new legs.taper (repro_h, thigh WIDTH narrows to the knee) + prof0 .24 + cheat 28 + boots.sz 1.4 merges the SE thighs only. b11 = b10 + these; search s7 (no parallel tests).
- LEAD MSG: motion being redone -> finish rig H2 calibration only (rig + residuals + RIG H2 READY), no clip renders; stop after. s7 (7 rounds): 11 -> 6 fails.
- RIG H2 built: hy3d/rigs/H2/{parts (repro_h, spec_solved.json), rig_parts.blend + rest_S/SE/E (rig_lib MOCAP=1 ELBOW=1 SOCKS=1), PROPORTIONS_H2.json, calib_state.json (= g96/work2/b12.json = s7 best), check/check_<V>.png + residuals.txt/json}. Bone names, elbow split, centred bow/knot (midline, back-top) kept. PPU 26.304 (96 cell) unchanged -> frames PPU_FIX 52.608, PX unchanged.
  fails vs polished masters: rig H S9 SE8 E6 (NE9 N8) -> H2 S2 SE4 E2 (NE7 N6). Residuals left (each documented):
  E eye -5: CAMERA GEOMETRY - face front ~13 px ahead of the neck axis projects ~6 px lower in S than E under the 30 deg ortho camera; masters use one eye line (S/SE fit to +-1, E carries the rest).
  S wfoot -3: CAMERA-GEOMETRY COUPLING - a wider/toe-boxed boot fixes S but drops the SE/E lowest pixel (toe) by 2 rows, shifting every sole-aligned SE/E row -2 (masters force sole 124 in all views).
  N H/crown +3, waist +2, wobi -3, wshoulder +2, wfoot -2 (check view): CAMERA GEOMETRY - from behind the toe is the far side, rig N sole projects 2 rows higher than S -> sole-aligned N rows shift +2.
  NE crown/H -7 (check view): measure artefact (polished NE ribbon runs down the middle of the hair, crown rule finds row 43); NE wsock/wcalf +7: true NE camera overlaps the legs, master draws them apart.
  SE knee +1.05 / E knee -1.34: master knee reads disagree (S 103 / SE 101 sock-highlight start / E 103); the rig knee joint projects within 1 px across views -> 0.05/0.34 px over.
  SE wobi -3, whem +3, wband +2: SE calib-pose overlap (near arm covers the obi and touches the skirt at hem-2; thighs merged 17 vs 15 at leg yaw cheat 28 - lower cheat drops the SE sole row). Pose-dependent, not part scales.
  S armpit -2: part-shape trade-off (rig sleeve leaves the torso 2 rows above the master's; shoulder_x/torso.width fixes break S obi/waist + SE shoulder). Not camera geometry.
RIG H2 READY (hy3d/rigs/H2; PPU 26.304/96-cell = 52.608/192-cell; render env MOCAP=1 ELBOW=1 SOCKS=1 PARTS=v2/hy3d/rigs/H2/parts; measure: G96_MASTERS=m96/masters default, rig bun keeps hair class, SE no armpit)
FRAMES H2 NOT RENDERED - lead stop (motion being redone with whole-body mechanics). Driver ready: .venv/bin/python -I v2/g96/scripts/frames_H2.py [ACTS] [VIEWS] -> hy3d/frames_H2/<act>_<dir>/s96, gifs g96/gifs_H2 (PPU from H2 calib_state). ff_redraw params when rendered (gpivot/gscale as H, PPU unchanged): prep ACT DIR --guides v2/hy3d/frames_H2/<act>_<DIR>/s96 --cell 128 128 --pivot PX 124 --gpivot 96 152 --gscale 4; PX: H values S 62 SE 61 E 68 NE 70 N 65 were for the old masters - polished masters' feet centres (rows 120-124, mean x) S 63.5 SE 62.8 E 68.3 NE 68.2 N 63.0 -> re-derive PX from the H2 guides when frames are rendered.
- cleanup: work2 test dirs removed (kept work2/b*.json states, s*/best.json + logs, final/meas.json); /tmp files removed. DONE_H2 written (calibration only).
