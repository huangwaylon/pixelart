# Study: the `pixelart` (Snowpeak) project, and what it means for Akane

Source: `/Users/waylonhuang/Documents/other/pixelart` (studied read-only at HEAD `2000561`, 2026-10-24; 124 commits on `main`, no tags).
Everything here comes from git log/show, the repo's docs, review files, code and published boards. Nothing in that repo was built, run or modified.
Images copied for reference are in `docs/img/pixelart_study/`.

Path conventions: `PA/` = `/Users/waylonhuang/Documents/other/pixelart/`. Paths without a prefix are in our project (`/Users/waylonhuang/Documents/other/pixelart/swordswoman/`).

---

## 0. Executive summary

- **Goal.** 8-direction isometric pixel sprites for a mobile snow game: a chibi winter girl, reproducible byte for byte, consistent across facings.
- **Pipeline.** A procedural 3D mannequin (ellipsoids, later SDF) is raycast in numpy into palette indices. A long, ordered 2D pixel pass follows: bands → despeckle → rules → outline/sel-out → face cels → protected cleanup. Reasoned, hash-bound hand overrides sit on top.
- **Characters.**
  - H1, a Pokémon-overworld body at 48x48, was signed off and released.
  - The user then asked for cuter, more Japanese and semi-chibi. That gave S0-S6, and **S4 "half-up bow"** won.
  - S4 got a full 13-clip action set (`S4_actions_v1`) and then an HD SDF model (`S4_hd`). **`releases/S4_hd_actions_v1` is still the approved hero.**
- **Rejected along the way, all by the user:**
  - HD "concept art" portraits rendered from the 3D model (r10).
  - Vector-to-pixel illustrations (r12): *"the illustrations look terrible"*.
  - A Gemini-generated mesh (r17): "hideous".
- **What worked.** Hand-typed pixel grids (r13) were approved for busts, turnaround and poses.
- **The Blender detour (r18-r20).**
  - Blender models from independent agents (r18) were baked into sprites in r19. They were cleaner, but **worse at 48x64**: a 6.5-head figure leaves no room for a face.
  - r20 tried Claude vs Gemini Blender base models. Neither became canon.
  - So r21 went back to refining the SDF model (S4_hd2, round 7, not yet approved).
- **The biggest transferable lesson:**
  1. Review every pixel and log each fix with a reason.
  2. Move every recurring fix into a deterministic post-pass rule.
  3. Keep only a small, hash-bound override layer.

  On H1 this took hand pixels **570 → 254 → 170 → 100 → 98**. The S4_hd release needed only **28 px in 4 files** (24 px in 3 files in the current tree).
- **The most relevant lesson for us:**
  - A sprite model must be **built at sprite proportions**. You cannot retarget it after the fact (r19).
  - The pixel pass must **supersample and majority-vote** from a multi-pass bake. Point-sampling at 1x is not enough.
  - Faces at this size are **stamped cels**, not rendered geometry.

---

## 1. Timeline

### 1.1 Git shape

- 124 commits on `main` / `origin/main`, from 2026-10-22 to 2026-10-24. There are no tags.
- `docs/CLEANUP_PLAN.md` §1.5 *proposed* tags `S4_actions_v1 4883be7` and `S4_hd_actions_v1 85853e2`, but they were never created.
- Rounds r0-r8 all arrive in one bulk commit, `aa2d9fc` ("Snowpeak sprite pipeline: 3D-reference generator, line-art passes, variants, editor, reviews"), on top of `6e37ddd` (first commit). From r9 (`7c2d918`) on, each round has its own commits.
- **The cleanup plan was never executed.** `PA/docs/CLEANUP_PLAN.md` (written at `5051432`) still says "Status: PLAN". All old rounds, `releases/H1_*` and the dead modules are still present. The `docs/LEARNINGS.md` it seeds was never written; its §5 "LEARNINGS seed" is the closest thing.

### 1.2 Round by round

