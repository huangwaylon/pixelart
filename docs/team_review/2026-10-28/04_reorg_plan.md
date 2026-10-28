# 04 Repo reorg plan (architect, 2026-10-28)

Written against branch `merge-swordswoman`, HEAD `e1d45ca6`. **Nothing has been moved yet.** The executor runs
the phases in order. Each phase is one commit and ends with its own checks. Every count below came from
`git ls-files`, `git grep` or `/usr/bin/grep -r` on 2026-10-28. Re-run the quoted grep before each rewrite. If a
count differs by more than a few, stop and ask.

## 0. Decision in one paragraph

**Recommended: Option B, "two roots, in place, plus `archive/`".** Snowpeak stays at the repo root and
`swordswoman/` stays where it is. Dead ends move into an `archive/` folder (`archive/snowpeak/...` at the root,
`swordswoman/archive/...` inside the project). Generated files stop being tracked, and the root README becomes an
index. This is a deliberate rejection of `projects/snowpeak` + `projects/swordswoman` (Option A, section 2). Option A
is mechanically possible, but it means rewriting **1403 swordswoman files** (769 tracked + 634 untracked or ignored,
which git cannot roll back), 50 `.gitignore` lines, 2 symlinks and a venv. It would also change the bytes of 248 committed
JSON outputs that embed absolute paths, so every "byte-identical to the committed artifact" check in swordswoman would
fail afterwards. Option B instead edits **no build-hash input** (`pipeline/*.py`, `data/**`, `overrides/**`), so every
snowpeak build ID stays the same, and it rewrites only about 25 small text files.

## 1. Evidence (inventory, 2026-10-28)

| Path | Disk | Tracked | What it is | Facts that constrain moves |
|---|---|---|---|---|
| `pipeline/` | 1.3 MB | 48 | snowpeak package, `python -m pipeline.*` | `ROOT = dirname(dirname(__file__))` in build/server/board/override. `build.py:input_files()` hashes `pipeline/*.py`, `data/variants/*.json`, `data/faces`, `data/props`, the clip's `data/animations/*.json` and `overrides/**` by **path relative to ROOT**. |
| `editor/` | 24 KB | 3 | browser editor | served from ROOT by `pipeline/server.py` (`/editor/`, `/api/*`, PORT env, default 8777) |
| `data/`, `overrides/`, `art/` | 2.6 MB | 235 / 121 / 76 | snowpeak sources | 27 `data/animations/*.json` and `pipeline/pixelrules.py` cite `docs/review/...`, so **renaming `docs/review` changes every build ID** |
| `00_REVIEW/` | 37+ MB | 722 | review rounds r10–r21 (the user reads these on GitHub) | written to by `pipeline/publish.py` (hashed), `pipeline/tools/r15_*, r17*, r19_*, r21_*`, `r13_bust/*`. **Renaming it means editing hashed `publish.py`.** |
| `releases/` | 16 MB | 884 | `S4_hd_actions_v1` (approved hero), `S4_actions_v1` (rollback), `H1_v1/v2_1/v2_3/v2_4` (668 files, old jump-only hero), `HERO -> H1_v2_4` symlink (stale) | H1 is referenced by 12 occurrences in 5 files (START_HERE, CLEANUP_PLAN, 2 x `docs/review/pixel/H1_*.md`, the swordswoman study). `releases/HERO` is referenced in 3 files (all docs). |
| `out/` | 204 MB | **2553** (variants 2490, jump 33, boards 30) | generated "latest build" copies | ignored by `out/*` but tracked from before that rule. `!out/boards/` whitelists the boards. |
| `builds/`, `work/` | 2.9 GB, 793 MB | 0 | generated / scratch | **Bug:** the root `.gitignore` has `work/` *unanchored*, so it also ignores every `swordswoman/**/work/`. That silently defeats `!swordswoman/v2/g96/work*/*.json`: the 6 g96 calibration JSONs (`act_H`, `H_state`, `H2_state`, `s0..s2`) were never committed (`git check-ignore -v` -> `.gitignore:14:work/`). |
| `blender/` | | 21 | r18 independent-model sources A/B | hard-coded `/tmp/indep/{A,B}` (17 occurrences in 9 files), so it cannot run in place. Only referenced by `swordswoman/docs/pixelart_project_study.md`. Not used by `pipeline/blender_*.py`. |
| `pipeline/tools/` | | | per-round scripts | not hashed. `r17_gemini_render.py` and `r17b_sdf_render.py` are **untracked** and import `pipeline.tools.r15_mesh_compare`. `make_s4_hd2.py` imports `pipeline.tools.make_s4_hd`. `r13_bust/*` imports `pipeline.tools.r13_bust.pixlib`. `pipeline/tools` has no `__init__.py` (namespace package; `-m` works). |
| `START_HERE.md` | | 1 | H1 round-5 status (`releases/HERO`, `out/boards`) | fully stale. Referenced only by CLEANUP_PLAN and the swordswoman study. |
| `docs/CLEANUP_PLAN.md` | | 1 | 2026-10-23 cleanup plan, **never executed** | its data/variant pruning (sections 1.3–1.6) is still a valid, separate proposal |
| `reference/3d/` | 58 MB | 197 | swordswoman Hunyuan outputs. `best -> ../../swordswoman/v2/hy3d/best` | `hunyuan_studio_research/` and `sota_survey/` are **exact copies** of `.models/hunyuan_studio` and `.models/sota_survey` (`diff -rq` differs only in `.DS_Store`) |
| `swordswoman/` | 4.3 GB | 13329 | merged project | **2764 absolute `…/pixelart/swordswoman` occurrences in 769 tracked files**, plus 634 untracked/ignored files on disk (248 json, 234 py, 208 txt, 54 sh among the tracked ones). There are 0 such references outside `swordswoman/`. 2 `.pyc` files embed the path. `.scratch -> ../.models`. `.venv/bin/activate` has the absolute `VIRTUAL_ENV`. |
| `.models/` | 41 GB | 0 | weights/venvs + scratch | the real items are `hy_omni` (35 G), `parts` (4.8 G), `pixelize` (1.0 G) and `mocap` (103 M). The other 41 entries are scratch (list in 3.3). Venv console-script shebangs are absolute, so **`.models` must not move.** |

Swordswoman live-dependency findings (these block "archive every dead v2 strand"):
- `v2/pixelize` -> `v2/final` (56 files; `pzlib.py` does `sys.path.insert(0, ROOT+'v2/final/tools')`) and -> `v2/hair` (70).
- `v2/anim_cut/tools/cm.py` (used by `ff_redraw`, which m96/animate96 use) loads `HERE/../../pixel/palette.json`. That is
  **`v2/pixel/palette.json`, which is gitignored and untracked** (`.gitignore:57 swordswoman/v2/pixel/`). It is a live input that exists only on disk.
