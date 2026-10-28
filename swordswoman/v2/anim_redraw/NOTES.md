# v2/anim_redraw: ANIM_REDRAW strand notes (Gemini redraw + heavy cleanup)

## Step 0 (2026-10-26) setup
- Read BRIEF, pixel/NOTES (predecessor pipeline), anim/NOTES (r6 guides).
- Raw redraws from v2/pixel/anim/*_SE are very inconsistent (head size drifts, run poses ignore guide legs, jump double swords). Sheets: work/raw_{run,jump,dash,idle}.png; guide sheets work/guide_*.png.
- tools/gimg.py: gemini image with imageConfig (aspect/size). imageConfig requests hang (>15 min) on floodgate -> not usable; default no-ref output is 1408x768, with a 1024^2 ref output is 1024^2.
- tools/gen.py: N candidates per frame in parallel (master@8x + aligned r6 guide@8x, guide scale from idle rest pose for all actions), per-frame pose hints (tools/hints.json) -> snap/quant/clean into work/<act>_SE/cand/fNN_kK.png.
- First gen run (run_SE, n=3) killed by session restart (exit 137) after ~7 candidates.

## Step 1 (restart x2) tooling
- Restarts kill child processes, even with nohup -> tools/detach.sh LOG cmd... (perl setsid + nohup + disown). gen.py now skips existing candidates (resumable).
- tools/sel.py ACT: scores candidates (0.5 silhouette IoU vs aligned guide + 0.5 lower-third/legs IoU; rejects no-iris / >3 iris clusters) -> work/<act>_SE/sel.json + cands.png sheet.
- tools/fin.py PLAN: erase Gemini blade -> pin feet (y120 or guide lift on air frames) + x locked to r6 head_offset trajectory -> master head-variant stamp (bow can be shifted per frame for overlap/lag) with chin-gap fill -> procedural katana from r6 blade angle (handle d/D, 5px guard, 3px w/n/# blade, L=34) -> orphan clean + outline repair -> temporal de-crawl (isolated <=3px changes in static neighbourhoods revert to previous frame).
- tools/fxs.py PLAN: FX stage (afterimage, speed lines, foot lines, launch streak, dust1-3, blade arc crescent w/n/m tapered+dithered tail, flash, spark, footsmear) + gif (5x, #6e6e6e) + sheet.
- Design strand locked Level D2 (flattest: no lapel lines, no blush, mitten hands, flat bow, no hair strands). Since the master head is stamped on every frame, Opus is redrawing the SE master to D2 as a text grid (master/opus_prompt.txt -> master/SE_clean_grid.txt / SE_clean.png), katana removed (procedural).
- Note: the old master's blade interior is transparent (hollow) - another reason for the procedural blade.

## Step 2 (2026-10-26, round 3 restart) D2 master finished
- Opus (be_system) delivered master/SE_clean_grid.txt + SE_clean.png (128x128, Level D2, katana removed, mitten fist; lint: no off-palette, only eye glints flagged). Visual check OK: flat 2-tone hair, flat bow, V neck, obi band, clean outline. Locked as head-stamp + body master; blade is procedural.

## Step 3 128px D2 run test -> pivot to 48px
- gen.py with D2 master (tag d2): run/jump/dash/slash cands in work/<act>_SE/cand/d2f*. fin.py: x-pin now head-centre + r6 head_offset (cycles: minus mean). run v3 (gifs/run_SE_v3.gif, crit/run_v3_*): Argon 4.5, Opus 4.5. Problems: body off-model frame to frame (sleeves/hem/obi boil), head pasted (no tilt), skin specks behind hair, katana detached from hand, no arm swing.
- tools/gen4.py: 4 frames per Gemini call (2x2 sheet) -> far better within-sheet consistency.
- Found team standard = 48px char in 64 cell (DESIGN_SPEC "48 px recommended"; anim_cut builds 64 cells). 128/~100px was off-spec. PIVOT: new 48px pipeline.
  - m48/SE.png (+SE_grid.txt): anim_cut stand_SE (hand-pixeled 48px D-level) with p->2, j->H (pure D2). FOOT=59.
  - tools/gen64.py: 2x2 sheet, 512px panel = 64 cell @8x, guides shade4x->8x aligned (idle overlay verified /tmp check), hints48.json (sword words -> fist). Output work48/<act>/cand/<tag>fNN_kK.png.
  - run test (tag a, n=2): consistent, on-model, good poses.

## Step 4 48px pipeline v1 + hand-keyed mannequin guides
- tools/fin48.py (64-cell finisher: palette grid, keep_main, steel erase, feet pin FOOT=59 - lift, obi-x pin, master head template-match stamp + neck fix, procedural 2px katana, outer outline, orphans, decrawl, FX: smear/afterimage/speed/dust/spark/lines, 6x GIF #6e6e6e + 3x sheet w/ 1x strip). tools/crit48.sh (Argon + Opus be_system on the sheet).
- run_SE_v1 (r6 guides, gen64 tag a): Argon 4.5, Opus 4 (crit/run_v1_*). Problems: legs don't alternate (r6 guides have tiny unreadable legs, f4-7 = f0-3), x slide, passing frames too long, katana floats, FX too small, neck skin bar.
- r6 guides judged weak -> tools/pose48.py + tools/keys48.py: hand-keyed 3D-ish mannequin (near limbs light, far dark, katana drawn from the near fist at the keyed angle), per frame ms/head variant/bow lag/blade angle/hints. Exported work48/<act>/guide/{fNN.png,frames.json,sheet.png}. gen64 --mine [--sword].
- run tag n (mannequin, no sword) -> clearer alternating strides. Hand detection for procedural blade unreliable -> now Gemini draws the katana (guide shows it), fin48.fit_blade PCA-fits Gemini's steel (grip+angle), erases it, redraws the procedural 2px blade (angle = key + 0.6*deviation, tol 35deg).
- tools/idle48.py: idle built procedurally from ONE finished frame (breath squash, head lag, bow lag, blink) -> zero shimmer.
- Generating tag s (mannequin + sword) for all actions.

## Step 5 (2026-10-26 ~11:00, resumed) round head + state check
- State: tag s (mannequin + sword) cands complete for all actions (walk 8f, jump 9f, dash 6f, slash 8f, idle 1f); nothing half-written. Lead's "run_SE_v3" review matches sheets/run_SE_v2.png (48px, 2x4 grid); the 4160px run_SE_v3 sheet is the old 128px run.
- Boxy head fix: tools/roundhead.py -> m48/SE.png + SE_grid.txt now has a rounded skull dome (superellipse, rows 15-27) and the bun reads as a separate round bun with a notch; face/bow/body untouched. Backup m48/SE_box*.png/txt. anim_cut's own round-head task (r5H) not delivered yet, so this is ours.
- fin48 master_head: bow-lag shift no longer drags the bun outline.
- Turned-away head (lead f4/f8): every fin48 frame is re-stamped with the locked SE master head; low template scores (f4 0.78, f6 0.76 in v2 log) were where Gemini's head was turned. Will force head_dx/dy and verify stamp sits on the neck.

## Step 6 all SE actions v1 (48px, tag s cands + locked round master head)
- fin48: erase_steel also drops u/U (Gemini steel quantised to beige) + bare '#' outline strands (fixed double blades); smear FX never paints over the head stamp (prot) and has a 'dith' tail option; FIN_PAD=top,side env gives a tall cell (jump uses 16,8 -> 64x80 output) so the jump can rise ~27px.
- Plans: tools/plans_s.py (walk v1 k1 x8; jump v1/v2 picks + per-frame dy for a head-top arc 37->24->14->10->13->24->land; dash v1 ghosts/speed/skid dust), slash plan_v2 hand-built (ready, windup, smear 40ms on lunge pose, impact+spark+shake 100ms hit-stop, fade, follow, recover, ready). run v4 = v2 re-stamped with round head.
- idle48 rewritten: rigid row-delete squash (torso at waist, head at neck) + blink, base = slash v2 c00 ready stance -> no bow gaps.
- Sheets: sheets/{idle_SE_v1,walk_SE_v1,run_SE_v4,jump_SE_v2,dash_SE_v1,slash_SE_v2}.png. Running crit round 1.
- crit r1 (crit/*_{v1,v4,v2}_*): Argon/Opus idle 5.5/5, walk 4/4, run 4.5/5, jump 5/5, dash 5.5/5, slash 5.5/5. Common: head/bow rigid copy-paste, katana angle/position popping, Opus got blank ms (plans lacked ms). walk: march knees, leg mush; jump: no launch stretch, blade through skull, tip clips cell; dash: dither ghost = noise, weak anticipation, upright skid; slash: smear dotted/thin, impact spark tiny, F3=F4.

## Step 7 round 2
- fin48: body_ops per frame (vsq +n squash / -n stretch at the obi row; shear k = top leans k px), bow lag fixed (old bow outline removed, skull top re-closed, dy clamped -1..2).
- idle48: 3px settle with head trailing, half-lid/closed/half blink, 1px overshoot-up stretch (10f).
- walk: regenerated tag w (gen64 --mine --sword + "calm walk, feet low, legs separated" extra); w k1 chosen, +-1 bob, squash head on contacts, bow lag.
- tools/plans_r2.py: run v5 (keyed trailing blade, behind on crossing frames, contact dust, air speed lines), jump v3 (crouch vsq2, launch vsq-2 + stretch head + launch lines, f3 = f2 pose hang 140ms, fall lines, land vsq2, blades trail left behind body, no clipping), dash v2 (anticipation squash+lean back, solid 2-tone ghosts, burst2 +3px forward, skid shear -3 + bigger dust), slash v3 (windup blade over the shoulder, solid 9px smear, impact vsq1+shear+flash blade+6px spark+2px shake 110ms, fade, recover). Critting r2.
- crit r2: Argon/Opus idle 5.5/4, walk 4.5/5, run 4.5/5, jump 5.5/6, dash 5.5/5.5, slash 5.5/5. idle: blink turned katana glints peach (bug), torso cut through the sword; walk: dy bob lifted planted feet; run: blade vanishes f1 (behind), speed lines blink; slash: X spark on F4, windup blade hidden, tip clips right edge; dash: solid ghosts = dress-coloured slabs, skid upright.

## Step 8 round 3
- fin48: spark = 3x3 core + long w/n rays + warm e/E diagonals; afterimage 'outline' (hollow cool ghost); smear may cross hair but never the face.
- idle48: blink only in head rows; idle v3 squashes at the knees (cut 53) so the sword stays rigid; 2px knee give + 1px head trail + blink 60/110/60 + overshoot.
- tools/plans_r3.py: walk v3 (waist-squash bob, feet planted, blade lag sway), run v6 (one trailing blade angle in front, continuous alternating speed lines), dash v3 (hollow n/m ghosts, deeper anticipation, skid vsq2+shear-4), slash v4 (all 4px left, windup blade across the bun, impact 80ms + big starburst, no F4 smear). Critting r3.
- crit r3: idle v3 5/6, walk v3 5/4, run v6 4.5/5.5, dash v3 5.5/6, slash v4 5.5/6. Extra pass: walk v4 (no stretch head, eased ms) 4.5/4, run v7 (symmetric lifts + stretch on up frames) 4.5/4 -> kept run v6.
- FINAL: copied to gifs/<action>_SE.gif + sheets/<action>_SE.png: idle v3, walk v4, run v6, jump v3, dash v3, slash v4. Wrote DONE with scores.
- Remaining issues: walk/run legs mush at 1x and stride halves don't mirror (Gemini limit; next step would be hand-pixelled leg parts or Opus leg redraw per frame), rigid head stamp, katana angle pops, 1-2px body drift.

## Step 9 (round 2 lead task: legs / heads / katana) setup
- Lead: slash + dash = project baseline. Round 2: Opus hand-pixelled walk/run legs, 3-4 locked head stamps (+ rounder skull), pre-drawn katana sprites with smooth angle sequences, re-crit.
- fin48: kat_place() pastes anim_cut parts/common/kat_DD.txt (16 dirs, grip pivot, nearest angle) instead of the procedural blade (plan 'kat': 0 = old blade); apply_legs() replaces rows from a '; y0 N' char-map (frame 'legs'); body stage dumped as <ver>/bNN.png.
- Stage frames work48/{walk,run}/k1/bNN.png (walk v4 / run v6 plans). Opus (be_system) jobs: work48/<act>/legs/prompt.txt -> legs/fNN.txt (rows 46-63) checked with tools/legprev.py; m48/heads/prompt.txt -> heads/{neutral,up,squash}.txt checked with tools/headprev.py.
- Opus jobs had to run in the foreground (background shell: "Proxy startup failed ... no available ports"). Delivered: m48/heads/{neutral,up,squash}.txt (rounder dome + separate round bun; up = irises/brows up 1px; squash = +1 col/-1 row, bow 1px lower) and walk/run legs/fNN.txt (near light 2/d, far dark 1/D, swap between half-cycles, knee up on passing, boots on row 59, planted foot fixed).
- neutral head written into m48/SE.png (prev: SE_r1.png). fin48 master_head loads heads/up|squash.txt; 'lean' = neutral stamp +1px forward/down; back/stretch now = neutral (locked).
- tools/plans_r4.py: walk v5, run v8 (Opus legs, blade behind body d9 / d8-d9), jump v4 (heads squash/up/up/up/../squash; blade d8 d6 d7 d7 d8 d8 d8 d9 d9), dash v4 (lean on burst; d8 d8 d8 d9 d9 d9), slash v5 (lean on smear/impact; d1 d7 d15 d15 d14 d0 d1); idle v4 from slash v5 c00. Critting.
- crit after heads/legs/katana: idle v4 4.5/4 (Gemini hilt remnant + sprite = "bent crowbar", 60ms blink frames), walk v5 4.5/5 (f3/f7 both feet up, near/far same value), run v8 4.5/5 (near/far same value, static speed lines, d9/d8 pop), jump v4 5.5/6, dash v4 5.5/5, slash v5 5/6.
- Fixes: Opus legs pass 2 (far leg skin 1 only + boot D, near 2 with 3 highlight, walk f3/f7 support foot on row 59; pass-1 backup legs/r1/); fin48 plan 'head_lock' (head x locked to the pinned obi) for walk/run; run speed lines drift left per frame, ms 55/65/80/70; idle v5 base = slash v5 c00 with the Gemini hilt line removed (work48/idle/base_v5.png), slower blink 80/120/80.
- crit pass 2: idle v5 5.5/5, walk v5 4.5/5, run v8 5.5/5. Then walk vsq re-levelled (hair-top bob 22/23/22/21) + fixed hilt path, run one blade angle d9 + smooth hilt path + ms 70/80/50/60: walk v5 4/5, run v8 5.5/5.5.
- FINAL round 2: gifs/<action>_SE.gif = idle v5, walk v5, run v8, jump v4, dash v4, slash v5. Wrote DONE2.
- DONE3 written (v2/anim_redraw/DONE3).
