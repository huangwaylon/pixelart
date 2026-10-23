# Repo cleanup + reorg plan (Phase 1: inventory and plan only)

Status: PLAN. Nothing has been moved or deleted yet. Written 2026-10-23 against HEAD `5051432`.

## 0. Constraints (read before executing)

- **The face/bangs agent is working right now.** Its files: `pipeline/sdf.py`, `pipeline/face.py`,
  `pipeline/tools/make_s4_hd.py`, `data/variants/S4_hd.json`, `data/faces/*` (including the untracked
  `kawaii_hd.json`), `overrides/variants/S4_hd/*` (modified/deleted in the working tree), and `00_REVIEW/r15_face_bangs/`.
  Execution must either wait until that work is committed, or run in a separate worktree/branch that does
  not touch those paths (recommended, see section 6). Nothing below edits, moves or deletes any of those files.
- **`*_r14` animations will soon be promoted into the base names.** Do not delete `data/animations/*_r14.json`.
  The base-name clips (`idle.json`, `run.json`, ...) stay too, until that promotion lands.
- **Releases to keep:** `releases/S4_actions_v1` (v1 rollback, built from `S4_halfup_bow`) and
  `releases/S4_hd_actions_v1` (current hero).
- **Git history keeps everything.** Before deleting, tag the repo (`pre-cleanup`) and push the tag, so any deleted
  round can be recovered with `git checkout pre-cleanup -- <path>`. Do not rewrite history.
- **Build hashes will change, pixels must not.** `build.py:input_files()` hashes every `data/variants/*.json`,
  `pipeline/*.py`, `data/faces/*.json`, `data/props/*.json` and the clip's overrides. Deleting any old variant or
  dead module therefore changes `buildHash` in every `_sheet.json`/`manifest.json`, even though the output pixels are
  identical. Verification compares PNG bytes plus JSON with the hash fields stripped (section 7).

## 1. Inventory

### 1.1 Top level

| Path | Disk | Tracked in git | Kind | Verdict |
|---|---|---|---|---|
| `00_REVIEW/` | 37 MB | 524 files, 37.4 MB | published review rounds (user looks here on GitHub) | keep the latest round per topic, delete the rest (see 1.2) |
| `art/hand/S4/` | 0.5 MB | 76 files | **source**: hand-typed `.pix` grids (busts, turnaround, heads, poses) | keep |
| `builds/` | **2.1 GB** | 0 (gitignored) | generated, 113 immutable build dirs + `latest_*.json` | `rm -rf` locally, rebuildable |
| `data/` | 1.6 MB | 233 files | **source**: variants, animations, palettes, faces, props, illustrations | prune heavily (see 1.3) |
| `docs/` | 0.7 MB | 121 files | kickoff memos, DECISIONS, research, 112 review docs | reorganize into `docs/history/` + 3 new docs |
| `editor/` | 24 KB | 3 files | browser pixel editor (served by `pipeline/server.py`) | keep (has a bug, see 5) |
| `out/` | **171 MB** | **2553 files, 70.1 MB** (committed before `out/*` was gitignored; `!out/boards/` is still whitelisted) | generated, "latest build" copies | untrack all of it, `rm -rf` locally |
| `overrides/` | 0.5 MB | 122 files | **source**: hand pixel overrides | keep `variants/S4_hd` only |
| `pipeline/` | 1.3 MB | 54 files, **including 16 `__pycache__/*.pyc`** | **source** code | delete 3 dead modules, untrack pycache |
| `releases/` | 16 MB | 884 files | frozen engine deliverables | keep S4_actions_v1 + S4_hd_actions_v1, delete H1_* + HERO symlink |
| `README.md` | | | describes the H1/jump era (64x64 jump, `out/jump`) | rewrite (short, current) |
| `START_HERE.md` | | | H1 board-review status from round 5/6, fully stale | delete (fold the useful part into README) |
| `.git` | 424 MB | | history | untouched (no rewrite) |

Tracked working-tree content: ~125 MB. After this plan: ~34 MB.

`out/` tracked content: `out/variants/` 59 MB (37 old exploration variants: A_chibi, BO*, O*, R*, H1*, H2*, C*, T*,
H1_v1_release), `out/boards/` 9.3 MB (round 4-10 comparison boards), `out/jump/` 1.7 MB (classic H0 jump).
None of it is the current hero; everything current is in `00_REVIEW/` or `releases/`.

