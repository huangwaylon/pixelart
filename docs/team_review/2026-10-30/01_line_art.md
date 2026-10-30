# 01 · Line art review: swordswoman skinned-rig chain (2026-10-30)

Reviewer role: senior pixel artist and technical artist. Scope: line quality only, meaning outline, interior lines, weight, slopes and temporal stability. Colour and shading are mentioned only where they change how heavy a line reads.
Everything referenced here is in `docs/team_review/2026-10-30/line_art/`:
- Metric script: `lamet.py`
- Prototype: `proto_vecline.py`
- Numbers: `metrics.json`, `proto_metrics.json`, `proto_table.txt`
- Boards: `board_audit_{S,SE,E}.png`, `board_proto_idle_{S,SE,E}.png`, `board_proto_walk_SE.png`, `board_zoom_walkSE_f03.png`

## TL;DR
The round-10 outline is **closed and mostly 1 px**. That part works. What makes it look unpolished is three things:
1. **Irregular slope runs on every curve.** The 1-2-1 and 1-3-1 zig-zags on the sleeves, legs and hair come from threshold-rasterising the 3D silhouette. The chain has 6.6–8.8 zig-zags per frame against 4–5 in the masters, and only 38–44 % of curve stretches have clean run progressions against 62–65 % in the masters (S, SE).
2. **2–3x more interior K line than the masters, and it boils.** There are 29–48 interior K px per frame against 11–18 in the masters, and 26–82 % of those pixels pop in or out between frames.
3. **Hair reads as a 3–4 px dark blob, so the outline loses its weight hierarchy.** The hair is filled with `h` and `d` (the sock sheen colour is leaking into the hair), so the K outline melts into it.

A prototype that **vectorises the 8x silhouette and re-rasterises it at 1x with clean-slope runs** cut zig-zags from 6.7 to 0.7 per frame (–90 %) and redundant L-corners from 8.9 to 4.0. It raised clean-run stretches from 0.48 to 0.77, which is above the masters, with no outline gaps. This is the fix I recommend integrating for the outer line. Interior lines need the same treatment as a follow-up.

## 1. Audit

The metrics are per-frame means. Idle has 12 frames and walk has 8; the masters are single frames. "mono" is the share of curve stretches with clean runs: monotone like 1-1-2-3, or a strict alternation like 1-2-1-2. "boil" is the share of K px that appear or disappear rather than moving with the body (best global shift, ±1 px tolerance).

| set | redundant L | 1-3-1 zig | mono | sil. gaps | 2x2 K clumps | interior K | orphan K | K weight 1/2/3+ px | boil sil / int |
|---|---|---|---|---|---|---|---|---|---|
| master SE | 13 | 4 | **0.65** | 0 | 11 | **16** | 7 | 65/16/20 % | n/a |
| r10 idle SE | 7.5 | 8.4 | 0.38 | 0 | 11 | 48 | 5.8 | 67/16/17 % | 0.14 / 0.34 |
| r10 walk SE | 7.1 | 6.6 | 0.44 | 0.1 | 6 | 42 | 6.5 | 67/14/19 % | 0.26 / 0.26 |
| hybrid idle SE | 2.5 | 9.4 | 0.29 | **21** | **51** | 32 | 6.8 | 53/18/22 % (8 % no line) | 0.14 / 0.47 |
| master S | 3 | 5 | 0.62 | 0 | 10 | 18 | 4 | 71/12/17 % | n/a |
| r10 idle S | 6.1 | 8.8 | 0.38 | 0.1 | 14 | 29 | 5.8 | 68/14/18 % | 0.13 / 0.46 |
| master E | 6 | 5 | 0.44 | 0 | 9 | 11 | 5 | 67/13/20 % | n/a |
| r10 idle E | 7.0 | 6.8 | 0.45 | 0.7 | 10 | 32 | 3.2 | 65/14/20 % | 0.09 / 0.47 |