| Round | What | Outcome / user verdict | Key refs |
|---|---|---|---|
| Kickoff | Brief: chibi girl, jump animation, 2:1 iso, 8 dirs, "quality and cross-angle consistency are the top priorities", reproducible and iterable. Role memos from AD, GD, 3D artist and SE. | v1 locked decisions table | `PA/docs/kickoff/*.md`, `PA/docs/DECISIONS.md` |
| r0 | Camera elevation test, 18° vs 26.565° | Images only | `PA/docs/review/r0/elev_*.png` |
| r1 | First jump build | GD: **"FAIL"** (foot slide 0.4 px, 1010 orphans, "hat brim hides the eyes" at 26°). AD: "a cream cupcake on a red sack". 3D: the launch is a "stiff I", the fall "reads as a T-pose". → **Character camera 26.565° → 18°**, 770 ms timing, low chain damping, despeckle. | `PA/docs/review/r1_*.md` |
| r2 | Polish | GD timing PASS. Greyscale gate added: hat luma 234 ≈ snow 232, so hat luma must be ≤205. | `r2_*.md` |
| r3 | **Architecture pivot.** "The model is good at *where* things are … bad at *what they look like* at 40 px … it's a mannequin." The 3D model is demoted to a maintained reference. Adds `guide.json` and the grounding sheet. Palette: one 32-colour master plus 6 colourways. Pokémon research. **Camera 16°**. | | `r3_3d_grounding_proposal.md`, `r3_art_director_palette.md`, `PA/docs/research/pokemon_style.md` |
| r4-r5 | Proportion candidates A-E, outfits O1-O6, resolutions R1-R4 | R2 (48x48, ~29-36 px) chosen on memory and cleanup-hours grounds (~8 h vs 14 h per animation). **H1 = B body + O1 charcoal; H2 = A body (alternate).** The AD and GD split on the body: "This is your call" (`START_HERE.md`). | `r4_*.md`, `r5_panel_*.md`, `out/boards/1-4_*` |
| H1 pixel review | 4 pixel artists, 96 frames, every override with a reason → AD cross-check → **8 locked style rules** → 4 generator rounds | **570 → 98 hand px**. v2.3 was "NOT SIGNED: one ship blocker": the sole rule recoloured mittens as boots. v2.4 SIGNED. | `PA/docs/review/pixel/H1_*.md`, `H1_AD_signoff.md`, `H1_v2_vs_v1.md` |
| r6 | GD acceptance | "ACCEPT WITH NOTES": engine sim 16/16, but 26 of 44 overrides were stale. `--release` now fails on stale overrides. Release `releases/H1_v2_4` = `releases/HERO`. | `r6_game_director_acceptance.md` |
| r7 | jump_v2, "cuter, more expressive" | Head tilt counters the spine; net head yaw is ~0 in the air; a two-beat landing | `r7_animation_jump_v2.md` |
| r8 | **User:** "more Japanese-esque (ドット絵) … CUTER and more FEMININE … must READ WELL FROM A DISTANCE". Research verdict on the signed H1: "red hat with legs". 6 candidates C1-C6. | Panels shortlisted C1/C3/C4/C2 | `r8_*.md`, `PA/docs/research/japanese_dote_style.md` |
| r9 | **User:** semi-chibi, curvier, long hair, likes O6's teal, "design consistency across the 8 angles", "nothing may penetrate the body". New base S0 (~3.4 heads, 48x64, pivot 24,57) and candidates S1-S6. | `chain_penetrations = 0` QA gate | `r9_*.md`, `7c2d918` |
| r10 | **S4_halfup_bow is the user's favourite.** Hair stylists (clump lines + one angel ring), face designer (kawaii_v2 cels), **outline study** (5 styles, GD melt measurements) | Decisions: sel-out on a dark outline, closed exterior, ink eyes, outline on its own palette index. **HD concept portraits rendered from the model: rejected by the user** ("should be reimagined … like actual anime pixel art"). | `r10_*.md`, `00_REVIEW/r10_*`, `a939e36`, `e4fa1c0` |
| r11 | S4 action set: 13 clips, 4 work packages, 3 + 1 review rounds | **`S4_actions_v1` APPROVED** by AD, Animation Director and GD (`4883be7`) | `r11_*.md`, `PA/releases/S4_actions_v1` |
| r12 track 1 | Vector illustration → pixel (`pipeline/illustrate.py`): busts, model sheet, poses | AD approved parts in review 2. Then **the user rejected the whole approach** (`1b1cd5d` "superseded: user rejected vector->pixel approach") | `r12_illustration_plan.md`, `00_REVIEW/r12_illustration` |
| r12 track 2 | **S4_hd**: SDF sphere-traced model (sharp hair tips, open bow loops, soles). 6 AD rounds; the main fight was the ponytail's 1-px tapered tip. User asks mid-round: anime head and chin, modelled eyes, bouncy bow, walk hair sway (`ace889b`). | **`S4_hd_actions_v1` APPROVED** (`85853e2`). AD warning on record: "If HD still only equals legacy at 48x64, tell the user plainly". | `r12_hd_*.md`, `PA/releases/S4_hd_actions_v1/README.md` |
| r13 | **Restart after the rejection.** User: *"the illustrations look terrible, i want you to create them not based on the 3d model but generate anime pixel art based on the description of the character and then define it with a team"*. Design bible (Koyuki), AD style guide, 3 face tests (C won), hand-typed `.pix` grids. | Turnaround approved after 6 reviews (`76babb1`), busts after 5 (`bffda53`; blind expression tests 10/10), 8 poses after 4 (`23747fc`). Gemini critique tool introduced (`5051432`). | `r13_*.md`, `PA/art/hand/S4/**`, `00_REVIEW/r13_anime_pixel` |
| r14 | GD timing budgets ("build-up after the commit point, or in skippable holds"); animator retimes; engine features (hold_of, skippable, smear, per-key ease, budgets) | `_r14` clips pass QA. Not promoted into the release. | `r14_*.md`, `668b282`, `41b0ef8`, `540069d` |
| r15 | **User:** "SE far eye still looked weird and too close", "bangs should be longer … so she doesn't look bald" | 5 mockups, AD picked B (2x3 far eye). `hem_pin` rule after the anim director measured the bang gap flipping 1/0/1/0. Approved, AD review 4 (`ef51014`). `meshrender.py` + mesh compare (`f9ff5d9`). | `r15_*.md`, `00_REVIEW/r15_face_bangs` |
| r16 | **User:** "face looks a bit too fat … more pointy, curved face … bangs more voluminous and come off the forehead" | `s_fringe` (3 clumps + V-notches), `jaw_taper`, `profile_brow`. "S fringe dots" APPROVED (`5813af8`). Gemini auth root cause found (`0a17554`). | `r16_*.md`, `09d6260`, `bbb69a8` |
| r17 | **User:** have Gemini Argon build "a better, more pretty, detailed, base model from scratch". User reference images; proportion 5.0 heads. | Gemini mesh v2 called **"hideous"** by the user. Gemini mesh tracks stopped (`5d48162`). | `r17_gemini_model_brief.md`, `PA/docs/review/gemini/r17_*` |
| r18 | Two independent Blender modelers (bpy only, forbidden from reading the repo) | AD: "B as the base" + A's bow, back hair and scarf. B round 2 rigged (39 bones), LODs. AD review 2: FIXES (nose-to-chin "one straight diagonal"). | `r18_independent_model_brief.md`, `PA/blender/A`, `PA/blender/B`, `2d390f9`, `09f59b8` |
| r19 | **Blender model B baked into sprites** through the unchanged S4_hd pixel pass | **"No improvement for 48x64; keep S4_hd."** Gemini agrees. Tooling kept. | `00_REVIEW/r19_blender_sprites/README.md`, `metrics.json`, `2933f56` |
| r20 | **User:** "use the gemini model argon and also claude opus 5.5, start from scratch … do not give any 3d models to the LLMs … use blender". Track C (Claude, 23 rounds) and Track G (Gemini, stopped at r2). | AD on C at round 9: "not traceable as canon yet" (helmet hair, V-shield jaw, tube coat, stick legs). **Direction changed to refining S4_hd** (`6c27007`, rationale not written down). | `r20_brief.md`, `r20_AD_C_review1.md`, `PA/work/r20/` |
| r21 | **S4_hd2**: same rig, animations and pixel pass; geometry rebuilt from swept sheets and smooth unions, using base-mesh references | Round 7: idle/walk/run QA PASS, S4_hd byte-identical. Open issues: the S-view bow is only 1-2 px past the head, the fringe roots read as planted, sheet-edge noise. **Not approved, not released.** | `00_REVIEW/r21_s4_hd2/latest/README.md`, `critique.md`, `640b41e`, `2000561` |

### 1.3 Current state

- **Approved hero:** `PA/releases/S4_hd_actions_v1`.
  - 13 clips, 48x64, pivot (24,57), ≤16 colours per frame, all QA PASS.
  - 4 override files / 28 px: one 4-px temple-skin fix (carry_idle NW f0) and three ponytail-tip restores. The current tree has 3 files / 24 px.
  - Built from a dirty tree on `23747fc`, a pitfall `CLEANUP_PLAN.md` itself flags.
- **Rollback:** `PA/releases/S4_actions_v1`.
- **Legacy:** `PA/releases/HERO` → `H1_v2_4` (the jump-only H1).
- **Approved but not in a release:** r13 hand-pixel busts, turnaround and poses; r15/r16 face rules (they live in the S4_hd variant); `_r14` retimes.
- **In progress:** S4_hd2 (r21 round 7). The Blender bake tooling is retained but unused.

---

## 2. Pipeline architecture

### 2.1 Data flow

```
data/variants/<v>.json --chargen.build--> character (bones, primitives/parts, chains, colliders, face)
data/animations/<clip>.json --rig (FK/IK, fixed-5ms verlet chains)--> posed frames
data/palettes/cw_*.json --palette--> colours, ramps, material_bands, line_colors
   → frames.Scene.render_base(frame, dir): yaw the character (camera never moves), raycast (render.py | sdf.py | any tracer)
   → majority vote → bands → inner lines → despeckle → pixelrules → outline/sel-out → face cels → protected despeckle → restores
   → build.render_all: apply overrides (base_hash → stale) → temporal hold
   → build.write_build: sheet PNG+JSON, shadow/fx/prop strips, GIFs, QA, manifest → builds/<tag>_<hash12>/ → out/
```
Entry point: `PA/pipeline/build.py:main`. Editor: `PA/pipeline/server.py` + `PA/editor/`.

### 2.2 SDF/ellipsoid raycaster (their main route)

- **Camera** (`PA/pipeline/render.py:7-28`):
  - Orthographic; `ppu` is pixels per world unit.
  - **Screen-fixed key light** `-0.55·right + 0.68·up + 0.48·to_cam`, so every facing shades the same.
  - Directions are yaws applied to the character (`DIRECTION_YAW`). The jump height is removed and exported as `z_px`.
- **Geometry:**
  - Legacy: ellipsoids on bones (`rig.body_primitives`).
  - HD: `PA/pipeline/sdf.py`, a sphere tracer (48 steps). It has shapes (capsule, rcone, sweep sheets, chain ribbons…), smooth-min blend sets, clip planes and "vote" keys, so a whole material/group votes as one part.
  - Both satisfy a **tracer protocol** (`raycast`, `occluded`). `meshrender.MeshTracer` and the Blender fake tracer plug into the same slot.
- **`render_pixels`** (`render.py:114-224`):
  1. Supersample 3x3.
  2. N·L, cast shadows clamped to ≤ -0.2.
  3. Optional coverage blur.
  4. **Majority coverage → opaque; majority material wins (ties to the centre sample).**
  5. Light averaged over the winning material's samples.
  6. Bands from `material_bands`.
  7. `_clean_orphan_tones`.
  8. Inner lines at group depth breaks > 2.2, drawn in the front part's darkest tone, never on skin; components shorter than 3 dropped.

### 2.3 Blender bake route (r19)