- `v2/face` is read by mocap/pose/throw code (15+ files). `v2/face2` by prop/hy3d rig F. `v2/pose` by mocap/throw.
  `v2/design` by hy3d/hair/pose. `v2/rigcal` by g96. `v2/style` by fx/face/anim_cut. `v2/anim_redraw` by `v2/heads/tools/crit.sh`.
  `v2/masters` by `ff_redraw.py` (`--stamps` option).
- No live inbound references (code or abs path): `v2/pixel_E` (14 tracked), `v2/animate` (9), `v2/mastersF` (79; only its own 5 files),
  `v2/anim` (0 tracked, 32 MB on disk; only referenced from dead `anim_redraw`/`pixel_E`).
- v1 dirs (`concept`, `model`, `pixel`, `hybrid`, `renders`, `tools/hybrid`, `tools/pixel`): **no v2 code references them.**
  `v2/BRIEF.md` and the README cite `hybrid/ANIM_DIRECTION.md` and `hybrid/STYLE_TARGET.md` (text only). Internally, 591 v1 code
  files use cwd-relative paths between v1 dirs.

Baseline smoke results (run 2026-10-28, current tree):
- `repro_h.py ... /tmp/r`: 10 of 11 outputs are byte-identical to `v2/hy3d/rigs/H2/parts/`. **`torso.glb` differs in bytes**
  (248908 vs 248744 B), but vertices, faces, vertex and face colours are identical (the GLB JSON header differs). So compare
  geometry, not bytes (script in 7.4). That is the state before the reorg; it is not caused by it.
- `pz.py EC0 S 96`: prints `EC0_S_96 ok (128, 128)`. The `.json` is byte-identical run to run. The `.txt`/`.png` differ run to run
  (PixelOE is non-deterministic, as the swordswoman README says). Compare the `.json` exactly and only sanity-check the png/txt.
- `build_id('idle','S4_hd2') == build_id('idle','S4_hd') == c715eca703ac`. The ID does not include the variant name, because
  every variant file is hashed. This is harmless (output dirs carry the tag) but worth knowing.

## 2. Options weighed

| | A: `projects/snowpeak` + `projects/swordswoman` | **B: in place + `archive/` (recommended)** | C: only `swordswoman -> projects/swordswoman` |
|---|---|---|---|
| snowpeak `python -m pipeline` | works if cwd = `projects/snowpeak` (ROOT follows `__file__`, build IDs unchanged since paths are ROOT-relative). But 57 command lines in 30 tracked docs, every agent prompt, and memory notes assume cwd = repo root. Root `.venv` must be recreated or called as `../../.venv/bin/python`. | unchanged | unchanged |
| editor URL | `/editor/` unchanged (served from the new ROOT) | unchanged | unchanged |
| GitHub links to `00_REVIEW/...` | all 722 files change URL | unchanged | unchanged |
| swordswoman absolute paths | one perl over 1403 files (769 tracked + 634 untracked, the untracked ones not revertible by git) | **0** | same as A |
| other swordswoman fallout | `.scratch` symlink -> `../../.models`; `reference/3d/best` symlink; 50 `.gitignore` lines; `.venv` activate; 2 `.pyc`; committed JSON outputs change bytes (for example pz `*.json` embeds the source png path) | none | same as A |
| benefit | symmetric layout | removes the stale and confusing items with near-zero risk | little: the root would still be snowpeak |

Option A is a reasonable one-shot later if it is ever wanted. Appendix A gives the exact recipe, but this plan does not schedule it.

## 3. Target structure (after phases 1–6; phase 7 adds `swordswoman/archive/v1`, `archive/v2`)

```
pixelart/
  README.md                  index (section 9)
  .gitignore                 root patterns anchored (/builds/ /out/ /work/)
  # ---- snowpeak (root project; cwd must be the repo root) ----
  pipeline/                  unchanged core + tools/{make_s4_hd.py, make_s4_hd2.py, r21_review.py, gemini_*.sh, r13_bust/}
    tools/rounds/            r15_mesh_compare, r17_gemini_render, r17b_sdf_render, r19_compare, r20_boards, r20_render, r20_gemini.sh, make_r3_palettes
  editor/  data/  overrides/  art/            unchanged
  00_REVIEW/                 unchanged rounds r10..r21, README rewritten as a status index
  releases/                  S4_hd_actions_v1 (hero), S4_actions_v1 (rollback), README.md (new)
  docs/                      DECISIONS, SCHEMA_v2, CLEANUP_PLAN (banner: superseded), kickoff/, research/, review/ (unchanged), team_review/
  builds/ out/ work/         gitignored, local only (out/ fully untracked)
  # ---- shared ----
  reference/3d/              unchanged (swordswoman 3D outputs + research copies)
  archive/
    README.md                old path -> new path table
    snowpeak/
      releases/H1_v1 H1_v2_1 H1_v2_3 H1_v2_4
      boards_r04_r10/        (was out/boards, 30 files)
      r18_blender_src/A B    (was blender/)
      START_HERE_2026-10-22.md
  .models/                   ONLY hy_omni/ parts/ pixelize/ mocap/   (gitignored)
  .venv/                     unchanged
  # ---- swordswoman (self-contained; cwd must be swordswoman/) ----
  swordswoman/
    README.md  docs/ (+ docs/reviews/)  refs/  tools/  v2/  .scratch -> ../.models  .venv/
    archive/
      scratch_heads/         (was .scratch_heads, 3 files)
      scratch/               (gitignored: ex-.models scratch, 23 MB + ai_pixel_test 35 MB)
      v1/  (phase 7)         concept/ model/ pixel/ hybrid/ renders/ tools/{hybrid,pixel}/
      v2/  (phase 7)         pixel_E/ animate/ mastersF/ anim/
```

## 4. Naming and retirement decisions

Conventions going forward: new directories are lowercase snake_case. Review rounds are `rNN_<topic>` with a two-digit
round number and a lowercase topic. Variant IDs keep their case (`S4_hd2` is a data ID shared by `data/variants`,
`out/variants`, `builds`, `releases`). Dead ends go to `archive/`, not to deletion; git history plus the tag
`pre-reorg-2026-10-28` covers anything that does get deleted.

**Deliberately NOT renamed** (each rename would touch hashed build inputs or published URLs):
- `00_REVIEW/`: its `00_` prefix sorts it first on GitHub. Renaming it requires editing `pipeline/publish.py` (hashed, which changes every build ID) and 5 tools.
- The round folders `r10_S4_jump`, `r10_semichibi_candidates`, …: these are already-numbered, published URLs. The only uppercase one is `r10_S4_jump`, which stays.
- `docs/review/r1_*.md … r9_*.md` (not zero-padded): 27 `data/animations/*.json` + `pipeline/pixelrules.py` cite `docs/review/...`, so moving or renumbering them changes every build ID. New review docs use `rNN_`.
- `swordswoman/v2/<strand>` names and `swordswoman/refs/` (22 files, 17 of them code/json, cite `refs/1.png` etc.).