Round 4 sits between the two, with more L-corners (9–15). All rows are in `metrics.json`.

**Findings, by checklist item:**
- **Continuity: OK in round 10.** The silhouette is closed in K (0–0.7 gap px). The **hybrid fails here**: 14–33 silhouette px per frame are not K. Most are hair edges in `h`/`H`, which is an accidental sel-out on the darkest material, the one place sel-out does not help. The hybrid also has 22–88 2x2 K clumps, from heavy K masses in the hair (orange on `board_audit_SE.png`).
- **Weight: OK on paper, wrong to the eye.** The K run measured inward is 1 px about 67 % of the time in the chain and the masters alike. But counting the visually dark colours `K|h|D`, 45–49 % of SE silhouette px are 3+ px dark. Hair and socks merge with the outline, so the outline only reads on the red and skin areas. This is a colour issue that shows up as line weight. In r10 the hair fill is mostly `h`/`d` (`d` is the sock sheen), where the masters use `H`/`g`/`L` bands.
- **Doubles / L-corners.** The chain removes L-corners on the outer ring only. The limb-width repair, orphan fold-in and interior lines then put 6–11 redundant elbows back per frame, usually where an interior line meets the outline (hand, legs, bow). The masters are not pixel-perfect either (3–13), so this is polish, not the main problem.
- **Jaggies: the main problem.** In `board_zoom_walkSE_f03.png` the sleeve diagonals in the chain alternate 1-2-1-3 runs, and the sock edges carry single 1 px steps on otherwise vertical runs. The cause is the fill: it is a coverage-≥0.5 threshold of a 3D silhouette, and the outline is just its 4-dilation. Nothing in the chain ever decides a slope.
- **Interior lines: mostly not deliberate.** 67–96 % of interior K in r10 sits in the top 40 % of the figure, the hair and face mass, as 1–3 px fragments left by the textured head plus the `clean_orphans` "boxed in by K, fold into K" rule. These fragments boil: 34–47 % of interior K changes per idle frame, even though idle barely moves. The deliberate lines are leg|leg, sleeve|body, hand|sleeve and eyes. Those are fine.
- **Outline colour.** It is uniform K `#160c0d` all round, as in the approved masters. Snowpeak locked 1 px sel-out over a dark coloured outer line (`docs/review/r10_outline_AD.md`). For this character, sel-out only makes sense on the red and skin lit edges (see the prototype variant). Never use it on hair or socks, where it produces the hybrid's broken edges.
- **Banding / pillow shading.** None in the silhouette sense. There is one real doubling: the `R` shadow band on the shadow-side sleeve edge runs exactly parallel to the K line for 8–10 px. That reads as a 2 px line at 1x on SE and E.