- **`PA/pipeline/blender_bake.py`** (run under `blender -b`):
  - Rebuilds the pipeline camera and light in Blender axes and yaws the rig per direction.
  - Cycles, 1 sample, 0 bounces, filter 0.01, seed 0, EXR.
  - Disables the outline hulls and hides the modelled eyes and face lines.
  - Renders **3 passes at 12x**: ID (role, body part, depth), world normal, and a hard-sun shadow.
  - Maps materials through `ROLE_OF`. Body parts come from the dominant deform bone (`tag_parts`), so inner lines fall at part breaks.
  - Writes `.npz` per frame/dir, plus `meta.json` with eye/mouth/head positions.
- **`PA/pipeline/blender_sprites.py`:**
  - `fake_pixels` builds pseudo-primitives and a tracer that returns the baked hits.
  - It then calls the **real** `render_pixels` (`ss=12`) through `BakeScene(frames.Scene)`, which monkeypatches `frames.render_pixels`. All downstream passes and the face cels run unchanged.
  - A synthetic head matrix is solved so the eye markers land on the Blender eye centroids.
  - No build hash, QA or overrides.
- **Verdict:** see §4.2.

### 2.4 Variants and chargen

- `PA/pipeline/chargen.py` builds an 18-bone humanoid with primitives, chains and colliders from `proportions` / `outfit` / `face`.
- Variants use `"extends"` chains (S4_hd → S4_halfup_bow → S0_semichibi_base), plus `anim_patch`, `ramp_overrides`, `material_bands` and `prim/part_overrides`.
- Big HD variants are *generated* by scripts (`PA/pipeline/tools/make_s4_hd.py`, `make_s4_hd2.py`).
- `render.*` flags switch every optional pass (`v2`, `lineart.*`, `face_eyes.*`, `temporal_hold`, `bow_shine`, `final_orphan_pass`…). This kept old variants byte-identical while new rules were added.

### 2.5 Pixel-pass order (the valuable template)

`PA/pipeline/frames.py:214-380`:
1. Raycast plus head-space hair styling (clump lines, angel ring).
2. `remove_lone_pixels` + material-aware `despeckle` (islands ≤3).
3. `apply_rules`: the pre-outline pixelrules.
4. `separate_materials`: the nearer part takes its line colour where same-colour parts touch.
5. Accessory cels (pom).
6. `regularize_silhouette` (ジャギ取り), protecting deliberate small accessories.
7. `add_outline` → `pixel_perfect_outline` (L-corner removal) → `selout_outline` → `_even_outline_runs`.
8. Post-outline rules (`outline_notches`).
9. **Face cels.**
10. Second despeckle with face and outline colours protected; undo eye growth; restore stamped pixels; restore short sel-out runs.
11. Accessory restores (`grounded_soles` by part mask, `ring_trim`, `skin_edge_dark`, `bow_shine`).
12. `_final_orphans`.

Then overrides are applied, and `temporal_hold` runs for near-static loops.

### 2.6 Face decals

- `PA/pipeline/face.py`:
  - `apply_face`: procedural templates (v1/v2).
  - **`apply_face_cels`**: JSON cel grids per view class (front / three_quarter / profile) and expression. Authored facing screen-right and mirrored for left views; this is the only sanctioned mirror. Cels paint **only onto skin**.
  - **`apply_face_eyes`**: per-eye blocks at projected 3D eye markers, with bridge, contour and row-alignment solving, plus the hem/fringe/jaw helpers.
  - Stamped pixels become `deliberate`, which exempts them from the orphan QA.
- `PA/data/faces/kawaii_hd.json` is the current cel set.
- `PA/pipeline/face_hd.py` + `portrait.py` made the HD analytic anime face for the r10 concept portraits, which the user rejected. CLEANUP_PLAN marks both modules dead.

### 2.7 Hand grids (`.pix`)

- Format (`PA/pipeline/pixgrid.py:3-19`): `size:`, `extends:`, `legend:` (char = hex + role name), `grid:`, repeatable `patch: X Y` with `_` = keep.
- CLI: `render | sheet | stats | fromimg`. `stats` counts colours and orphans.
- Sources live in `PA/art/hand/S4/{bust,turnaround,head_small,poses}`. Expressions are `extends: bust_base.pix` plus patches.
- **No build stage consumes `.pix`.** Hand art reaches game sprites only through the override layer. `.pix` was for dialogue busts, turnaround and cut-scene poses.

### 2.8 Overrides and the editor

- Override JSON per (variant, clip, dir, frame): `{"px": [[x,y,index|-1]], "base_hash", "reasons":[{time,author,pixels,why}], "needs_review"}`.
- **`--reason` is mandatory** (`PA/pipeline/override.py:97`).
- `base_hash` = sha1 of the base index frame. A changed base flags the override **stale**, and `--release` builds fail on stale overrides.
- `--prune` drops override pixels the generator now produces itself and marks the override for review.
- Editor (`PA/editor/editor.js`, `PA/pipeline/server.py`, port 8777): pencil, erase, fill, picker, revert, onion skin, base-only view, undo, feedback notes.
- **Known bug:** `server._out` ignores the clip, so it only works for `jump`.
- Our `tools/pixel/` already ports this design (README says so) and improves it with per-pixel `base_color`, conflict detection, `approve` and a HISTORY log.

### 2.9 QA, determinism, hashes, export

- **QA checks** (`PA/pipeline/qa.py:run_qa`):
  - palette/alpha; bounds margin ≥2;
  - foot slide <0.5 px; treadmill slide; squash range;
  - body-only height spread across directions ≤3;
  - **orphans = 0** (outline, face, deliberate and override pixels exempt);
  - chain penetration = 0; loop seam ≤1 px;
  - jaggy count; colours per frame (warn above 16); palette ≤32;
  - stale overrides; sub-pixel features (HD);
  - `timing_budget` (max lock, event deadlines, skippable frames must be grounded…).
- **Determinism:** no RNG, a fixed 5 ms sim step, durations in multiples of 10 ms, `sorted()` everywhere. A hash-ordered set once made builds vary between runs; it was fixed in `09d6260`. `--verify` renders twice and fails on any difference.
- **Build id** = SHA-256 over the pipeline version plus each input path and its hash: all variants, all `pipeline/*.py`, faces, props, the clip and its derived sources, overrides.
  - Pitfall: hashing *all* variants and modules means any unrelated edit changes every hash. **Compare pixels, not hashes.**
- **Sheet JSON** (`PA/pipeline/build.py:241-283`):
  - `buildHash`, `frameSize`, `pivot`, `layout`, `directions`, `paletteId`, `palette`, `totalMs`, `inputLockEnd_ms`, `cameraElevation`, `loop`, `root_px_mode`;
  - `layers{shadow,fxBack,fxFront,propBack,propFront}`;
  - per frame: `duration_ms`, `z_px`, `phase`, `events`, `cancelable`, `face`, `root_px`, `skippable`, `smear`, `hold_of`, `prop{visible,layer}`;
  - `anchors{hand_L,hand_R,carry}[dir][frame]`; `derivedFrom`.
- `manifest.json` holds input hashes, override meta and frame hashes. `guide/guide.json` holds the projected joints.

### 2.10 Gemini tooling

- **`PA/pipeline/tools/gemini_critique.sh <name> "<context>" img…`:**
  - Calls `pi -p --model apple-gemini/gemini-4-argon --no-session --no-tools`.
  - The persona is a "veteran Japanese pixel-art (dot-e) art director".
  - Required output: a one-line verdict, the top 5 problems **with pixel x,y**, what to keep, one stretch idea.
  - Output goes to `docs/review/gemini/<name>.md`; 420 s timeout.
