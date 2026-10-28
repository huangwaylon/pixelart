# ANIMATE96 PILOT REPORT: idle_SE + walk_SE, full 96 px pipeline (2026-10-27)

Outputs are in v2/animate96/gifs/: `{idle,walk}_SE.gif` (4x on #6e6e6e, real ms), `_1x.png` (1x RGBA strip), `_sheet.png` (guide | frame per key), `_fx.json`. Work dirs are v2/animate96/work/{idle,walk}_SE (fNN = artist output, cNN = post output). Critiques are in v2/animate96/crit/. The step log is NOTES.md.

## Result
- **QC gate (`qc_gate.py clip`):** idle_SE PASS (7/7 items) and walk_SE PASS (7/7 items). Reports: v2/qc/out/clip_{idle,walk}_SE/report.txt.
- **Per-frame lint + gate + eyecheck:** 12/12 frames OK. The head re-paste restored 0 px in every pass, so the artists never touched the locked head.
- **Critic scores after the fix round** (final quality / master consistency / motion / 1x readability / no boiling, each /10):

| clip | critic | final | master | motion | 1x | no boiling |
|---|---|---|---|---|---|---|
| idle | Argon | 6 | 9 | 5 | 7 | 4 |
| idle | Opus | 6 | 7 | 5 | 7 | 4 |
| walk | Argon | 4 | 8 | 3 | 5 | 7 |
| walk | Opus | 5 | 7 | 3 | 5 | 4 |

  For comparison, round 1 scored idle 6/8/5/7/5 and 5/5/4/6/3, walk 5/7/3/6/7 and 5/6/4/6/4.
- **Verdict:** the pipeline integration is sound. Master consistency is good (head, face, colours, palette). **Motion is not final quality yet.** The remaining problems are mostly in the guides plus some per-frame redraw boiling (see "Open quality issues").

## What broke, and what was fixed
Every patched file has a `*.bak_a96` backup. Without the new options, each tool behaves exactly as before.
1. **The eyecheck and gate hooks were never called by ff_redraw.** New options: `--qc gate,eye` runs `qc_gate.validate_hook` and/or `eyecheck.qc_hook` inside `validate()`, so artist retries receive the fix lines from both.
2. **Gate bug: expression frames were compared against the neutral master.** Their eyes, bow (mouth pixels were read as bow) and eye row produced false FAILs: cheerful 3, joy 10, pain 9, and so on. Fix: `qc_gate.ref_with_stamp()` builds the reference from the master plus the frame's stamp at its origin. All 6 expressions tested now give 0 false FAILs.
3. **Gate bug: the key-name regex overrode explicit flags.** Walk "contact" frames were treated as rest frames (row checks) and needed both feet down, but the mocap contact has 1 foot down. Fix: explicit `frames.json` `rest` wins, and contact need = `min(need, feet_down)`. `prep` writes both `feet_down` (counted from the guide) and `rest` (from `--rest-keys`).
4. **Head was not locked.** The old prompt said "paste the stamp". Fix: `--head-lock` computes a per-frame anchor, pre-seeds fNN.txt with the stamp, uses a body-only prompt, and re-pastes the stamp after every artist pass.
   - x = stamp origin + guide head_centre joint + bias.
   - The bias is constant per view: it comes from a head-silhouette IoU fit on idle and is reused from `ROOT/idle_<V>/frames.json`. Per-clip fits clamped on big poses (jump, throw, dash).
   - y: walk and idle use `--head-bob N` (rig head height scaled to 0..N px; highest = master row). Other acts use the snapped joint.
5. **Head y jittered or inverted with the frames_H feet snap.** The idle rig foot slides 2 px down on "down", and the SE walk far-foot contact sits 3 px higher. The `--head-bob` option above fixes this.
6. **Idle key "rise" was treated as airborne** (name heuristic), so its feet were not snapped and it got no feet check. Fix: `air` comes from guide `frames.json`.
7. **Expression names did not match the stamp names**, and missing stamps silently fell back to neutral. `smile` and `squash` have no m96 stamp. New option `--expr-alias smile=cheerful,squash=blink_closed,hurt=pain`, and a missing stamp now prints a WARN (except N, which only has neutral).
   - Idle now uses neutral throughout (`smile=neutral`, following face2/expr_map). Critics saw the cheerful/neutral toggle as face flicker.
8. **The prompt rules were the old 48 px rules** (STYLE_GUIDE sections 5, 6 and 10, using old palette chars). New option `--rules v2/animate96/RULES96.txt` supplies 96 px rules with the real palette chars, master proportions, single-K soles and "start from the master body".
9. **Lint failed the master itself** (R1 16 interior K, O3 jaggies), which caused pointless retries. New option `--lint-rel`: O3 is dropped (the gate only WARNs on it), and R1 is tolerated up to the master's count + 4.
10. **post.py was 64-cell specific**, used the old fx/ manifest, and had no walk FX. New `animate96/tools/post96.py` (the old post.py is untouched):
    - `clean`: head re-paste, deboil, a static-region boil report, `--dx` clip shift, `--sock-thin`.
    - `out`: fx96 dust_step at walk/run contacts (walk: contact + 1 frame), 4x GIF, 1x strip, guide|frame sheet.
    - `qc`: runs the gate.
11. **Pivot x was off: the SE guide body sits 2-3 px left of the master** (PX 61). The gate PIVOT check gave -2 px on idle "up". Fix: `post96 clean --dx 2` for both SE clips. For the fan-out, measure each view on idle first (see below).
12. **Sock flicker:** the d highlight was drawn as 2-px stripes, unlike the master's 1-px streak. `--sock-thin` reduces each run to one d pixel (29 px in walk).
13. **Critique fix round** (`tools/fix96.py`, crit/fix_r1.json):
    - idle: f00 rebuilt as the key frame; f01-f05 rebuilt from f00 with only the head offset moved.
    - walk: T-pose arms (f00, f01), kicked contact leg (f00), lifted back leg (f04), double-K soles.
    - One extra targeted fix (fix_r1b) for the walk f03/f04 back leg, which came back as a thin "stick" after the first fix. After all fixes, both gates PASS.

## Time and cost per frame
- **Draw** (lint + gate + ≤2 retries): key frames f00 took 339 s and 461 s; other frames 131-314 s; mean 246 s per frame.
- **Wall time:** 12 frames in 907 s at 9 parallel jobs.
- **Critique fix round:** 77-437 s per frame, mean 210 s. Targeted fixes about 95 s.
- **Per finished frame:** about 7.5 min of artist time including one fix round; about 50 s wall per frame at 9 jobs.
- **Artist calls:** 31 for drawing (1.6 per frame on the first pass), plus 13 fix calls and 4 critic calls. API errors or retries: 0 on all 3 accounts (bni_requests, nsystem4, be_system).
- **Cost: not measured.** `claude -p` text mode does not report usage, so I can't give a dollar figure. Each call reads the master and guide char-maps (16 KB each) plus 1-2 PNGs and writes a 16 KB grid 1-3 times. If accounting is needed, add `--output-format json` in `call_artist` before the fan-out.

## Recommended concurrency
- **9 parallel jobs** (3 per account): no errors in the pilot, and per-call times did not degrade.
- 12 is probably safe with all 3 accounts healthy but was not tested.
- run96 draws f00 of every clip first (the continuity key), then the rest.

## Fan-out (35 clips, 215 frames). Estimate: about 1.7 h of drawing at 9 jobs, plus about 1 h for one critique fix round.
The dry run is done: `fanout.sh prep1` and `prep2` into a temp root prepped 35/35 clips (anchors, stamps, feet_down, bias all present). Commands, run in this order:
```
zsh v2/animate96/tools/fanout.sh prep1 [v2/hy3d/frames_H2]   # 5 idle clips -> v2/animate96/fan (writes per-view head_bias)
zsh v2/animate96/tools/fanout.sh draw1                       # run96.py pool 9 over idle_S idle_SE idle_E idle_NE idle_N
zsh v2/animate96/tools/fanout.sh post1                       # post96 clean/out + gate; read "PIVOT ... drift" per view -> set DX[v] = -drift in fanout.sh
zsh v2/animate96/tools/fanout.sh prep2 [v2/hy3d/frames_H2]   # walk run jump dash hurt throw x S SE E NE N (reuses idle head_bias)
zsh v2/animate96/tools/fanout.sh draw2                       # pool 9, 30 clips
zsh v2/animate96/tools/fanout.sh post2                       # gifs -> v2/animate96/gifs/<act>_<V>.gif + gate per clip
# then per clip: critique boards (tools/critboard.py CLIPDIR OUT.png) + one fix round (tools/fix96.py ROOT 9 FIXES.json)
```
What fanout.sh sets for each prep:

| setting | value |
|---|---|
| PX per view | S 62, SE 61, E 68, NE 70, N 65 |
| DX per view | SE 2, others 0 until measured in post1 |
| poses: walk | mocap/poses_mocap.json |
| poses: throw | throw/poses_throw.json |
| poses: other acts | unarmed/poses_unarmed.json |
| expression aliases | idle `smile=neutral`; other acts `smile=cheerful,squash=blink_closed,hurt=pain` |
| head y | idle `--head-bob 1`, walk `--head-bob 2`, other acts snapped joint |
| rest frames | idle `--rest-keys up` |
| on every prep | `--head-lock --qc gate,eye --lint-rel --rules RULES96.txt --palette pixelize/palette.json --master EC0_<V>_96.txt` |

To switch to H2: pass `v2/hy3d/frames_H2` as the second argument to prep1 and prep2. "FRAMES H2 READY" had not appeared in g96/NOTES.md as of this report.

## Open quality issues (fix before calling clips final)
1. **Guides (frames_H):**
   - Mocap walk arms are spread wide (the artist copied a T-pose).
   - The stride is asymmetric: the contact2 legs are nearly vertical.
   - The idle rig foot slides 2 px.
   - The run "pass" head drops 14-18 px.
   - **Recommendation: wait for H2**, or run frames_H only as a draft fan-out.
2. **Boiling (no-boiling score 4/10):** per-frame redraws change the legs, hem and hands. For idle and holds, run the fix96 "rebuild from f00" pass by default (it is already proven to pass the gate). For cycles, the critics ask for a mirrored half-cycle (f03-f05 = mirror of f00-f02).
3. **Walk motion is 3/10:** the arm swing is small or frozen and there is no follow-through on the hair/bow. The bob is now 0-2 px via the head anchor.
4. **Dust_step on walk:** 2 frames. Opus called 3 frames too heavy, so the effect may be optional for walk.