### 4.1 Snowpeak

| Item | Action | Destination | Why |
|---|---|---|---|
| `releases/HERO` (symlink) | `git rm` | – | stale (points to the jump-only H1). The hero is `S4_hd_actions_v1`. |
| `releases/H1_v1`, `H1_v2_1`, `H1_v2_3`, `H1_v2_4` | `git mv` | `archive/snowpeak/releases/` | superseded hero. Kept browsable. 2 doc refs rewritten. |
| `releases/H1_v2_4/.DS_Store`, `…/preview/.DS_Store` | `git rm --cached` | – | the only 2 tracked `.DS_Store` files |
| `START_HERE.md` | `git mv` | `archive/snowpeak/START_HERE_2026-10-22.md` | stale. README replaces it. |
| `blender/` | `git mv` | `archive/snowpeak/r18_blender_src/` | `/tmp/indep` scripts, not runnable in place. Note: `pipeline/blender_bake.py` and `blender_sprites.py` stay, because they are hashed. |
| `out/variants`, `out/jump` (2523 tracked) | `git rm -r --cached` (files stay on disk) | – | generated. Other clones will lose them on pull, which is fine. |
| `out/boards` (30 tracked) | `git mv` | `archive/snowpeak/boards_r04_r10/` | historical boards, cited by 6 docs (rewritten) |
| `pipeline/tools/{r15_mesh_compare,r17_gemini_render,r17b_sdf_render,r19_compare,r20_boards}.py`, `r20_render.py`, `r20_gemini.sh`, `make_r3_palettes.py` | `git mv` | `pipeline/tools/rounds/` | finished rounds. The current tools (`make_s4_hd*.py`, `r21_review.py`, `gemini_*.sh`, `r13_bust/`) stay. r13_bust stays because it serves the approved r13 art and is imported as `pipeline.tools.r13_bust.pixlib`. |
| `docs/CLEANUP_PLAN.md` | keep + banner | – | structure superseded by this plan; data pruning still pending |
| `00_REVIEW/README.md` | rewrite | – | it currently describes only r10 |
| `00_REVIEW/r21_s4_hd2/latest/S4_hd2_idle.obj` (15.6 MB, untracked) | leave untracked | – | owner decision. Do not commit as part of the reorg. |

### 4.2 Swordswoman

| Dir | Status (README + NOTES + inbound refs) | Destination |
|---|---|---|
| `v2/m96`, `pixelize`, `hy3d`, `g96`, `fx96`, `qc`, `animate96`, `motion`, `heads96`, `prop`, `mocap`, `throw`, `unarmed`, `REVIEW`, `_lead`, `tools`, `BRIEF.md` | live | stay |
| `v2/final`, `hair`, `anim_cut`, `face`, `face2`, `design`, `pose`, `style`, `parts`, `rigcal`, `masters`, `heads`, `anim_redraw`, `fx` | dead or superseded **but read by live code** (section 1) | stay; marked "support/dead" in the README strand table |
| `v2/pixel` | dead, but `v2/pixel/palette.json` is a live input (`cm.py`) | stay; `git add -f v2/pixel/palette.json` |
| `v2/pixel_E`, `v2/animate`, `v2/mastersF`, `v2/anim` | dead, no live inbound refs | `swordswoman/archive/v2/<name>` (phase 7, optional) |
| `concept/`, `model/`, `pixel/`, `hybrid/`, `renders/`, `tools/hybrid`, `tools/pixel` | v1 dead end (README "Dead ends") | `swordswoman/archive/v1/...` (phase 7, optional). First move `hybrid/ANIM_DIRECTION.md` and `hybrid/STYLE_TARGET.md` to `docs/`. |
| `.scratch_heads/` (3 tracked: `r.py`, `all.png`, `E_S_base_orig.txt`) | one-off scratch, no inbound refs | `swordswoman/archive/scratch_heads/` (1 abs-path rewrite in `r.py`) |
| `reviews/` (3 files) | Gemini critiques from v1 | `swordswoman/docs/reviews/` (3 refs rewritten) |
| `refs/` | canonical design inputs (`refs/1.png` wins on conflict) | stay |
| `v2/**/*.bak_*` (14 tracked) | backups | leave (optional `git rm` later) |

### 4.3 `.models/` (gitignored): keep models/venvs/data only

| Keep in `.models/` | Why |
|---|---|
| `hy_omni/` | Omni venv + weights. Used by g96, hy3d, prop scripts. Hard-coded absolute in 7 scripts. |
| `parts/` | PartCrafter |
| `pixelize/` | PixelOE venv/src (`pz.py`, m96 tools) |
| `mocap/` | CMU/Bandai/LaFAN1 data. Absolute in `v2/unarmed/scripts/armstat.py`. |

| Move out of `.models/` | Size | Refs | Destination |
|---|---|---|---|
| `ai_pixel_test/` | 35 MB | `swordswoman/docs/pixel_cleanup_guide.md:13` | `swordswoman/archive/scratch/ai_pixel_test` (ref rewritten) |
| `landscape/` | 52 KB | `v2/hy3d/LANDSCAPE.md:5` | `swordswoman/archive/scratch/landscape` (ref rewritten) |
| `hunyuan_studio/` | 3.4 MB | 3 doc lines | **delete** after `diff -rq` (duplicate of tracked `reference/3d/hunyuan_studio_research`); refs -> `../reference/3d/hunyuan_studio_research/` |
| `sota_survey/` | 1.8 MB | 1 doc line | **delete** after `diff -rq` (duplicate of `reference/3d/sota_survey`); ref -> `../reference/3d/sota_survey` |
| `designE/` `guide/` `m9crop/` `NE_artist/` `S_artist/` `W_pixel/` `nw/` `se/` `sw/` `qa_ne_r3/` `qa_nw/` `qa_S/` `qa_sw/` `qa_W/` | ~19 MB | 0 tracked refs, 0 on-disk refs | `swordswoman/archive/scratch/` |
| `gem_test.txt` `img_test.json` `models.txt` `proxy.log` `p_argon-4.json` `p_gemini-3-pro-image-preview.json` `p_gemini-3-pro-image.json` `p_gemini-3.1-flash-image-preview.json` `p_gemini-3.5-flash-image.json` `p_gemini-3.8-flash.json` `p_gemini-4-argon.json` `p_gemini-argon-4.json` `t_argon-4.txt` `t_gemini-2.5-flash-image.txt` `t_gemini-3-pro-image-preview.txt` `t_gemini-3.1-pro-preview.txt` `t_gemini-3.5-pro.txt` `t_gemini-3.8-flash.txt` `t_gemini-3.8-pro.txt` `t_gemini-argon.txt` | ~4.2 MB | 0 | `swordswoman/archive/scratch/` (owner may `rm` later) |
| `.DS_Store` | | | `rm` |