- **`gemini_auth.sh` / `gemini_env.sh`.** Root cause (`0a17554`): inside Claude Code, `CLAUDE_TLS_CERT_PATH`/`CLAUDE_TLS_KEY_PATH` make `pi` attempt mTLS with Claude Code's certificate, which Floodgate rejects. The fix is `env -u CLAUDE_TLS_CERT_PATH -u CLAUDE_TLS_KEY_PATH pi …`. There is also an AppleConnect GUI fallback and one retry (`873a4ff`). Before the fix, auth "seemed to work for ~50 min" off a cached token, then failed.
- **`r20_gemini.sh`:** a persistent session (`--session-dir --session-id`), 1500 s, operator-only stance.
- **`r17_gemini_render.py`, `r17b_sdf_render.py`, `r20_render.py`, `r20_boards.py`, `r15_mesh_compare.py`, `r19_compare.py`, `r21_review.py`:** these render an external mesh in the same camera so it can be judged fairly against the house model.

---

## 3. Pixel-art rules they converged on (with reasons)

### 3.1 From hand fixes to generator rules (570 → 98)

| Stage | Hand px | Source |
|---|---|---|
| H1 v1.1 (4 artists + AD cross-check of 174 px) | 570 in 90 files | `PA/docs/review/pixel/H1_*.md`, `PA/overrides/variants/H1_B_final/` |
| v2.1 (8 generator changes) | 254 | `H1_v2_vs_v1.md:31-51` |
| v2.2 | 170 | `H1_v2_vs_v1.md:62-88` |
| v2.3 ("My count is 100, not 88") | 100, NOT SIGNED (mitten-as-boot blocker) | `H1_v2_vs_v1.md:114-122` |
| v2.4 signed | 98 in 28 frames | `H1_v2_vs_v1.md:172`, `PA/overrides/variants/H1v2_B_final/` |
| S4_hd release | 28 in 4 files (3 ponytail tips + 1 temple sliver; 24 px in 3 files in the current tree) | `PA/releases/S4_hd_actions_v1/overrides/` |

**Generator fixes ranked by pixels saved** (`H1_AD_signoff.md:22-32`):

| Fix | px saved |
|---|---|
| back-view skin | ~119 |
| profile eye | ~81 |
| stray coat-tone islands | ~70 |
| boot ground rows | ~69 |
| hat-cuff close | ~65 |
| screen-space pom highlight | ~49 |
| min 2 px features + separators | ~38 |
| face clearance | ~30 |
| outline cleanup | ~25 |
| highlight band close | ~10 |

**The method:**
1. Fix by hand with a reason.
2. Cluster the reasons.
3. Any fix that appears in ~3 or more frames becomes a named, toggleable rule.
4. Rebuild, then `--prune` the overrides the rule now covers.
5. The AD re-signs.

**The failure mode:** a rule that selects by colour or height. `grounded_soles` turned mittens into boots in 13 frames. The fix was to restrict it to the rig's boot **part mask**. *Select by part ID, never by colour alone.*

### 3.2 AD locked rules (H1, `H1_AD_signoff.md:12-20`) and their descendants

1. **Front/3/4 eye.** 2x3, catchlight top-left, near eye only. The far eye gets a dark edge mark and no catchlight. Later S4_hd r15 changed this: the far eye is 2x3, same height but narrower, catchlight on the inner column, no outer lash wing, no blush.
2. **Profile eye.** A 1x2 column, a 1 px nose in front, eye top 1 row below the hat cuff, catchlight on the back side, mirrored E/W. No catchlight when determined or squinting. In code, the cel is pinned to the last skin pixel on the eye row, so the nose is **always exactly 1 px** (`face.py:362-373`).
3. **Mouth.** 1 row below the eyes. It touches no eye, scarf or outline, diagonals included. If it would, shift it up; otherwise omit it. Never a 1-px joyful mouth.
4. **Accessory band** (hat cuff). One ramp, unbroken, no off-ramp tone. Code: `cuff_continuity`, `temple_cover`.
5. **Small round accessory** (pom). A fixed cel with exactly 3 px of top-left highlight, **identical every frame**. Lit or unlit comes from a rule table, not per-normal lighting, which blinked.
6. **Ground row** of footwear. Boot lit or shadow tone, never cuff ("sock feet"). One colour per contiguous sole run.
7. **Nape and chin row** = skin shadow (`chin_shadow`, `backview_skin`). In back views, head skin becomes hair, with no cheek slivers.
8. **One ramp per material.** No stray tone from another ramp: "coat lav_1 islands … it blinked".

### 3.3 Camera, light, size

- **Character camera 16°** (12-18° research range), separate from the 2:1 world.
  - Reason: at 26.565° "the hat brim hides the eyes" (r1 GD FAIL); Pokémon draws humans near-frontal (`pokemon_style.md §3`).
  - The ground shadow still uses 2:1.
- **Screen-fixed key light**, upper-left and slightly toward the camera.
- **Render all 8 directions; never mirror.** Face cels are the only mirrored asset.
- **Size is set by information, not memory.** R2 was chosen because "every design element survives at 2 px or wider; R3 adds flat coat areas but no new information" (r5 AD).

### 3.4 Palette and bands

- ≤32 colours in the master palette, **≤16 per frame**, and 0 off-palette pixels (an exception is raised).
- 2-3 tones per material. Hue-shifted: cool/purple shadows, warm lights. The outline is dark plum `#241628`, never black.
- **About 70% of each part is base tone.** Default 3-tone bands went `[-0.25, 0.72]` → `[-0.45, 0.85]` (`r3_art_director_palette.md:34`). Skin was 4-tone `[-0.35, 0.40, 0.85]` because "skin_0 covered half the face" (r1 AD).
- **Hair bands `[-0.3, 0.999]`.** Only the designed angel ring (forced lam = 1.0) reaches the highlight tone. The r10 stylist: the old 0.55/0.7 threshold "scattered hair_2 blobs, the main cause of the 'random strands' look." **Procedural light should never produce highlight specks; highlights are designed.**
- Bow/ribbon is effectively flat (`[-0.2]`), and its shine is a designed decal (`bow_shine`: a 2-px highlight on each loop of ≥7 px, plus 1 fold pixel). Reason: bands alone never produced it (0 → 160 px in idle).
- Greyscale and 1x gates: no light material may match the ground's luminance (hat 234 vs snow 232 failed). The build writes `greyscale_check` and `distance_test` previews.

### 3.5 Hair: angel ring and clumps (天使の輪, 毛束)

- Hair is shaded in **head space**, so the design is identical in every view (`render.py:_stylize_hair`, `dc5979f`):
  - **Clump lines** at fixed azimuths (S4: every 72°), starting below the crown, skipped within 50° of the face, constant 0.75-px width.
  - **One ring** at `ring_y 0.64`, `ring_w 0.14`, broken at the clump lines, with a crisp under-band shade.
- `ring_trim`:
  - stops the highlight 2 px inside the silhouette;
  - drops runs shorter than 3 px;
  - keeps 1 px clear of the bow;
  - fills 1-2 px breaks.

  Reason: crown "rust specks" and seam rust.
- Style rules (`r13_style_guide §4`):
  - 3-5 tapered clumps, each with a dark line on **one side only**;
  - the ring broken per clump (a 4-5 px dash over a 2-3 px dash);
  - "DON'T stripe the long hair (corduroy)".
- r19 failure: **the thin highlight band loses the majority vote** in a plain Blender bake, so there is "no crown shine". The ring must be a designed mask/AOV, not lighting.

### 3.6 Outline (r10 study: `PA/docs/research/outline_techniques.md`, `r10_outline_AD.md`, `r10_outline_GD.md`)

1. **Closed, connected 1-px exterior, binary alpha.** "It must be closed, but not black." Every open or lineless style "melts" into the ground: the GD measured 5-59% of edge pixels below readable contrast.
2. **Sel-out (色トレス).**
   - Lit (top/left) edges take the material's `line_colors` / darkest tone.
   - Shadow side, bottom 2 rows and feet stay near-black.
   - A **contrast floor** forces near-black where a light material would vanish on the ground.