### 1.2 00_REVIEW rounds (latest per topic)

| Round | Size | Topic | Superseded by | Verdict |
|---|---|---|---|---|
| `r10_concept_art` | 0.3 MB | HD concept portraits (`pipeline/portrait.py`, `face_hd`) | r13_anime_pixel (hand-pixel busts/turnaround/poses, approved) | **delete** |
| `r10_S4_jump` | 0.8 MB | first S4 jump | r11 -> r12 HD -> r14 retime | **delete** |
| `r10_semichibi_candidates` | 1.3 MB | 6 semi-chibi candidates | S4 chosen | **delete** |
| `r10_outline_study` | 0.5 MB | outline styles; the 3 `.md` are byte-identical copies of `docs/research/outline_techniques.md`, `docs/review/r10_outline_{AD,GD}.md` | decision recorded in DECISIONS + LEARNINGS | **delete** |
| `r11_actions` | 4.6 MB | S4 v1 action set (13 clips) | `releases/S4_actions_v1` (same sheets) + HD set | **delete** |
| `r12_hd_model` | 20.2 MB | HD SDF model, boards, STL/OBJ, fix images | (latest HD model) | **keep**. Optional trim: `fixes/` (0.4 MB) and `r13/` (0.5 MB) round snapshots |
| `r12_illustration` | 1.0 MB | vector illustrations | **rejected by the user** | **delete** |
| `r13_anime_pixel` | 0.7 MB | hand-pixel busts, turnaround, heads, poses (APPROVED) | (latest illustrations) | **keep** |
| `r13_sprite_face` | 1.2 MB | SE/SW 3/4 face cel fix on legacy S4 | r12 HD face_eyes + `r15_face_bangs` | **delete once r15 is published** |
| `r14_retime` | 7.1 MB | retimes of all clips | (latest retime) | **keep** (README only lists 4 clips, see pitfall in 5) |
| `r15_face_bangs` | - | in progress (face agent) | | **do not touch** |

Saves ~9.7 MB tracked. New `00_REVIEW/README.md` = one index table: topic -> latest round -> status -> "open first"
file, plus one line: "older rounds were removed from the tree; `git checkout pre-cleanup -- 00_REVIEW/<round>`".

### 1.3 data/

**Variants** (52 files). The `extends` chains of what is still needed:
- `S4_hd` -> `S4_halfup_bow` -> `S0_semichibi_base` (hero, current)
- `S4_halfup_bow` -> `S0_semichibi_base` (legacy, rebuilds `releases/S4_actions_v1` for rollback)

Keep those 3. Delete the other **49**: A_chibi, B_pokemon_ow, BO1-6, C_semichibi, C1-C6, D_trainer, E_puffball,
F_test, H1_B_final, H1v2_B_final, H2_A_final, H2v2_A_final, O1-6, OL_colored/dark/none/open/selout, R1-4,
S1_waist_beret, S2_long_twintails(_hires), S3_high_pony, S5_side_braid, S6_hood_down_long, T_cute, T_cute_reg,
T_hair, T_lineart, T_scarf. None is in a kept chain, and no pipeline code names any of them (only docstring examples
in `board.py`, `chargen.py`, `override.py`, `pixelreview.py`, `publish.py`, which get updated to S4_hd).

**Animations.** Keep every base clip and every `*_r14` clip (promotion pending). Delete:
- `jump.json` (12-frame H0/H1 jump, used only by H1/H2/A/B/O/R/BO variants and the classic mode), `jump_v2.json` (C*/T* only).
- `poses_concept.json` (only `pipeline/portrait.py`).
- Keep `jump.json` instead if the classic no-variant mode is kept (phase C decides).

**Palettes.** S4 uses `cw_oatmeal` (paletteId `frost_r3_oatmeal`). Delete `cw_oatmeal_portrait` (portrait only) and the
5 colourways only old variants use (`cw_charcoal`, `cw_cranberry`, `cw_forest`, `cw_lavender`, `cw_navy`), plus
their generator `pipeline/tools/make_r3_palettes.py` (one-shot r3 tool; it also rewrites `cw_oatmeal`, so it is
unsafe to rerun anyway). Note: the face agent's area is `data/faces`, not palettes.
`data/palette.json` + `data/character.json`: the classic, pre-variant H0 inputs. They are still referenced by
`build.py:variant_inputs(None)` and as `server.py`'s palette fallback, so they are removed only in phase C, with code.