## 5. Execution

All commands run from `/Users/waylonhuang/Documents/other/pixelart` unless the line starts with `cd swordswoman`.
Use **`/usr/bin/grep`** (the interactive shell's `grep` here is ugrep and handles `--include` differently). Use `.venv/bin/python -B`
so no `.pyc` files are written.

### Phase 0: preflight and baselines (no commit, except 0.2)

0.1 Nobody else is working: `pgrep -fl 'pipeline\.|pz\.py|ff_redraw|repro_h|Blender'` prints nothing. Tell the other team agents to pause.

0.2 The working tree is clean apart from these known untracked paths: `00_REVIEW/r17_gemini_model/` (2 png), `00_REVIEW/r21_s4_hd2/latest/S4_hd2_idle.{obj,mtl}`,
`docs/review/gemini/r16_face_bangs_r3.md`, `docs/review/gemini/r17_s{0..5}_*.md`, `docs/review/r16_review3.md`,
`pipeline/tools/r17_gemini_render.py`, `pipeline/tools/r17b_sdf_render.py`. **Ask the owner** before committing them (phase 3 needs the two r17 tools tracked):
```bash
git status --short
git add 00_REVIEW/r17_gemini_model docs/review/gemini/r16_face_bangs_r3.md docs/review/gemini/r17_s*.md \
        docs/review/r16_review3.md pipeline/tools/r17_gemini_render.py pipeline/tools/r17b_sdf_render.py
git commit -m "r16/r17: commit previously untracked review docs, gemini-model tools and turnarounds"
git status --short        # expect only: ?? 00_REVIEW/r21_s4_hd2/latest/S4_hd2_idle.mtl / .obj
```
If the owner says no, plain-`mv` the two r17 tools in phase 3 (instead of `git mv`) and still apply the perl.

0.3 Tag and branch:
```bash
git tag pre-reorg-2026-10-28
git switch -c reorg-2026-10-28
```

0.4 Baselines (the S4_hd2 build takes about 5 min):
```bash
B=/tmp/reorg_base; rm -rf $B; mkdir -p $B
.venv/bin/python -B -c "from pipeline.build import build_id
for v in ('S4_hd','S4_hd2','S4_halfup_bow'):
    for a in ('idle','walk','run','jump_sc'): print(v, a, build_id(a, v)[0])" > $B/build_ids.txt
.venv/bin/python -B -m pipeline.build --variant S4_hd2 --anim idle --verify > $B/build.log 2>&1; echo "exit $?"   # expect exit 0
cp -R out/variants/S4_hd2__idle $B/S4_hd2__idle
git ls-files | sort > $B/tracked.txt
cd swordswoman
.scratch/hy_omni/venv/bin/python -I v2/g96/scripts/repro_h.py v2/hy3d/rigs/H2/parts/spec_solved.json v2/hy3d/partsAB4f v2/hy3d/best/skel.txt /tmp/reorg_base/rigH2
.scratch/pixelize/pixeloe/venv/bin/python -I v2/pixelize/tools/pz.py EC0 S 96 --pal v2/pixelize/palette.json --out /tmp/reorg_base/pz
cd ..
```
Also write `/tmp/reorg_glbcmp.py` (outside the repo):
```bash
cat > /tmp/reorg_glbcmp.py <<'EOF'
import sys, os, numpy as np, trimesh
a_dir, b_dir = sys.argv[1:3]; bad = 0
def ld(p):
    s = trimesh.load(p); return s.dump(concatenate=True) if hasattr(s, "dump") else s
for n in sorted(os.listdir(b_dir)):
    if n == "spec_solved.json": continue          # input of repro_h, not an output
    pa, pb = os.path.join(a_dir, n), os.path.join(b_dir, n)
    if not os.path.exists(pa): print("MISSING", n); bad = 1; continue
    if open(pa, 'rb').read() == open(pb, 'rb').read(): print("BYTES-SAME", n); continue
    if not n.endswith(".glb"): print("DIFF", n); bad = 1; continue
    A, B = ld(pa), ld(pb)
    ok = (np.array_equal(A.vertices, B.vertices) and np.array_equal(A.faces, B.faces)
          and np.array_equal(A.visual.vertex_colors, B.visual.vertex_colors))
    print("GEOM-SAME" if ok else "GEOM-DIFF", n); bad |= (not ok)
sys.exit(bad)
EOF
```
Today's expected result against `v2/hy3d/rigs/H2/parts` (verified 2026-10-28): 10 x BYTES-SAME, `torso.glb` GEOM-SAME, exit 0.
Pass the output dir first and `rigs/H2/parts` second.

### Phase 1: `.gitignore` fix + untrack generated files

1.1 Edit `.gitignore` by hand. Replace this exact block (lines 7–14):
```
# reproducible build outputs (regenerate with python -m pipeline.build); boards + releases are kept
builds/
out/*
!out/boards/
**/pixelreview/
out/.DS_Store
.DS_Store
work/
```
with:
```
# reproducible build outputs (regenerate with python -m pipeline.build); releases are kept. Root-anchored on purpose.
/builds/
/out/
/work/
**/pixelreview/
# swordswoman per-strand scratch dirs (previously caught by the unanchored `work/`); g96 work JSON stays tracked
swordswoman/**/work/
!swordswoman/v2/g96/work/
swordswoman/archive/scratch/
```
Leave the rest of the file unchanged. The existing `swordswoman/v2/g96/work*/*` + `!swordswoman/v2/g96/work*/*.json` lines at the end
still apply. This rule set was tested in a scratch repo: only `g96/work/*.json` and `g96/work2/*.json` become addable, and every other
`swordswoman/**/work/` stays ignored.

1.2 Untrack:
```bash
git rm -r -q --cached out/variants out/jump
git rm -q --cached releases/H1_v2_4/.DS_Store releases/H1_v2_4/preview/.DS_Store
git add .gitignore swordswoman/v2/g96/work/*.json      # the 6 calibration JSONs that were never committed
git add -f swordswoman/v2/pixel/palette.json             # live input of v2/anim_cut/tools/cm.py
```
Checks:
```bash
git ls-files out | wc -l                     # 30 (boards; moved in phase 2)
git status --short | /usr/bin/grep -v '^D ' # only: M .gitignore, A 6 g96 json, A palette.json, ?? S4_hd2_idle.{obj,mtl}
git status --short --ignored swordswoman/v2/g96/work | head   # srch*/ and non-json still ignored (!!)
git check-ignore -v swordswoman/v2/m96/work/x 2>/dev/null || echo "check: m96/work must be ignored"
```
Commit: `git commit -m "gitignore: anchor root build/out/work; untrack generated out/; track g96 work JSON + v2/pixel/palette.json"`

### Phase 2: snowpeak archive

```bash
mkdir -p archive/snowpeak/releases
git rm -q releases/HERO
git mv releases/H1_v1 releases/H1_v2_1 releases/H1_v2_3 releases/H1_v2_4 archive/snowpeak/releases/
git mv START_HERE.md archive/snowpeak/START_HERE_2026-10-22.md
git mv blender archive/snowpeak/r18_blender_src
git mv out/boards archive/snowpeak/boards_r04_r10
```
Path rewrites. Check the counts first:
```bash
git grep -cE 'releases/H1_(v1|v2_1|v2_3|v2_4)' -- docs/review         # expect H1_AD_signoff.md:1, H1_v2_vs_v1.md:1
perl -pi -e 's#\breleases/(H1_v1|H1_v2_1|H1_v2_3|H1_v2_4)\b#archive/snowpeak/releases/$1#g' \
  docs/review/pixel/H1_AD_signoff.md docs/review/pixel/H1_v2_vs_v1.md
git grep -c 'out/boards/' -- docs 00_REVIEW                              # expect 6 files, 1-3 each
perl -pi -e 's#\bout/boards/#archive/snowpeak/boards_r04_r10/#g' \
  docs/research/outline_techniques.md 00_REVIEW/r10_outline_study/outline_techniques.md \
  docs/review/r10_face_designer.md docs/review/r4_outfits.md docs/review/r4_proportions.md docs/review/r5_panel_art_director.md
perl -0pi -e 's/\A/> **Status 2026-10-28:** the repo-structure parts of this plan are superseded by `docs\/team_review\/2026-10-28\/04_reorg_plan.md`. The data\/variant\/dead-module pruning (sections 1.3-1.6) was never executed and is still a valid separate proposal.\n\n/' docs/CLEANUP_PLAN.md
```
Do **not** rewrite: `README.md:100` and the `pipeline/board.py` docstring (`--out out/boards/x` is an example of a new local output);
`swordswoman/docs/pixelart_project_study.md` (a dated study, left as history); `docs/CLEANUP_PLAN.md` body (history).
Remaining `out/variants/...` and `out/jump` prose in old docs (19 + 4 files) refers to regenerable outputs; leave it.

Create `archive/README.md`: one table of old path -> new path (the 5 moves above plus the phase 3/4/7 ones) and the sentence
"Everything here is frozen history; nothing in `pipeline/` reads it. Deleted items: `git show pre-reorg-2026-10-28:<path>`".
Create `releases/README.md`: 2 rows (`S4_hd_actions_v1` = approved hero, built per its `BUILD.json`; `S4_actions_v1` = v1 rollback),
plus "H1 releases: `archive/snowpeak/releases/`".

Checks: `ls releases` -> `README.md S4_actions_v1 S4_hd_actions_v1`. `git ls-files out | wc -l` -> 0. `test ! -e blender`.
Commit: `git commit -m "Archive snowpeak dead ends: H1 releases, out/boards, r18 blender sources, START_HERE; drop stale HERO symlink"`

### Phase 3: `pipeline/tools/rounds/`

```bash
mkdir -p pipeline/tools/rounds
git mv pipeline/tools/r15_mesh_compare.py pipeline/tools/r17_gemini_render.py pipeline/tools/r17b_sdf_render.py \
       pipeline/tools/r19_compare.py pipeline/tools/r20_boards.py pipeline/tools/r20_render.py \
       pipeline/tools/r20_gemini.sh pipeline/tools/make_r3_palettes.py pipeline/tools/rounds/
# module paths + file paths (imports in r17*, docstrings, 3 docs)
perl -pi -e 's/\bpipeline\.tools\.(r15_mesh_compare|r17_gemini_render|r17b_sdf_render|r19_compare|r20_boards)\b/pipeline.tools.rounds.$1/g;
             s#\bpipeline/tools/(r15_mesh_compare\.py|r17_gemini_render\.py|r17b_sdf_render\.py|r19_compare\.py|r20_boards\.py|r20_render\.py|r20_gemini\.sh|make_r3_palettes\.py)#pipeline/tools/rounds/$1#g' \
  pipeline/tools/rounds/* docs/review/gemini/r20_G_r1.md docs/review/r20_brief.md docs/review/r3_art_director_palette.md
# the two tools that compute ROOT from __file__ are one level deeper now (3 -> 4 dirnames)
perl -pi -e 's/^ROOT = os\.path\.dirname\(os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)\)$/ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))/' \
  pipeline/tools/rounds/r19_compare.py pipeline/tools/rounds/make_r3_palettes.py
```
`r20_gemini.sh` still calls `pipeline/tools/gemini_auth.sh` relative to the repo root. That is correct and the perl does not touch it.
Checks:
```bash
git grep -nE 'pipeline[./]tools[./](r15_|r17|r19_|r20_|make_r3)' -- ':!docs/CLEANUP_PLAN.md' ':!pipeline/tools/rounds' ; echo "^ expect nothing"
git grep -nE '^ROOT = ' -- pipeline/tools/rounds        # r19_compare + make_r3_palettes: 4 dirnames
.venv/bin/python -B -c "import pipeline.tools.rounds.r15_mesh_compare, pipeline.tools.rounds.r17_gemini_render, pipeline.tools.rounds.r17b_sdf_render, pipeline.tools.rounds.r20_boards, pipeline.tools.r21_review, pipeline.tools.make_s4_hd2; print('ok')"
.venv/bin/python -B -c "import os, pipeline.tools.rounds.r19_compare as a, pipeline.tools.rounds.make_r3_palettes as b; assert a.ROOT == b.ROOT == os.getcwd(), (a.ROOT, b.ROOT); print('ROOT ok')"
```
(Importing `make_r3_palettes` is safe: its file writes are behind `if __name__ == "__main__"`. **Never run it**, because it rewrites `cw_oatmeal`.)
Commit: `git commit -m "pipeline/tools: move finished-round scripts to tools/rounds/"`

### Phase 4: swordswoman light moves (tracked)

```bash
mkdir -p swordswoman/archive
git mv swordswoman/.scratch_heads swordswoman/archive/scratch_heads
perl -pi -e 's#pixelart/swordswoman/\.scratch_heads/#pixelart/swordswoman/archive/scratch_heads/#g' swordswoman/archive/scratch_heads/r.py
git mv swordswoman/reviews swordswoman/docs/reviews
perl -pi -e 's#`reviews/#`docs/reviews/#g' swordswoman/docs/pixel_cleanup_guide.md                 # 2 lines (11, 12)
perl -pi -e 's#(?<![\w/])reviews/gemini_pixel_critique_base_input\.png#docs/reviews/gemini_pixel_critique_base_input.png#g' \
  swordswoman/docs/reviews/gemini_pixel_critique_base.md                                          # 1 line (3)
```
Checks: `git grep -nE '(^|[^/\w])reviews/gemini' -- swordswoman | /usr/bin/grep -v docs/reviews` prints nothing. `git grep -n scratch_heads` prints only `archive/scratch_heads/r.py`.
Commit: `git commit -m "swordswoman: .scratch_heads -> archive/, reviews -> docs/reviews"`

### Phase 5: `.models` scratch out (local only, not git) + doc refs

```bash
D=swordswoman/archive/scratch; mkdir -p $D
for i in ai_pixel_test landscape designE guide m9crop NE_artist S_artist W_pixel nw se sw qa_ne_r3 qa_nw qa_S qa_sw qa_W \
         gem_test.txt img_test.json models.txt proxy.log p_argon-4.json p_gemini-3-pro-image-preview.json p_gemini-3-pro-image.json \
         p_gemini-3.1-flash-image-preview.json p_gemini-3.5-flash-image.json p_gemini-3.8-flash.json p_gemini-4-argon.json \
         p_gemini-argon-4.json t_argon-4.txt t_gemini-2.5-flash-image.txt t_gemini-3-pro-image-preview.txt t_gemini-3.1-pro-preview.txt \
         t_gemini-3.5-pro.txt t_gemini-3.8-flash.txt t_gemini-3.8-pro.txt t_gemini-argon.txt; do
  mv -n ".models/$i" "$D/" || echo "FAILED $i"; done
diff -rq -x .DS_Store .models/hunyuan_studio reference/3d/hunyuan_studio_research && \
diff -rq -x .DS_Store .models/sota_survey reference/3d/sota_survey && rm -rf .models/hunyuan_studio .models/sota_survey
rm -f .models/.DS_Store
ls -A .models          # expect exactly: hy_omni  mocap  parts  pixelize
perl -pi -e 's#\.scratch/hunyuan_studio/#../reference/3d/hunyuan_studio_research/#g; s#\.scratch/sota_survey\b#../reference/3d/sota_survey#g; s#\.scratch/(ai_pixel_test|landscape)\b#archive/scratch/$1#g' \
  swordswoman/docs/pixel_cleanup_guide.md swordswoman/docs/sota_image_to_3d_2026.md swordswoman/docs/trellis_and_hunyuan_studio.md \
  swordswoman/v2/hy3d/HUNYUAN_VERSIONS.md swordswoman/v2/hy3d/LANDSCAPE.md
git grep -nE '(\.scratch|\.models)/(hunyuan_studio|sota_survey|ai_pixel_test|landscape)' ; echo "^ expect nothing"
git status --short swordswoman/archive   # expect nothing (scratch/ is ignored)
```
The moved scratch scripts (for example `NE_artist/build.py`) keep their old absolute paths. They are dead and are not rewritten.
Commit: `git commit -am "swordswoman docs: point research refs at reference/3d and archive/scratch (.models now holds models only)"`

### Phase 6: indexes

- Rewrite the root `README.md` per section 9. Keep the current snowpeak technical body further down, or move it verbatim to `docs/SNOWPEAK_PIPELINE.md`
  and link it. Moving it is preferred: `git mv` is not possible for part of a file, so create the new file with the old content.
- `00_REVIEW/README.md`: one table, newest first: round | topic | status (current / approved / superseded by rNN / rejected / dead end) | open first.
  Known statuses: r21_s4_hd2 current; r20_blender_base stopped (direction change to S4_hd2); r18/r19 Blender A/B dead end; r17 gemini model;
  r16_face_slim_bangs, r15_face_bangs -> folded into S4_hd; r15_model_gemini; r14_retime; r13_anime_pixel approved; r13_sprite_face superseded by r15;
  r12_illustration rejected; r12_hd_model (the HD model); r11_actions approved -> `releases/S4_actions_v1`; r10_* superseded. Take the rest from each round README.
- `swordswoman/README.md`: (a) change `.scratch` contents to "hy_omni, parts, pixelize, mocap"; (b) add a "Strand status" table with three
  columns (live / support-read-by-live-code / archived) using section 4.2; (c) note that `v2/pixel/palette.json` is a live input; (d) `reviews` -> `docs/reviews`.
Commit: `git commit -m "README index; 00_REVIEW status index; releases + archive READMEs; swordswoman strand table"`

### Phase 7 (optional, separate PR-sized commit): swordswoman v1 + dead v2 strands -> `swordswoman/archive/`

Do this only if the owner accepts that **v1 scripts stop being re-runnable as-is.** 591 v1 code files use cwd-relative paths like
`renders/model_round_9` or `hybrid/lock/...`. Absolute paths get rewritten; relative ones do not. To re-run one later, run from
`swordswoman/archive/v1` with `refs`, `tools/gemini.py` and `.scratch` linked in.
```bash
cd swordswoman
git mv hybrid/ANIM_DIRECTION.md hybrid/STYLE_TARGET.md docs/       # still cited by v2/BRIEF.md + README
mkdir -p archive/v1/tools archive/v2
# .gitignore first, so the 1.1 GB of ignored hybrid/renders output does not suddenly show as untracked (13 lines)
perl -pi -e 's#^swordswoman/(hybrid|pixel|renders|concept|model)/#swordswoman/archive/v1/$1/#; s#^swordswoman/v2/anim/#swordswoman/archive/v2/anim/#' ../.gitignore
git mv concept model pixel hybrid archive/v1/
mv renders archive/v1/renders                                        # 0 tracked files: plain mv
git mv tools/hybrid tools/pixel archive/v1/tools/
git mv v2/pixel_E v2/animate v2/mastersF archive/v2/
mv v2/anim archive/v2/anim                                           # 0 tracked files: plain mv
# absolute-path rewrite over tracked AND untracked text files (expect ~340 files; record the list for rollback)
P=/Users/waylonhuang/Documents/other/pixelart/swordswoman
/usr/bin/grep -rlI --exclude-dir=.venv --exclude-dir=.scratch --exclude-dir=__pycache__ -E \
  "$P/(concept|model|renders|pixel|hybrid|tools/hybrid|tools/pixel|v2/pixel_E|v2/animate|v2/mastersF|v2/anim)/" . > /tmp/reorg_p7_files.txt
wc -l /tmp/reorg_p7_files.txt
tr '\n' '\0' < /tmp/reorg_p7_files.txt | xargs -0 perl -pi -e '
  s#(/pixelart/swordswoman/)(concept|model|renders|pixel|hybrid)/#$1archive/v1/$2/#g;
  s#(/pixelart/swordswoman/)tools/(hybrid|pixel)/#$1archive/v1/tools/$2/#g;
  s#(/pixelart/swordswoman/)v2/(pixel_E|animate|mastersF|anim)/#$1archive/v2/$2/#g'
perl -pi -e 's#hybrid/(ANIM_DIRECTION|STYLE_TARGET)\.md#docs/$1.md#g' v2/BRIEF.md README.md
find . -name __pycache__ -path './archive/*' -prune -exec rm -rf {} +
cd ..
git add -A swordswoman .gitignore
git status --short | /usr/bin/grep -v '^R ' | head -40              # expect only M (rewritten files) and the 2 .md renames
```
These patterns cannot hit live paths: `swordswoman/pixel/` does not match `swordswoman/v2/pixel/`, and `v2/anim/` does not match `v2/anim_cut/`
or `anim_redraw/`. Then run all of section 7 again. Commit: `git commit -m "swordswoman: archive v1 (concept/model/pixel/hybrid/renders/tools) and dead v2 strands"`

## 6. What breaks (by move), with evidence

| Move | References | Handling |
|---|---|---|
| `releases/HERO` rm | 4 occurrences in 3 docs (START_HERE, CLEANUP_PLAN, swordswoman study) | history docs; left |
| H1 -> archive | 12 occurrences / 5 files | 2 rewritten (docs/review/pixel). START_HERE moves with the archive. CLEANUP_PLAN and the study are left as history. |
| `out/` untrack | 31 `out/variants` + 7 `out/jump` mentions in 23 docs; `server.py`/`build.py` write to `out/` | the files stay on disk, and the pipeline keeps writing there (ignored). Clones lose them on pull (regenerate with `pipeline.build`). |
| `out/boards` -> archive | 19 occurrences / 12 files | 6 docs rewritten. `README.md` + `board.py` are examples of new output and are left. |
| `blender/` -> archive | 1 file (swordswoman study) | left |
| `START_HERE.md` -> archive | 4 occurrences / 2 files | left |
| tools -> `rounds/` | imports: r17 x2 -> r15/r17 (rewritten); docstrings in the moved files; 3 docs (r20 x2, r3 palette) rewritten; ROOT depth in 2 files fixed | `r21_review`, `make_s4_hd*`, `r13_bust` untouched |
| `.gitignore` anchoring | the root `work/` was hiding 6 intended g96 JSONs | they get added. Other `swordswoman/**/work/` stay ignored via the new rule. |
| `.scratch_heads`, `reviews` | 1 + 3 refs | rewritten |
| `.models` scratch | 5 doc refs (`.scratch/{hunyuan_studio,sota_survey,ai_pixel_test,landscape}`) | rewritten. 0 code refs. `hy_omni/pixelize/parts/mocap` untouched. |
| phase 7 | ~340 files with absolute refs (rewritten), 13 `.gitignore` lines (rewritten), 2 md refs to ANIM_DIRECTION/STYLE_TARGET (rewritten), 591 v1 files with relative refs (**not** rewritten, so the dead code is not re-runnable as-is) | accepted, documented in `archive/README.md` |
| **Not changed anywhere** | `pipeline/*.py`, `data/**`, `overrides/**`, `editor/**`, `00_REVIEW/<round>` names, `docs/review/` layout, every live swordswoman strand, `.models/{hy_omni,parts,pixelize,mocap}`, both venvs, both symlinks | so build IDs, the editor and the swordswoman abs paths are all intact |

## 7. Verification checklist (after every phase from 2 on, and fully after 6 and 7)

1. **Git integrity.**
   `git diff -M --summary pre-reorg-2026-10-28 HEAD | /usr/bin/grep -vE 'rename .*\(100%\)|delete mode .* out/(variants|jump)/'` shows only
   the expected creates (READMEs, 6 g96 JSON, palette.json, docs/SNOWPEAK_PIPELINE.md), the HERO + 2 `.DS_Store` deletes, and renames below
   100% for exactly the rewritten files. `git ls-files out | wc -l` = 0. `git ls-files | /usr/bin/grep -c DS_Store` = 0.
2. **Build IDs unchanged** (proves no hashed input was touched):
   ```bash
   .venv/bin/python -B -c "from pipeline.build import build_id
   for v in ('S4_hd','S4_hd2','S4_halfup_bow'):
       for a in ('idle','walk','run','jump_sc'): print(v, a, build_id(a, v)[0])" | diff - /tmp/reorg_base/build_ids.txt && echo IDS-SAME
   ```
3. **Snowpeak build (~5 min):** `.venv/bin/python -B -m pipeline.build --variant S4_hd2 --anim idle --verify` exits 0, and its verify/QA lines
   match `/tmp/reorg_base/build.log` (`diff <(/usr/bin/grep -iE 'identical|qa' /tmp/reorg_base/build.log) <(... new log ...)`). Then
   `diff -r /tmp/reorg_base/S4_hd2__idle out/variants/S4_hd2__idle && echo OUT-SAME` (the outputs have no timestamps or absolute paths, so the whole tree must match).
4. **Editor:**
   ```bash
   PORT=8799 .venv/bin/python -B -m pipeline.server & S=$!; sleep 2
   curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8799/editor/            # 200
   curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8799/editor/editor.js   # 200
   curl -s 'http://127.0.0.1:8799/api/state?anim=jump' | head -c 120; echo           # JSON (out/jump is still on disk)
   kill $S
   ```
   (Do not test `&variant=` here. `server.py:_out()` maps a variant to `out/variants/<variant>` and not `<variant>__<clip>`. That bug is
   already known from CLEANUP_PLAN section 5 and is unrelated.)
5. **Snowpeak tools:** the phase-3 import and ROOT checks pass. `.venv/bin/python -B -c "import pipeline.board, pipeline.publish, pipeline.pixelreview, pipeline.override, pipeline.pixgrid"` succeeds.
6. **Swordswoman pixelize** (from `swordswoman/`):
   ```bash
   .scratch/pixelize/pixeloe/venv/bin/python -I v2/pixelize/tools/pz.py EC0 S 96 --pal v2/pixelize/palette.json --out /tmp/x
   # prints "EC0_S_96 ok (128, 128)"
   cmp /tmp/x/EC0_S_96.json /tmp/reorg_base/pz/EC0_S_96.json && echo PZ-JSON-SAME
   ```
   The png/txt are not deterministic (PixelOE), so just open `/tmp/x/EC0_S_96.png` and check it looks like the baseline.
7. **Swordswoman rig H2** (from `swordswoman/`):
   ```bash
   rm -rf /tmp/r
   .scratch/hy_omni/venv/bin/python -I v2/g96/scripts/repro_h.py v2/hy3d/rigs/H2/parts/spec_solved.json v2/hy3d/partsAB4f v2/hy3d/best/skel.txt /tmp/r
   .scratch/hy_omni/venv/bin/python -I /tmp/reorg_glbcmp.py /tmp/r v2/hy3d/rigs/H2/parts
   ```
   Expect 10 x BYTES-SAME, `torso.glb` GEOM-SAME (same as at baseline), exit 0. Also
   `/tmp/reorg_glbcmp.py /tmp/r /tmp/reorg_base/rigH2` gives all BYTES-SAME.
8. **Links/paths:** `ls -L swordswoman/.scratch/hy_omni/venv/bin/python reference/3d/best/raw_mvD4_s5.glb` both resolve.
   `test -f swordswoman/v2/pixel/palette.json`. After phase 7, from swordswoman: `/usr/bin/grep -rlI --exclude-dir=.venv --exclude-dir=.scratch -E "/pixelart/swordswoman/(concept|model|renders|pixel|hybrid|tools/hybrid|tools/pixel|v2/pixel_E|v2/animate|v2/mastersF|v2/anim)/" . | wc -l` = 0.
9. **Ignore sanity:** `git status --short` is clean (except the 2 known untracked S4_hd2_idle files). `git status --short --ignored | /usr/bin/grep -c '^!!'` is
   about the same as before. Phase 7 must not add `?? swordswoman/archive/...` lines for the old ignored output.
10. **GitHub:** after pushing the branch, open `README.md`, `00_REVIEW/README.md` and `archive/README.md` on GitHub and click every link.

## 8. Rollback

- Phases 1–4 and 6: `git switch merge-swordswoman` (the branch is untouched) or `git reset --hard pre-reorg-2026-10-28` on the reorg branch.
  Phase 1 used `git rm --cached`, so `out/` is still on disk either way.
- Phase 5 (not in git): `mv swordswoman/archive/scratch/* .models/`. The deleted `hunyuan_studio`/`sota_survey` are byte-copies of
  `reference/3d/{hunyuan_studio_research,sota_survey}`: `cp -R` them back.
- Phase 7: before switching branches, reverse the plain `mv`s (`archive/v1/renders -> renders`, `archive/v2/anim -> v2/anim`). Then reverse the
  perl on the untracked files, using the paths in `/tmp/reorg_p7_files.txt` mapped to their new locations, with the substitutions swapped
  (`archive/v1/X/ -> X/`, `archive/v1/tools/X/ -> tools/X/`, `archive/v2/X/ -> v2/X/`). Finally `git reset --hard` to the phase-6 commit, and
  `mv` back any ignored directories git left behind in `swordswoman/archive/`.

## 9. Proposed root `README.md` (index)

```markdown
# pixelart: chibi sprite projects

Two projects share this repo. **Snowpeak lives at the repo root** (its pipeline must be run with cwd = repo root);
**Swordswoman is self-contained in `swordswoman/`** (run its scripts with cwd = `swordswoman/`; many use absolute paths).

## Projects
| Project | Where | Current best | Status |
|---|---|---|---|
| Snowpeak girl (3D->pixel pipeline + editor) | `pipeline/ data/ overrides/ art/ editor/` | `releases/S4_hd_actions_v1/` (13 clips, approved) | S4_hd2 refinement: idle/walk/run in `00_REVIEW/r21_s4_hd2/` |
| Swordswoman (Hunyuan3D rig -> 96 px pixel) | `swordswoman/` | `swordswoman/v2/m96/` masters (M96 READY) | animation in progress (see `swordswoman/README.md`) |

## Look here first
- Reviews: `00_REVIEW/README.md` (round index, newest first) · Swordswoman hub: `swordswoman/v2/REVIEW/index.html`
- Releases: `releases/README.md` · Decisions: `docs/DECISIONS.md` · Team reviews: `docs/team_review/<date>/`

## Run
| Task | Command (cwd) |
|---|---|
| Build a clip | `.venv/bin/python -m pipeline.build --variant S4_hd2 --anim idle --verify` (root) |
| Editor | `.venv/bin/python -m pipeline.server` -> http://127.0.0.1:8777/editor/ (root) |
| Pixelize | `.scratch/pixelize/pixeloe/venv/bin/python -I v2/pixelize/tools/pz.py ...` (swordswoman/) |
| Rig H2 | `.scratch/hy_omni/venv/bin/python -I v2/g96/scripts/repro_h.py ...` (swordswoman/) |

## Repo map
| Path | What | In git |
|---|---|---|
| `pipeline/` (`tools/`, `tools/rounds/`) | snowpeak code; current tools; finished-round scripts | yes |
| `data/` `overrides/` `art/` | snowpeak sources (hashed into build IDs) | yes |
| `editor/` | browser pixel editor | yes |
| `00_REVIEW/` `releases/` | review rounds r10–r21; frozen deliverables | yes |
| `docs/` | decisions, schema, research, review history (`docs/review/` path is cited by data, do not move) | yes |
| `reference/3d/` | 3D generator outputs (swordswoman) | yes |
| `swordswoman/` | second project (`archive/` inside for its dead ends) | yes (bulk ignored) |
| `archive/` | snowpeak dead ends (H1 releases, old boards, r18 Blender sources, START_HERE) | yes |
| `builds/` `out/` `work/` | generated / scratch | no |
| `.venv/` `.models/` | snowpeak venv; weights+venvs (`hy_omni parts pixelize mocap`, ~41 GB) | no |

## Conventions
- New dirs: lowercase snake_case. Review rounds: `rNN_topic`. Variant IDs keep their case (`S4_hd2`).
- Generated output is never committed; dead ends go to `archive/`, nothing is renamed in `00_REVIEW/` or `docs/review/`.
- Never edit `pipeline/*.py`, `data/**`, `overrides/**` for housekeeping: it changes every build ID.

## Snowpeak pipeline details
See `docs/SNOWPEAK_PIPELINE.md` (the previous README body).
```

## Appendix A: Option A recipe (not scheduled)

This is for reference only, if a symmetric `projects/` layout is ever wanted. It must be its own branch, after phases 1–6.
1. `git mv pipeline editor data overrides art 00_REVIEW releases docs archive projects/snowpeak/` plus plain `mv builds out work .venv projects/snowpeak/`,
   then recreate the venv (`python3 -m venv projects/snowpeak/.venv && …/pip install numpy pillow`). Build IDs are unchanged (ROOT-relative hashing);
   check with section 7.2 run from `projects/snowpeak`.
2. `git mv swordswoman projects/swordswoman`, then run `ln -sfn ../../.models projects/swordswoman/.scratch` and `ln -sfn ../../projects/swordswoman/v2/hy3d/best reference/3d/best`.
3. One perl over every text file under `projects/swordswoman` (tracked + untracked, excluding `.venv`, `.scratch`, `__pycache__`):
   `s#/pixelart/swordswoman/#/pixelart/projects/swordswoman/#g` (expect 1403 files / 2764+ tracked occurrences), plus `.gitignore`:
   `s#^(!?)swordswoman/#$1projects/swordswoman/#` (50 lines) and `s#^/(builds|out|work)/#/projects/snowpeak/$1/#`.
4. Recreate `projects/swordswoman/.venv` (uv, Python 3.13, numpy pillow scipy). Delete the 2 stale `.pyc` files.
5. Expect committed swordswoman JSON outputs that embed absolute paths (248 tracked JSON files) to differ from fresh runs. Update every doc,
   memory note and agent prompt that says "cwd = repo root".