3. **Pixel-perfect:** L-corner doubles removed. Use the *exterior* mask, because a ramp can legitimately contain the outline colour.
4. **Even outline runs.** An outline pixel whose colour matches none of its outline neighbours takes their majority colour. Reason: speckled sel-out, and frame-to-frame shimmer (GD measured a 10.2% sel-out flip rate).
5. **The outline gets its own palette index.** Eyes use a separate `ink` index, because 9% of outline-index pixels had been inside the silhouette. The engine can then swap the outline to a light rim on dark tiles ("brings melting to 0%").
6. **Inner lines only at real depth breaks** between parts, in the front part's darkest tone, never black. Never on skin (`no_face_lines`). Drop components shorter than 3 px. Reason: dark inner lines clutter 30-40 px sprites and shrink faces.
7. **`separate_materials`.** Where two same-ramp parts touch, the nearer one takes its line colour (a teal bow vs a teal mitten fused otherwise).
8. **Prop depth vs the outline ring.** Dilate body depth into the outline ring, so a prop behind the body never draws over the body's outline (`e6266e4`).
9. **`outline_notches`.** Transparent 1-px notches enclosed on 3 sides become outline. Never create adjacent outline pixels.
10. **`skin_edge_dark`.** Both cheeks get the dark outline. Sel-out had made one cheek soft and the other dark.
11. **`_restore_outline_runs`.** Short 2-3 px sel-out runs over ribbon or hair are line art, not speckle; restore them after despeckle.
12. Review-only rule: **no 2-px dark bands.** A shadow pixel touching the outline is lifted to mid tone.

### 3.7 Silhouette, curves, clusters

- **Monotone runs** on curves (3-2-1-1-2-3); equal runs on straights. Banned: 2-1-2 and 2-1-3-1. A dome top is a flat run of at least 3 px, never a 1-px nipple.
- **`regularize_silhouette`** median-fixes 1-row bumps and notches per row and column. It protects deliberate small accessories, so 1-px tapered tips survive only if this pass leaves them. That is why the ponytail tips still needed 24 override px.
- **Minimum feature width 2 px**; mitten and hand blobs 2x2 to 3x3.
- **Despeckle is material-aware.** Islands ≤3 merge only into their own part's tones, so small parts are never swallowed. `keep` colours (face ink, outline) never grow.
- **Run despeckle a second time after the face stamp**, with face pixels protected. Decals split bands into 1-2 px fragments.
- **`thin_highlights`.** A 1-px-wide highlight run collapses to base unless it touches a 2x2 highlight block. Reasons: flicker, and anti-pillow/anti-banding.
- **`_final_orphans`.** Any remaining pixel with no same-colour 8-neighbour takes its 4-neighbour majority. QA requires orphans = 0, with deliberate/face/override pixels exempt.
- **`temporal_hold`** (near-static loops). An A→B→A toggle with a static neighbourhood takes A, as long as that creates no orphan. Reason: sub-pixel head bob toggled clump seams and bow edges. Crown flicker fell from 74 to 18 (S) and from 51 to 23 (N).

### 3.8 Face and fringe (S4_hd r12-r16)

- **Faces are 2D cels pinned to projected 3D eye markers, never rendered geometry.**
  - Modelled eyes and face lines are hidden in the sprite pass (r19 bake too).
  - View class comes from the head yaw: front ≤22.5°, 3/4 ≤67.5°, profile ≤112.5°, otherwise back.
- **Front eyes** (kawaii_hd): a 2x3 iris, a 3-px outward lash cap, the catchlight top-left **on the same side for both eyes**, 2-px blush. The bridge is **locked at 3 px in front view**; it jittered between 2 and 3 before the lock ("wider-set eyes also read more anime").
- **3/4 eyes:** the bridge is at least 2 px (`89e033c`, after the user said the SE face "looked strange"). The far eye has at least 2 px of skin to the cheek contour, the near eye at least 1. The far eye moves in first, then the near eye moves out.
- **Both eyes share one row** unless the head roll is 12° or more. A 1-px offset reads as a crooked face.
- **One shape family for expressions:** ^ joyful, > < squint (they read as >< in every facing), a lowered lid for determined. Blink = the neutral lash row moved down one row.
- **`hem_pin`.** Draw the bang hem *relative to the cel's lash row L*: rows up to L-2 are hair, L-1 is exactly one skin row. Blinks use the open lash row.
  - Reason: the hem and the lash moved differently on head bob, so the gap strobed 1/0/1/0.
  - **Pin hair to the face cel, not to geometry.**
- **Lone-hair cut:** hair pixels inside the face with 3 or more skin/eye neighbours become skin. **Lash beats bang tip** on the lash row.
- **Temple rules convert skin only, never outline.** In `d2e0a6d` an SW-mirror regression turned the dark contour into mid hair. **Every face rule must be checked on the mirrored side.**
- **`s_fringe`** (front). 3 clumps (centre locked to the eye span), 2 dark V-notches, one 2-px highlight *dot* per clump, no dark pixel on the hem row.
  - "Dots win. Band runs change per frame … That shimmers at 1x" (r16 review 3). This reverted Gemini's band suggestion.
  - Rejected alternatives: a dark under-band (read as a headband) and 1-px flicks (speckle at 1x).
- **`jaw_taper`.** Below the eyes the contour steps in at least 1 px per row for 4 rows (S 10-8-5-2, 3/4 8-8-6-1), with skin-shadow corners. Reason: "balloon cheek". A 1-2-1 step reads lumpy.
- **`profile_brow`:** the frontmost forehead pixel under the fringe is skin shadow, so the face front is not a wall.
- **3/4 fringe tip** overhanging the far contour drops 1 px, so it arcs instead of reading as a "visor brim".

### 3.9 Animation and engine rules worth keeping

- Jump drawn in place; the engine applies `z_px`; the shadow is a separate strip on the ground.
- Head tilt counters spine tilt so the fringe never covers the eyes. Net head pitch ≤5° keeps the profile eye in forward leans. No overhead arms on chibis (hands sit on the head in E/W). Hands stay off the face in E/W.
- Exit frames match idle within 1 px; loop seam ≤1 px (pre-roll two cycles).
- Planted IK is wrong for steps. Walk and run use FK with authored foot paths.
- `trail_wind`: locomotion trailing needs a velocity term. Otherwise "hair/scarf chains never trail".
- GD timing rule: build-up goes after the commit point or in skippable holds, "never between input and effect".
- Use a capsule from the pivot for collision, never per-frame pixel bounds (springy bows change the bounds).
- Derived clips (land from jump frames) hash their source clip.

---

## 4. What worked, what didn't (with evidence)

### 4.1 Worked

| Approach | Evidence |
|---|---|
| One model + one sim + screen-fixed light → 8 consistent facings | Every release passes cross-direction height QA; never mirrored |
| Reasoned overrides + rules from recurring fixes | 570 → 98 (H1); 28 px across S4_hd's 13 clips |
| Ordered 2D pixel pass, independent of the renderer | It ran **unchanged** on SDF, mesh and Blender inputs (`blender_sprites.py`) |
| Face as stamped cels with a spacing solver | Every face fix in r13-r16 was a cel/rule change, and approvals followed |
| Hand-typed `.pix` grids for busts, turnaround and poses | r13 approved after 4-6 rounds; blind expression tests 10/10 |
| Deterministic builds + `--verify` + byte-identity gates | Each new rule shipped behind a flag, with "S4_hd byte-identical" checked every r21 round |
| Numbered decisions + AD triage of external critique | `DECISIONS.md`, `r13_gemini_triage.md` ACCEPT/PARTIAL/REJECT |

### 4.2 Didn't work, or was abandoned