## 2. Research (short)
- **Pixel-perfect stroke**: a 1 px line is 8-connected with no orthogonal elbows. Drop any pixel whose two neighbours already touch diagonally (Aseprite's "pixel-perfect" mode).
- **Slope runs**: clean lines use uniform runs: 1:1, 1:2, 1:3, 2:1, and so on. Curves use monotone progressions (1-1-2-2-3-4, then back down), never a run that is longer or shorter than both its neighbours (1-3-1, 3-1-3). A convex smooth curve digitises naturally to monotone runs. The jaggies come from thresholding pixel coverage instead of drawing a curve.
- **Sel-out**: dark on the shadow side, one ramp step darker than the fill on the lit edge. It works when the lit fill contrasts with the background. Snowpeak adopted it (`docs/research/outline_techniques.md` §4).
- **How 3D-to-pixel productions get clean lines:**
  - **Dead Cells** (Motion Twin's 3D-to-pixel pipeline) renders at target resolution with no AA, uses cel shading and rim light, and has no outline. Cleanup is minimal because the line is not the carrier.
  - **t3ssel8r**-style real-time work renders at native resolution, gets edges from depth/normal/ID discontinuities in screen space, and chooses which side of the edge gets the line. It is stable because the edges come from geometry, not colour.
  - Studios that need hand-drawn-looking lines (for example the 3D-to-sprite workflows on GBA/DS) trace the silhouette as a curve and rasterise it with a stroke rule. Then a hand cleanup pass of about 5–15 min per frame goes on key poses only, while in-betweens inherit the cleanup.
  - Every approach that works decides the line **from geometry, at target resolution, with a stroke rule**. The current chain decides it from coverage, then patches it with rules.
- **Cleanup budget, realistically**: 8 directions × about 60 frames ≈ 480 frames. Hand-polishing everything (about 10 min each) is about 80 h. If the automated line passes the gates in §4, cleanup shrinks to key poses only (about 8 dirs × 6 keys × 5 min ≈ 4 h per action set).

## 3. Prototype: vector silhouette, clean-slope rasterisation (`proto_vecline.py`)
This is a post-process on 7 built r10 frames (walk SE f0–3 and idle S/SE/E f0). There is no rebuild, and the fill colours stay the chain's.
1. The silhouette contours (outer, plus arm|body holes ≥6 px²) are traced on R's 8x alpha from the guide pass (`work/<act>/<DIR>/<act>_<DIR>_fNN_guide.png`). The alpha is eroded by 4 hi-res px first so the silhouette keeps the chain's volume.
2. The contour is Gaussian-smoothed along the curve (σ 0.9 px). Sharp corners (interior angle <100°: bow lobes, hair tips, toes) are pinned to the raw shape. The result is simplified with Douglas-Peucker (ε 0.8 px).
3. Each segment is rasterised with **uniform runs** when its slope is within 25 % of a clean 1:k or k:1 ratio, and with Bresenham otherwise. Drift is re-aimed by the next segment. The whole path is then made pixel-perfect.
4. Inside = the 4-connected regions enclosed by the line with coverage ≥0.5. Colours come from the chain, nearest chain colour where the silhouette grew. Interior K outside the textured head is skeletonised and made pixel-perfect, and pieces under 4 px are dropped; the head keeps its pixels.
5. Optional sel-out variant: on lit top/left edges, red, skin and obi lines become one ramp step darker than the fill.

| 7 frames, mean | redundant L | 1-3-1 zig | mono | gaps | clumps | boil sil / int (walk SE) |
|---|---|---|---|---|---|---|
| r10 chain | 8.9 | 6.7 | 0.48 | 0.1 | 7.1 | 0.29 / 0.17 |
| **prototype** | **4.0** | **0.7** | **0.77** | 0 | 9.1 | 0.31 / 0.24 |
| masters (S/SE/E) | 7.3 | 4.7 | 0.57 | 0 | 10 | n/a |

The parameter sweep is reproducible with env `MODE=poly|dense|clean`, `EPS`, `SIG`, `SHRINK`, `PIN`. Two notes from it:
- Bresenham polylines alone ("poly") only got zig-zags to about 2.2 with mono still at 0.48.
- Digitising the smoothed curve densely ("dense") did not help either. The clean-slope rule is what moves mono.

**What it looks like** (`board_proto_idle_SE.png`, `board_proto_walk_SE.png`, `board_zoom_walkSE_f03.png`):
- Sleeves and socks become crisp, deliberate diagonals and verticals.
- The sleeve reads as a clean lozenge. That is the true 3D shape, and it shows the chain's lumps had been hiding it.
- The silhouette boil stays about the same as the chain's. **It is not yet better in motion**: smoothing is per frame, with no temporal term.
- **Known regressions**:
  - The hair silhouette loses some strand jaggedness (character).
  - The bow|hair separation is weaker.
  - Thinned interior lines boil a little more, and orphans rise to up to 11 on one frame. The skeleton fragments the chain's interior fragments further, which confirms that interior lines must come from geometry, not from cleaning up the chain's K.
  - Sel-out on red and skin reads well on mid-grey but softens the silhouette. Keep it optional and decide on the game background.

## 4. Recommended line-art spec
**Weights**
- Outer silhouette: **exactly 1 px, closed, pixel-perfect**.
- Interior lines: 1 px, only where listed below.
- 2 px K is allowed only at deliberate accents of at most 3 px: under the chin, the sole contact, and lash or eye masses.
- Never let K run parallel to a near-black fill for 4 px or more. Lift the adjacent hair/sock fill to `H`/`d`, so the outline keeps its hierarchy.

**Colours**
- Outer line is K by default, matching the approved masters.
- Optional sel-out on lit top/left edges of red, skin and obi only, using `E→R`, `s→S`, `O→o` (one step darker, never transparent).
- Never sel-out hair, boots or socks.
- No outward AA.

**Interior lines allowed only at these boundaries**, coming from depth/part-ID discontinuities in the 8x passes:
- leg|leg, arm or sleeve over body, hand|sleeve, hair|face (bangs edge), bow|hair, chin|neck
- Eyes and lashes come from the face layer.
- No interior K in the hair mass. Use `h` for strand lines instead.
- Minimum length 4 px, except eye pieces.
- Interior lines go on the **far** side of the occlusion edge (the chain already does this).
- On 40–50 px-tall parts, prefer the back part's shadow shade over K (Snowpeak rule).

**Slope rules**
- Outer and interior lines are drawn as polylines of clean-ratio segments (1:1, 1:2, 1:3, 1:4 and their inverses). Bresenham is the fallback for steep or shallow residuals.
- Curves must have monotone run progressions.
- No single-pixel run that is longer or shorter than both neighbours by 2 or more.
- Pinned corners are exempt.

**Gates** (add `lamet.metrics` to `gates.json`; fail the clip if any frame misses):
- silhouette gap = 0 (sel-out pixels excluded)
- redundant L ≤ 3
- 1-3-1 zig ≤ 1
- mono ≥ 0.70
- 2x2 K clumps ≤ master + 2
- interior K ≤ 1.3 × master for that view
- orphan K = 0 outside the face
- silhouette boil ≤ 0.12 on idle, ≤ 0.25 on walk/run
- interior boil ≤ 0.20

## 5. Integration plan and effort
1. **Outer line (1.5 d)**:
   - Replace step 4 of `pixel_chain.frame()` (the `ring = 4-dilation of fill` block) with `vec_line()` run on the 8x alpha.
   - Fill = `inside` ∩ the chain's labels.
   - Run the limb-width repair *before* the line, and never convert fill to K after the line. That conversion is where the post-hoc elbows come from.
2. **Temporal (1 d)**: smooth the contour vertices across frames.
   - Option A: match DP vertices by rest-space position (the `rpos` pass already exists) and low-pass them.
   - Option B: hysteresis that keeps last frame's line pixel if the new curve passes within 0.5 px of it.
   - Target: silhouette boil ≤ the gates above.
3. **Interior lines (2 d)**:
   - Extract open polylines where the part/lid ID changes *and* depth jumps more than DTHR.
   - Keep the far side, apply the same smooth, DP and clean-slope rasteriser, and drop pieces under 4 px.
   - Retire the `clean_orphans` "fold into K" behaviour outside the face.
4. **Hair/sock value fix (0.5 d, with the colour owner)**: stop `d` from reaching hair cells, and add the dark-adjacency rule from §4 Weights.
5. **Gates + boards (0.5 d)**: `lamet.py` is already written, so this is wiring.
6. **Hand cleanup**: key poses only, about 4 h per action set once the gates pass.

The total is about **5.5 dev-days** plus one review round. Risk: corner pinning needs a per-material table (hair and bow get looser pinning) to keep the masters' strand character. Check that against `board_proto_idle_SE.png` before scaling up.