**Faces.** `kawaii_v2` (legacy S4) and `kawaii_hd` (new, face agent) are in use. `hd_v1` is used only by `face_hd.py`/`portrait.py`;
`kawaii_v1` is not used anywhere. Both can go, **but `data/faces/*` belongs to the face agent: delete them only
after it has finished, and tell it first.**

**Illustrations.** `data/illustrations/S4/` (0.5 MB, rejected r12 vector illustrations) holds JSON specs **plus
Python scripts** (`poses/_build.py`, `_compose.py`, `_cels.py`, `_orphans.py`, `poses_def.py`, `_all.sh`). Its only
consumer is `pipeline/illustrate.py`. **Delete the whole directory.**

**Props.** `crate`, `smear`, `snowball`: all in use. Keep.

### 1.4 overrides/

- `variants/S4_hd/` (4 files): keep, and leave alone (the face agent is editing them).
- `variants/H1_B_final/` (90 files), `variants/H1v2_B_final/` (28): delete together with their variants.
- `jump/S/`: an empty, untracked dir. `rmdir`.

### 1.5 releases/

Keep `S4_actions_v1`, `S4_hd_actions_v1`. Delete `H1_v1`, `H1_v2_1`, `H1_v2_3`, `H1_v2_4` (10.6 MB, old B-body
hero) and the `HERO -> H1_v2_4` symlink. Add `releases/README.md`: two rows, hero vs rollback, plus how each was
built (`S4_hd_actions_v1/BUILD.json` git_base `23747fc`; `S4_actions_v1` at `4883be7`).
Tag the release source commits so they can still be rebuilt exactly after the r14 promotion:
`git tag S4_actions_v1 4883be7`, `git tag S4_hd_actions_v1 85853e2`.

### 1.6 pipeline/

Import graph (static `from .x import` plus lazy imports inside functions) and CLI entry points:

| Module | Used by | Verdict |
|---|---|---|
| build, frames, rig, render, sdf, chargen, face, pixelrules, fx, palette, mathutil, export, qa, reference, meshexport | build chain (`meshexport` lazy in build for HD; `sdf` lazy in frames/qa/meshexport) | keep |
| publish | CLI: 00_REVIEW rounds | keep |
| board | CLI: comparison boards (r12 boards) | keep |
| pixelreview | CLI + `override.py --preview` | keep |
| override | CLI: reasoned overrides | keep |
| server + `editor/` | CLI: editor | keep |
| pixgrid | CLI + `pipeline/tools/r13_bust/*`: hand-pixel art (r13, current) | keep |
| **illustrate.py** (597 lines) | only `data/illustrations/S4/poses/*` scripts (r12, rejected) | **delete** |
| **portrait.py** (146) | nothing; CLI that made r10_concept_art | **delete** |
| **face_hd.py** (122) | only `portrait.py`, through the `render.face_hd` branch in `frames.py:302-305`; no variant sets `face_hd` | **delete**, and drop that 4-line branch in `frames.py` |
| tools/make_s4_hd.py | authors `S4_hd.json` (current) | keep (face agent is editing) |
| tools/gemini_critique.sh | external critique (current) | keep; update its output path when docs move |
| tools/r13_bust/*.py (8 small scripts) | regenerate/inspect the r13 bust `.pix` (import `pipeline.tools.r13_bust.pixlib`, hardcode `00_REVIEW/r13_anime_pixel/bust`) | keep. Optional: rename to `tools/hand_bust/` (requires fixing 2 imports) |
| **tools/make_r3_palettes.py** | one-shot r3 palette generator | **delete** (with the colourways) |
| `__pycache__/*.pyc`, `tools/**/__pycache__` | tracked by mistake (16 files) | `git rm --cached` (already in .gitignore) |

Dead functions (AST scan of every top-level def against all non-dead modules): only `mathutil.lerp` (unused) and
`make_s4_hd.back_z` (unused; face-agent file, so leave it). Everything else is referenced.

**Phase C (optional, code simplification, separate commit, must pass the byte-identity gate):**
- `chargen.py` outfit branches that no kept variant reaches: coat `parka`/`puffer`, hair `braids`/`twintails`/`side_pony`/`pony`/`buns`/`bob`,
  hat `beanie`/`beanie_slouch`/`cat_beanie`/`earmuffs`/`hood`, accessory `clip`, bangs `points`, boots `snow`, scarf `chunky`. The kept
  chain uses hair `long`, hat `none`/`beret` (S0), bangs `straight`/`side`, accessory `ribbon_back`/`ribbon_side`, coat `aline`, legs
  `skirt_tights`, boots `tall`, scarf `long`. Removing the rest is about 100-150 lines, but it closes off cheap design exploration.
  **Recommendation: keep them.** They are data-driven and cheap, and the memory notes say "parts-library direction".
- Outline modes `open`/`colored`/`none` in `frames.py`/`render.py`: only the OL_* r10 study used them. Small; keep or drop.
- The classic no-variant mode (`--anim jump` without `--variant`, `out/jump`, `overrides/jump`, `data/character.json`,
  `data/palette.json`): make `--variant` required in `build.py`/`override.py`/`server.py`, then delete the 2 data
  files and `jump.json`. Touches build.py; do it after the face agent has merged.

### 1.7 docs/

112 review docs in `docs/review/` (r0-r14, `pixel/`, `gemini/`), plus `kickoff/` (5), `research/` (3),
`DECISIONS.md`, `SCHEMA_v2.md`. Keep all of them as history, but move them by round:

```
docs/history/r00_kickoff/        <- docs/kickoff/*  + docs/review/r0/*.png
docs/history/r01/ ... r14/       <- docs/review/rN_*.md (r3_palette_board.png -> r03/)
docs/history/r06_pixel/          <- docs/review/pixel/*  (H1 per-direction pixel reviews + AD sign-off)
docs/history/gemini/             <- docs/review/gemini/*  (gemini_critique.sh writes here after the path change)
```
Use two-digit round folders (`r01`..`r15`) so they sort. File names stay unchanged inside, so `grep` still finds them.

New docs (phase B):
- `docs/ARCHITECTURE.md`: data flow (variant spec -> chargen -> rig/sim -> render (ellipsoid legacy | SDF HD) -> pixel
  rules -> face cels/eyes -> outline -> overrides -> export/QA -> builds/ -> out/ -> publish/release), the module map
  (table 1.6), file formats (variant `extends`/`anim_patch`/`prim_overrides`, animation channels, `derived` clips,
  `hold_of`, override JSON, `.pix`), and the hashing/determinism model.
- `docs/HOWTO.md`: exact commands for setup, building one clip or all 13, `--verify`, `--no-reference`, publish a
  round, cut a release (BUILD.json; commit first), overrides (CLI + editor), pixgrid render/sheet/stats, boards,
  the gemini critique, and the r14 promotion procedure.
- `docs/LEARNINGS.md`: seed list in section 5.
- `docs/DECISIONS.md`: keep, and add a "current spec (S4_hd)" table at the top. Rows from older eras stay, marked superseded.
- `docs/SCHEMA_v2.md`: keep, or fold into ARCHITECTURE.
- `docs/CLEANUP_PLAN.md` (this file): delete after execution, or move it to `docs/history/r15/`.

## 2. Target tree

```
README.md                 short: what this is, current hero, where to look, 5 commands (links to docs/)
00_REVIEW/                README.md index + latest per topic: r12_hd_model, r13_anime_pixel, r14_retime, r15_face_bangs
releases/                 README.md, S4_hd_actions_v1/ (hero), S4_actions_v1/ (rollback)
art/hand/S4/              hand-typed .pix sources (illustrations)
data/
  variants/               S0_semichibi_base, S4_halfup_bow, S4_hd
  animations/             13 base clips + *_r14 (until promotion) [+ jump.json until phase C]
  palettes/               cw_oatmeal
  faces/                  kawaii_v2, kawaii_hd
  props/                  crate, smear, snowball
  character.json, palette.json   (only until phase C)
overrides/variants/S4_hd/
pipeline/                 core modules + publish/board/pixelreview/override/server/pixgrid
  tools/                  make_s4_hd.py, gemini_critique.sh, r13_bust/
editor/
docs/
  ARCHITECTURE.md  HOWTO.md  LEARNINGS.md  DECISIONS.md  SCHEMA_v2.md
  research/               japanese_dote_style, outline_techniques, pokemon_style
  history/                r00_kickoff ... r15, r06_pixel, gemini
(gitignored, local only: builds/, out/, .venv/)
```
11 top-level entries become 9 (8 dirs + README). `overrides/` was deliberately not moved under `data/`: that would
change paths in build/server/override, the release READMEs and the face agent's files, for little gain.

## 3. Sizes saved

| What | Tracked (repo checkout) | Local disk |
|---|---|---|
| `out/` untracked + removed | 70.1 MB | 171 MB |
| `builds/` removed (already untracked) | - | 2.1 GB |
| `releases/H1_*` | 10.6 MB | 11.5 MB |
| 00_REVIEW r10_* x4, r11_actions, r12_illustration, r13_sprite_face | 9.7 MB | 9.9 MB |
| data (49 variants, 3 anims, 6 palettes, illustrations, 2 faces) | ~0.6 MB | |
| overrides H1* | 0.2 MB | |
| pipeline dead modules + pycache | ~0.1 MB (865 lines of code) | |
| **Total** | **~91 MB of 125 MB (73%)** | **~2.3 GB** |

`.git` stays at 424 MB, since history is kept on purpose. A history rewrite (filter-repo) is not recommended: GitHub
review links and the release commit refs depend on that history.

## 4. Steps (exact commands)

Run from a dedicated worktree so the face agent's dirty tree is never touched:

```bash
cd /Users/waylonhuang/Documents/other/pixelart
git tag pre-cleanup HEAD && git tag S4_actions_v1 4883be7 && git tag S4_hd_actions_v1 85853e2
git worktree add ../pixelart-cleanup -b cleanup HEAD
cd ../pixelart-cleanup
PY=/Users/waylonhuang/Documents/other/pixelart/.venv/bin/python   # use -B everywhere (no .pyc writes)
```

**Step 0: baseline** (before any change; see section 7 for the script):
```bash
for c in idle walk run jump_sc fall land climb climb_top pick_up carry_idle carry_walk throw carry_throw; do
  $PY -B -m pipeline.build --variant S4_hd --anim $c --no-reference; done
for c in idle walk run jump_sc throw carry_walk; do $PY -B -m pipeline.build --variant S4_halfup_bow --anim $c --no-reference; done
for c in jump_sc_r14 land_r14 run_r14 idle_r14; do $PY -B -m pipeline.build --variant S4_hd --anim $c --no-reference; done
$PY -B -m pipeline.build --variant S4_hd --anim jump_sc            # full: reference + meshexport
mkdir -p /tmp/pa_base && cp -R out/variants /tmp/pa_base/
```

**Step 1: untrack generated files** (commit: "Untrack generated out/ and __pycache__"):
```bash
git rm -r -q --cached out pipeline/__pycache__ pipeline/tools/__pycache__ 2>/dev/null || true
git rm -r -q --cached pipeline/tools/r13_bust/__pycache__ 2>/dev/null || true
# .gitignore: replace the out/* + !out/boards/ + out/.DS_Store lines with a single `out/`
```

**Step 2: delete superseded review rounds and releases** (commit: "Remove superseded review rounds and H1 releases"):
```bash
git rm -r -q 00_REVIEW/r10_concept_art 00_REVIEW/r10_S4_jump 00_REVIEW/r10_semichibi_candidates \
  00_REVIEW/r10_outline_study 00_REVIEW/r11_actions 00_REVIEW/r12_illustration
git rm -r -q releases/H1_v1 releases/H1_v2_1 releases/H1_v2_3 releases/H1_v2_4 releases/HERO
# later, after r15_face_bangs is published:  git rm -r -q 00_REVIEW/r13_sprite_face
```

**Step 3: delete dead data and code** (commit: "Remove rejected illustration pipeline and unused variants"):
```bash
git rm -q pipeline/illustrate.py pipeline/portrait.py pipeline/face_hd.py pipeline/tools/make_r3_palettes.py
git rm -r -q data/illustrations
# frames.py: delete the `if rnd.get("face_hd"): ...` branch (lines 302-305); change the following `elif` to `if`
# mathutil.py: delete lerp()
cd data/variants && git rm -q A_chibi.json B_pokemon_ow.json BO?_*.json C_semichibi.json C?_*.json D_trainer.json \
  E_puffball.json F_test.json H1_B_final.json H1v2_B_final.json H2_A_final.json H2v2_A_final.json O?_*.json OL_*.json \
  R?_*.json S1_*.json S2_*.json S3_*.json S5_*.json S6_*.json T_*.json && cd ../..
git ls-files data/variants      # expect exactly S0_semichibi_base, S4_halfup_bow, S4_hd
git rm -q data/animations/jump_v2.json data/animations/poses_concept.json     # jump.json: phase C
git rm -q data/palettes/cw_{charcoal,cranberry,forest,lavender,navy,oatmeal_portrait}.json
git rm -r -q overrides/variants/H1_B_final overrides/variants/H1v2_B_final
# AFTER the face agent is done (its area):  git rm -q data/faces/hd_v1.json data/faces/kawaii_v1.json
# update docstring examples in board/chargen/override/pixelreview/publish to S4_hd
```

**Step 4: move docs** (commit: "docs: move review history into docs/history/<round>"):
```bash
mkdir -p docs/history
git mv docs/kickoff docs/history/r00_kickoff && git mv docs/review/r0/*.png docs/history/r00_kickoff/
for n in 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do d=$(printf r%02d $n); mkdir -p docs/history/$d
  for f in docs/review/r${n}_*; do [ -e "$f" ] && git mv "$f" docs/history/$d/; done; done
git mv docs/review/pixel docs/history/r06_pixel && git mv docs/review/gemini docs/history/gemini
# rewrite links in all tracked .md files (00_REVIEW, releases, docs):
#   docs/review/pixel/ -> docs/history/r06_pixel/ ; docs/review/gemini/ -> docs/history/gemini/ ;
#   docs/review/rN_x.md -> docs/history/rNN/rN_x.md   (small python script using re.sub, then review git diff)
# pipeline/tools/gemini_critique.sh: out="docs/history/gemini/$name.md"
# make_s4_hd.py comments mention docs/review/...: leave (face-agent file), fix later
```
Any `docs/review/r15_*` the face agent adds gets moved after it merges.

**Step 5: new docs + index** (commit: "docs: README, ARCHITECTURE, HOWTO, LEARNINGS; 00_REVIEW + releases index"):
rewrite `README.md`, `git rm START_HERE.md`, write `00_REVIEW/README.md` (index), `releases/README.md`,
`docs/{ARCHITECTURE,HOWTO,LEARNINGS}.md`, and add the current-spec table to DECISIONS.md.

**Step 6: verify (section 7), then merge.** Once the face agent has committed: `git rebase main` in the worktree
(or merge). The only expected conflict is `00_REVIEW/README.md`. Re-run section 7, `git push`, `git push --tags`.
Then clean up locally in the main checkout: `rm -rf builds out overrides/jump`, `git worktree remove ../pixelart-cleanup`.

**Phase C (optional, separate PR-sized commit):** the classic mode removal and the chargen pruning from 1.6, each gated by section 7.

## 5. LEARNINGS.md seed (what we learned; to be written up in phase B)

Pipeline
- One 3D model + one sim + a screen-fixed light gives 8 consistent facings. Never mirror; the 3/4 face cels are the one sanctioned mirror.
- Determinism: fixed 5 ms sim step, 10 ms-multiple durations, no RNG, `--verify` double render. The build id hashes all
  inputs, so an unrelated edit (any variant, any pipeline file) changes every hash: compare pixels, not hashes.
- Legacy (ellipsoid) and HD (SDF) models share rig, sim, pixel rules and export. HD adds a `temporal_hold` and per-eye `face_eyes`.
- Derived clips (`land_r14` <- `jump_sc_r14`) hash their source clip too.
- Prop layers are separate front/back strips, split by body depth. HD bodies must ship with HD prop strips (never mix sets).
- Recurring hand fixes get encoded as pixel rules (`pixelrules.py`). Hand pixels fell 570 -> 98 on H1.
  Overrides need a reason and go stale when the base changes.

Pixel-art rules (from AD reviews): closed outer outline, sel-out on a dark outline with a contrast floor on snow,
no orphan pixels (QA = 0), 2-3 tones per material, readable silhouette in greyscale, 1-px tapered tips survive only if
the silhouette pass does not trim them (ponytail rounds 4-6), consistent eye spacing in 3/4 views (2-px nose bridge).

Review process: AD + animation director + GD each review; the lead consolidates; a round is a numbered folder in
00_REVIEW with a README "open first" table. Approvals are written into the round README and the release README.

Agent workflow: one owner per file set (parallel agents must not edit the same files), publish only from built
outputs, commit before cutting a release.

Pitfalls found during this inventory
- `out/` was committed before it was gitignored (70 MB), and `pipeline/__pycache__` is tracked despite the `.gitignore`.
- `publish.py` **overwrites** `<round>/README.md` with only the clips in the latest call (the r14_retime README lists 4
  of the 13 retimed clips). Fix: merge rows into the existing README, or pass all clips.
- `releases/S4_hd_actions_v1/BUILD.json` says it was "built from the working tree" (uncommitted overrides). Commit first.
- `server.py:_out()` maps a variant to `out/variants/<variant>` regardless of the clip, but build writes
  `out/variants/<variant>__<clip>` for non-jump clips, so the editor only opens variant **jump**. Fix when phase C touches server.py.
- `server.py` falls back to `data/palette.json` (classic palette) for palette display.
- `data/illustrations` kept Python build scripts inside `data/`. Code belongs in `pipeline/tools/`.
- r13_bust tools hardcode `00_REVIEW/...` output paths and must be run from the repo root.

## 6. Coordination with the face/bangs agent

- Work on branch `cleanup` in `../pixelart-cleanup` (a worktree from HEAD). None of the steps touch `pipeline/sdf.py`,
  `pipeline/face.py`, `pipeline/tools/make_s4_hd.py`, `data/variants/S4_hd.json`, `data/faces/*`, `overrides/variants/S4_hd/*`
  or `00_REVIEW/r15_face_bangs`.
- `frames.py` (the face_hd branch) is the only shared-pipeline edit. If the face agent is also editing `frames.py`,
  postpone that 4-line change.
- Deferred until the face agent finishes: deleting `data/faces/{hd_v1,kawaii_v1}.json` and `00_REVIEW/r13_sprite_face`,
  moving its r15 docs, and the dead `back_z` in make_s4_hd.py.
- Do not run builds in the main checkout while the face agent is building. Both write `builds/` and `out/variants/`.

## 7. Verification plan

1. **Byte-identical sprites.** After steps 1-5 (in the worktree), rebuild exactly the step-0 list, then:
   ```bash
   for d in /tmp/pa_base/variants/*/; do n=$(basename $d)
     for f in $(cd $d && find . -name '*.png' -o -name '*.gif'); do cmp -s "$d/$f" "out/variants/$n/$f" || echo "DIFF $n/$f"; done; done
   ```
   For JSON (`*_sheet.json`, `qa_report.json`, `guide/guide.json`), compare after stripping the `buildHash`/`hashes`/`buildId`
   fields with a 10-line python script. Expected result: no DIFF lines. A `manifest.json` difference that is only
   input hashes and removed file names is expected.
2. **Release parity.** `cmp` the rebuilt `S4_hd__<clip>/<clip>_sheet.png` against `releases/S4_hd_actions_v1/<clip>/<clip>_sheet.png`
   for all 13 clips (body sheets must match; this also proves HEAD reproduces the approved release). For
   `S4_halfup_bow`, the body sheets match `releases/S4_actions_v1` except the documented SE/SW/NE/NW face change from
   r13 and the crate prop strips (see that release's post-release note). Compare against the step-0 baseline, not the release.
3. **QA + determinism.** `--verify` on S4_hd jump_sc and run must print IDENTICAL and QA PASS.
   The full (non `--no-reference`) jump_sc build must still write `reference/model_meshes.json` and the STLs.
4. **pixgrid.** `$PY -B -m pipeline.pixgrid render art/hand/S4/bust/*.pix --out /tmp/pa_pix` and `stats` succeed. Running
   `$PY -B pipeline/tools/r13_bust/export_sheet.py` from the repo root regenerates `00_REVIEW/r13_anime_pixel/bust/bust_spritesheet.png`
   with `git status` clean (byte-identical).
5. **publish.** `$PY -B -m pipeline.publish --variant S4_hd --round _tmp_check --clips idle run` writes
   `00_REVIEW/_tmp_check/` with GIFs, sheet and README. Then `rm -rf 00_REVIEW/_tmp_check`.
6. **Other CLIs import cleanly:** `$PY -B -c "import pipeline.board, pipeline.pixelreview, pipeline.override, pipeline.server, pipeline.meshexport"`.
   Also `grep -rn "illustrate\|portrait\|face_hd" pipeline` returns nothing.
7. **Links.** A short script that checks every relative markdown link in tracked `.md` files resolves to an existing path
   (catches docs/history moves and deleted rounds).
8. **GitHub check.** After the push, open `00_REVIEW/README.md` on GitHub and confirm every "open first" link renders.