| Approach | Why | Ref |
|---|---|---|
| H1 Pokémon-overworld chibi with a big hat | Signed off, then judged "red hat with legs … nothing reads as feminine" once the user asked for cute and Japanese | `japanese_dote_style.md` |
| HD concept portraits rendered from the 3D model (r10) | User: should be "reimagined … like actual anime pixel art". Team: "reads as a render: no line hierarchy, flat hair, a face that is a texture." | `r12_illustration_plan.md` |
| Vector illustration → pixel (r12) | User: "the illustrations look terrible". The AD's own warning: "Per-pixel authoring by an LLM drifts. We are reliable with coordinates, not with pixel intuition". The vector route, however, produced a "rendered" look. | `1b1cd5d`, `ce801b0`, `r13_brief.md` |
| Gemini as a mesh generator (r15, r17, r20 G) | r15 timed out or failed auth; r17 "hideous"; r20 G stopped at round 2 (fragments in front of the face, sidelock too thin) | `r15_model_mesh_request.md`, `r18_independent_model_brief.md`, `work/r20/gemini/operator_log.md` |
| Mesh compare (r15) | The tool works (`meshrender.py`, `r15_mesh_compare.py`), but there was never a better external mesh to compare | `f9ff5d9` |
| **Blender model → sprites (r19)** | See below | `00_REVIEW/r19_blender_sprites/` |
| Claude Blender base model (r20 C) | 23 rounds; at round 9 "not traceable as canon yet" (helmet hair, V-shield jaw, bow-tie bow, tube coat, stick legs). Direction changed to S4_hd2 (no written rationale). | `r20_AD_C_review1.md`, `6c27007` |
| Colour/height-selected rules | The sole rule recoloured mittens and scarf ends (v2.3 ship blocker) | `H1_v2_vs_v1.md` |
| Procedural highlights from lighting | Speckled "random strands"; a thin band lost the vote in Blender | r10 stylist, r19 README |
| `publish.py` README regeneration | It overwrote the round README with only the last call's clips | `CLEANUP_PLAN.md §5` |

**Did Blender-rendered sprites beat the SDF raycaster?** **No, not at 48x64**, and the reason is proportions, not the renderer. From `PA/00_REVIEW/r19_blender_sprites/metrics.json`:

| | S4_hd (SDF) | Blender B, true 6.5 heads | Blender B, chibi retarget |
|---|---|---|---|
| idle jaggies/frame | 1.5 | **0.8** | **0.6** |
| walk jaggies/frame | 1.4 | 1.4 | 2.5 |
| idle opaque px/frame | 493 | 254 | 421 |
| eye spacing px | 5.3 | 1.74 | 4.01 |

**Blender was better at:**
- real knee and stride articulation;
- fewer jaggies;
- a clean bow knot in back views;
- a noise-free bake;
- no SDF tuning.

**Blender was worse at:**
- the true-proportion figure is "a 6-px-wide stick" with a 3-px face, so the cels don't fit;
- the chibi bone-scale retarget scaled the hair with the head and buried the costume in "7 brown-blob views out of 8";
- the profile face was hidden by side hair;
- no crown shine;
- bangs read as "a flat cap or two horns".

Gemini agreed: "do not adopt". The retained conclusion (r20 brief): **a model for sprites must be "BUILT, not retargeted"** at about 2.5-3.4 heads, with an ~11-px face, side hair off the cheeks and a 2-px shine band.

**Our model meets those conditions:** 2.75 H, a 17-px head, a chibi built natively. So r19 is evidence *for* our route, provided we copy its pixel-pass discipline.

See `docs/img/pixelart_study/r19_compare_idle_8dir.png` and `r19_faces_8x.png`.

### 4.3 Images

All in `docs/img/pixelart_study/`:

| File | Shows |
|---|---|
| `5_hero_v1_vs_v2_keys.png` | H1 v1.1 (570 hand px) vs v2.4 (rules + 98 px) |
| `8_outline_styles_keys.png` | The r10 five-way outline study (sel-out won) |
| `r12_illustration_turnaround_x4_REJECTED.png` | The rejected vector-to-pixel look |
| `r13_turnaround_front_x4.png`, `r13_bust_sheet_x3.png` | The approved hand-pixel look |
| `r19_compare_idle_8dir.png`, `r19_faces_8x.png` | Blender vs SDF |
| `r21_idle_8dir_8x_old_vs_new.png` | S4_hd vs S4_hd2 |

---

## 5. Team and review process

### 5.1 Roles

All roles were played by agents. The lead consolidates.

- **Core:** Art Director (owner of style, final pixel sign-off), Game Director (engine contract, measurements, acceptance), 3D Artist/Animator, Software Engineer.
- **Added as needed:**
  - Animation Director, plus Animators A/B/C (r11, r14);
  - Character Designers A/B/C (r4, r8, r9);
  - Hair Stylists 1/2 and a Face Designer (r10);
  - 4 pixel artists, one per direction pair (H1 review);
  - Illustrators A/B/C (r12);
  - Modelers A/B, forbidden from reading the repo (r18);
  - Track C/G modelers (r20).
- **Gemini** acted as an external critic and, briefly, as a modeler.

### 5.2 Mechanics

- **Every round has three parts:**
  1. a brief (`rN_brief.md`) quoting the user;
  2. role reviews (`rN_review<k>_<role>.md`), each ending in a verdict (APPROVED / FIXES / FAIL) and a numbered must-fix list;
  3. a lead consolidation (`r1_decisions.md`, `r12_hd_fixlist.md`) that becomes numbered rows in `DECISIONS.md` with an owner.
- **Published rounds.** `00_REVIEW/<round>/README.md` has an "Open first" table (the user reviewed on GitHub). Approvals are written into the round and release READMEs and the commit message ("APPROVED by AD, animation director and GD").
- **Disagreements are recorded and escalated** ("Body: split … This is your call"; the GD overriding the designer's pick), or resolved with numbers (melt %, cleanup hours, MB).
- **Pixel review.** Per-direction reviewers write logs with coordinates and reasons. The AD cross-checks and *locks* rules. The generator is changed. Then the AD re-signs.
- **Mockups before code.** For face and bangs, the AD chose among 3-5 pixel mockups (r15 A-E, r16 FA-FC / B1-B3) before anything was implemented.
- **Blind tests:** fresh agents identify expressions from 1x images (10/10).

### 5.3 How they used Gemini

- They used one-shot critiques with images and a fixed format (verdict, top 5 with x,y, keep, stretch).
- **The AD triaged every item** as ACCEPT, PARTIAL or REJECT (with a reason), and checked each claim against the pixels.
- **Useful:**
  - r13: a detached leg, the missing hem trim;
  - r16: "comb" fringe, balloon cheek, squint chin;
  - r18: confirmed model B;
  - r19: confirmed keeping S4_hd.
- **Noisy:**
  - wrong leg named; a "heavy brow … not in the pixels";
  - flagged already-fixed issues;
  - suggestions against the bible;
  - its highlight-band fix shimmered and was reverted.
- **As a generator it failed** every time.

### 5.4 What the user cared about most

1. **Cute, feminine, Japanese anime pixel art**, and specifically *not* something that looks rendered or traced from 3D (r8, r10, r12, r13).
2. **The face:** far-eye spacing (SE "looked strange", "too close"), bangs ("doesn't look bald", "more voluminous … off the forehead"), face shape ("too fat … pointy, curved"), chin ("sharp", flagged in r21).
3. **Consistency across 8 angles** (r9, r11) and **no penetration** of hair or scarf through the body.
4. **Silhouette identity items:** the big bow (sized repeatedly: 2x head → 1.5x → 38 px in every view; "less flat", bouncy) and the ponytail's tapered tip (6 AD rounds).
5. Expressive motion (r11, r14).
6. A "pretty", production-quality base model (r17-r20). This is where the most rounds were spent for the least shipped value.

---

## 6. Recommendations for Akane

### 6.1 Code worth porting

| # | What | From | Why / what to change |
|---|---|---|---|
| 1 | **Supersampled multi-pass bake + majority vote** | `PA/pipeline/blender_bake.py` (ID/part/depth, normal and shadow passes at 12x; `tag_parts`; `ROLE_OF`) + `PA/pipeline/render.py:render_pixels` lines 114-224 (majority coverage/material, ties to the centre sample, band per material) | Our sprite cells are rendered **directly at 128 px with `aa=False`, 1 TAA sample** (`model/render_turnaround.py:135-141, 187-201`), i.e. point-sampled. That is the likely source of the "rampant 1px noise" in `reviews/gemini_pixel_critique_base.raw.txt`. It also contradicts our own bible §5 ("Render at 8-10× target resolution"). Port the bake as 8-12x ID + normal (+ shade) passes and the majority vote into a `tools/pixel/bake_resolve.py`. Changes: the hardcoded 48x64/ELEV/CROWN constants, material/bone names, and reading real Actions instead of the procedural `pose()`. |
| 2 | **Pixel-pass stage order + 2D helpers** | `PA/pipeline/render.py`: `despeckle`/`_despeckle_once` (304-352, material-aware), `pixel_perfect_outline` (423), `selout_outline` + `_even_outline_runs` (454-512), `regularize_silhouette` with a protect mask (539), `jaggy_count` (526); `PA/pipeline/frames.py`: `_restore_outline_runs` (660), `_final_orphans` (382), `_separate_materials` (639), `_ring_trim` (409) | Our `model/sprite_post.py` already does part of this: hair ring thinning, rim, `cluster_clean`, `outline`, `leg_split`, `blade_redraw`, `stamp_eyes`. Port the missing pieces: even-runs, restore-runs, final orphan pass, protected regularize, and the **second despeckle after the eye stamp**. Keep the stage order of §2.5. |
| 3 | **`temporal_hold`** | `PA/pipeline/frames.py:581-615` | Our idle has a 1-px breathing bob and the lint already reports `flicker`. This fixes it at the root with an orphan guard. Apply it to idle and combat-idle. |
| 4 | **Face-cel stamping with a spacing solver** | `PA/pipeline/face.py`: `face_view` (313), `apply_face_cels` (335), `apply_face_eyes` (711-807), `_face_hem` (397) | Our `stamp_eyes` places fixed templates. Port the view-class thresholds, mirrored cel JSON, bridge/contour/row-alignment solving, **paint-only-on-skin**, `deliberate` bookkeeping and the `hem_pin` idea (pin the bang hem to the lash row). Put our templates in a `faces/akane.json` cel file. |
| 5 | **Build/verify/QA discipline** | `PA/pipeline/build.py:57-85` (`input_files`/`build_id`), `--verify` (455), `PA/pipeline/qa.py` (orphans, colours per frame, height spread, loop seam, stale overrides, `timing_budget`) | Hash only the inputs that matter: `.blend`, bake scripts, `docs/palette.json`, the post-pass sources, overrides. Do *not* hash every file, or unrelated edits change every hash. Add a `--release` gate that fails on stale or conflicting overrides (our `px.py stale` already exits 1). |
| 6 | Override `--prune` | `PA/pipeline/override.py:112` | Our `px.py approve` drops pixels the new base already produces. Also add a report: "N override px now produced by rule X", to show rules replacing hand work (the 570 → 98 metric). |
| 7 | Gemini critique wrapper | `PA/pipeline/tools/gemini_critique.sh`, `gemini_auth.sh`, `gemini_env.sh` | Keep the `env -u CLAUDE_TLS_CERT_PATH -u CLAUDE_TLS_KEY_PATH` fix and the "top 5 with x,y" format. Always triage the output; never apply it blindly. |
| 8 | Sheet JSON contract | `PA/pipeline/build.py:241-283` | Fields for anchors (hand_L/hand_R → sword tip/hilt), `events`, `cancelable`, `inputLockEnd_ms`, `z_px`, `smear`, `layers`, `derivedFrom`. They match our `docs/anim_spec.json` (cancel windows, z-offsets). |
| 9 | `pixgrid` (.pix) | `PA/pipeline/pixgrid.py` | Only if we make dialogue busts or portraits. It is the approach the user accepted for illustration-scale art. |

**Do not port:**
- `chargen.py`, `rig.py`, `sdf.py`: our model is Blender.
- `illustrate.py`, `portrait.py`, `face_hd.py`: the rejected routes.
- `fx.py`'s snow puffs.
- The editor's `server._out` path logic (the bug in §2.8); ours is already fixed.

### 6.2 Rules to adopt directly into `docs/pixel_cleanup_guide.md`

Each rule is given with its reason. Where our bible already says it, it is marked (bible).

1. **Closed 1-px exterior with sel-out** (bible §5): lit side gets the material's darkest tone, shadow side and the bottom 2 rows get the outline colour. **Plus:**
   - even outline runs (no single off-colour outline pixel; that shimmers);
   - L-corner doubles removed using the exterior mask;
   - a contrast floor to the outline colour wherever a lit-edge tone is within ~15% luminance of the test floors.
2. **The outline colour is exterior-only.** Pupils and lash use the same hex in our palette (`#1a1220` = outline = dark[0] = leather[0]). That blocks the engine's "swap outline to light rim on dark floors" trick (their 0% melt result). **Consider a separate `ink` index**, even if it has the same RGB, so the engine can tell exterior line from interior pixels. See conflicts, §6.4.
3. **Inner lines only at real part overlaps** (bible), in the front part's darkest tone, never the pure outline, never across skin. Drop interior line fragments shorter than 3 px.
4. **Highlights are designed, not lit.**
   - Hair sheen (angel ring) and bow shine come from a head-space mask or AOV and are then trimmed: 2 px inside the silhouette, minimum run 3, 1 px clear of the bow, 1-2 px gaps filled.
   - Raise the hair highlight threshold so lighting alone can never produce hair[2] specks.
   - A 1-px highlight run collapses to base unless it touches a 2x2 block.
5. **About 70% base tone per part.** Shadow tone only on the far rim and occluded undersides (our red[0] violet rule matches).
6. **No orphans** (QA = 0), except deliberate stamped pixels (eye glint, 1-px nose/mouth). The editor and lint must know which pixels are deliberate.
7. **Despeckle is per material** (islands ≤2-3 merge only into their own ramp). Run it again after the face stamp, with face pixels protected.
8. **Curves use monotone runs; banned patterns are 2-1-2 and 2-1-3-1; a dome top is a flat run of ≥3 px.** Applies to the bun, the bow loops, the bell-cuff hems and the skirt petals.
9. **Minimum feature width 2 px**, except deliberate 1-px tips. Our bible's 2-px blade, 3-px hook and 2-px foot fit this. For 1-px tips (skirt-tail points, ribbon ends, the jaw strands) **protect them from the silhouette regularizer**. The pixelart team lost 6 AD rounds to a 1-px ponytail tip the cleanup kept trimming.
10. **Select by part ID, never by colour or height.** Every cleanup rule and every override macro should be scoped by our object-ID pass. The v2.3 "mittens as boots" blocker is the cautionary tale. For us the risk is red cloth vs bow vs collar vs sleeve, all on the red ramp.
11. **`separate_materials`.** Where two same-ramp parts touch (sleeve cuff vs skirt; bow vs collar), the nearer one takes its line colour. Our bible already asks for "interior lines where two similar values meet"; this is the mechanical rule for it.
12. **Faces:**
    - Eyes are stamped cels, never rendered.
    - Both eyes share one row unless the head roll is ≥12°.
    - Lock the S bridge (e.g. 3 px).
    - 3/4: bridge ≥2 px, far eye ≥2 px of skin to the cheek contour, near eye ≥1; the far eye is narrower, not shorter.
    - Catchlight on the light side, the same side for both eyes.
    - Profile: the eye column sits behind a 1-px skin nose pinned to the actual face edge.
    - Mouth: 1 row under the eyes, touching only skin, else omitted.
    - One expression shape family.
    - Blink = the lash row moved down one.
13. **Pin the bang hem to the lash row.** Exactly 1 skin row between the bangs and the lash in S/SE/SW, in every frame, including blinks. If a bang tip hits the lash row, the lash wins. Fixes bang/eye strobing on the idle breathing bob.
14. **Temple and hair-vs-skin rules convert skin only, never the outline.** Check every face rule on the mirrored direction (SE↔SW, E↔W) separately. Our costume is asymmetric, so mirrored *checks* are structural only.
15. **Back views (N/NE/NW):** head skin becomes hair (no cheek slivers), except the intended 1-2 px cheek/bang edge our facing-tell table asks for in NE/NW. Nape/chin row = skin shadow.
16. **Accessory cels must be identical every frame.** Small round or iconic items (bun knot, hip pouch, flower cluster) are stamped, not lit per frame. Lit vs unlit comes from a rule table, not per-normal lighting, which blinked.
17. **Temporal stability:** no A→B→A pixel toggle in idle unless the neighbourhood moves. A static loop must look static.
18. **Every override has a reason; any fix that recurs in ≥3 frames becomes a `sprite_post.py` rule.** Track the override pixel count per animation as the health metric.

### 6.3 Pitfalls to avoid

1. **Spending rounds on the base model that don't show at sprite size.** r17-r21 consumed about 5 rounds and produced no shipped improvement. The AD had warned: "If HD still only equals legacy at 48x64, tell the user plainly". Judge every model change in the 1x/2x sprite board first; hi-res renders come second.
2. **Retargeting proportions after the fact** (r19 head x2.8). Bake the model you built.
3. **Producing anything that looks rendered or traced** for illustration-scale art. The user rejected that three times. If we make portraits or busts, follow the r13 path: a definition doc, then hand grids, then review.
4. **Treating Gemini as an authority or a generator.** Triage everything with pixel evidence. It names the wrong side, reports artefacts that aren't in the pixels, and argues against the bible.
5. **Auth flakiness inside Claude Code.** Unset `CLAUDE_TLS_*` for `pi`.
6. **Hash-ordered iteration** (Python sets of materials) silently breaks determinism. Sort everything.
7. **Releasing from a dirty tree** (S4_hd v1 `BUILD.json`). Commit or snapshot first.
8. **Stale overrides piling up** (r6: 26 of 44 stale). Re-approve after every new model round. Our `snapshot` → `stale` → `approve` flow exists; make it a gate.
9. **Two agents editing the same files or the same output directories** (their CLEANUP_PLAN §6). One owner per file set; never build into a tree another agent is building into.
10. **Publish scripts that overwrite round READMEs** with partial content.
11. **Committing generated outputs** (their `out/` was 70 MB in git) and `__pycache__`.
12. **Thin designed features lost to the vote**: highlight bands, 1-px ribbons, the blade. Render them as their own ID or AOV and stamp or redraw them (as our `blade_redraw` already does). Don't rely on the downsample.

### 6.4 Conflicts with what we are doing now

| # | Our current choice | Their evidence | Suggested action |
|---|---|---|---|
| C1 | **Sprite cells are point-sampled at 1x** (`render_turnaround.py`: `aa=False`, filter 0, 1 TAA sample, `CELL` resolution). Toon colours are quantized in-shader. | Their pass always supersamples (3x SDF, 12x Blender) and resolves by **majority material + coverage**. The bake was "noise-free" with fewer jaggies. | Biggest technical gap. Our bible §5 already says 8-10x. Render ID + shade passes at 8x and resolve per pixel by majority (per-material quantize, as the bible requires). Measure the change with our lint (orphans, jaggy, flicker) on idle before vs after. |
| C2 | **Camera elevation 30°** (bible §5: "30° gives a better face read on a chibi") | They moved 26.565° → 18° → **16°** because at 26.565° "the hat brim hides the eyes" (r1 GD FAIL), and Pokémon humans are near-frontal. | Our heavy bangs, bun and bow sit on top of the head. Worth a quick A/B at 20-22° vs 30° on S/SE idle, measuring `eye_px` and bang/eye clearance. Keep ground contact at 2:1 either way (we already do). Not a mandate: our head is bigger and we have no hat brim. |
| C3 | Outline colour `#1a1220` is also used for pupils, lash, soles, corset recess (bible §4) | They split `ink` from `outline` so the outline index is exterior-only and the engine can swap it on dark floors (0% melt). | Add an `ink` palette entry (same RGB is fine) for interior uses, or have the exporter emit a separate exterior-outline mask. Our bible §5 already plans an engine silhouette pass, so the mask is cheap. |
| C4 | Hair has a sheen band "required" (bible §4), thinned to 1 px in `sprite_post.py` | Their ring is head-space-designed, trimmed (margin 2, min run 3) and protected from the vote. Highlight thresholds are set so lighting never adds specks. Their r16 lesson: "dots win" over thin bands, which shimmer at 1x. | Make the sheen a head-space mask/AOV, not a light band. Prefer short broken dashes per bang clump over a continuous 1-px line. Check its flicker in idle. |
| C5 | Idle spec says **6 frames @150 ms** (`docs/anim_spec.json`), the rig renders 8 (`tools/pixel/README.md` notes) | Their QA `timing_budget` fails builds on contract mismatches, and loops must seam within 1 px. | Resolve before cleanup effort is spent on frames that may be cut. |
| C6 | Our cleanup pilot is override-first (`pixel/overrides/` is empty; lint and editor are ready) | Their biggest win was rules over overrides (570 → 98) | Use the idle pilot to *collect* reasons, then promote recurring ones into `model/sprite_post.py`. Budget: override px per frame trending down each round. |
| C7 | Rim light pink[0] 1 px, drawn on the hair and bow silhouette (bible §5) | Their sel-out rule puts the material's darkest tone on lit edges; an extra rim colour on the silhouette competes with the outline and with `outline_gap` lint. | Not a conflict in principle. Define the precedence explicitly in the cleanup guide: rim side = pink[0] *inside* the closed outline, or *as* the outline on the rim side, but never both. Our lint already accepts `pink_0` as an outline tone. |
| C8 | Bible: 128x128 cell, ~56 px character, 22-colour palette | Their 48x64 limit was ≤16 colours per frame | Fine. 56 px gives us room their r19 bake lacked (eyes 4-5 px). Still add a colours-per-frame lint warning (e.g. >18) to catch stray tones. |

`docs/pixel_cleanup_guide.md` did not exist when this study was written. Section 6.2 is written so it can be pasted into it.

---

## 7. Key file index (pixelart)

**Status and decisions:**
- `PA/START_HERE.md`
- `PA/README.md`
- `PA/docs/DECISIONS.md`
- `PA/docs/CLEANUP_PLAN.md` (§5 = their learnings seed)
- `PA/00_REVIEW/README.md`

**Rules:**
- `PA/docs/review/pixel/H1_AD_signoff.md`, `H1_v2_vs_v1.md`
- `PA/docs/research/{outline_techniques,japanese_dote_style,pokemon_style}.md`
- `PA/docs/review/r13_style_guide.md`, `r13_design_bible.md`

**Face:**
- `PA/docs/review/r15_face_bangs.md`, `r16_review*.md`
- `PA/data/faces/kawaii_hd.json`

**Blender verdict:**
- `PA/00_REVIEW/r19_blender_sprites/README.md`, `metrics.json`
- `PA/docs/review/gemini/r19_blender_sprites.md`

**Code:**
- `PA/pipeline/{render,frames,face,pixelrules,qa,build,override,blender_bake,blender_sprites,pixgrid,meshrender}.py`
- `PA/pipeline/tools/gemini_*.sh`

**Releases:**
- `PA/releases/S4_hd_actions_v1/README.md` + `BUILD.json`
- `PA/releases/S4_actions_v1/README.md`
- `PA/releases/H1_v2_4`

**Commits:**

| Commit | What |
|---|---|
| `aa2d9fc` | r0-r8 bulk |
| `a939e36` | Sel-out + ink |
| `4883be7` | S4 v1 approved |
| `85853e2` | S4_hd v1 approved |
| `ce801b0` | r13 restart |
| `89e033c` | 2-px bridge |
| `e4f3ea6` | `hem_pin` |
| `d2e0a6d` | Skin-only temple |
| `09d6260` | `s_fringe` + determinism fix |
| `bbb69a8` | `jaw_taper` |
| `0a17554` | Gemini auth root cause |
| `2933f56` | r19 Blender verdict |
| `6c27007` | Direction change |
| `2000561` | r21 round 7 / HEAD |
