# FX strand NOTES (Pokemon/PMD-style VFX library), 2026-10-26

## Step 1: setup + refs
- Read BRIEF, STYLE_GUIDE (palette pk_palette.json, 48 px figure in 64x64 cell, slash smear 40 ms, dash smear 40 ms), style/NOTES.
- Refs (untrusted, study only): fx/refs/ = 20 pokeemerald battle-anim sprites (cut, slash, claw_slash, scratch, swipe, air_slash, impact, hit, punch_impact, cross_impact, slam_hit, sparkle_1, yellow_star, speed_dust, smoke, sweat_drop, sweat_bead, anger, movement_waves, flying_dirt) + 4 field effects (ground_impact_dust, emotion_exclamation, ash_puff, small_sparkle) from raw.githubusercontent.com/pret (already allowlisted; no new domains needed). Study board fx/refs_board.png (3x, bg index not transparent).
- Study notes: Gen3 cuts/slashes = crescent, thick-to-thin taper, 2-3 light bands, thin darker rim on one edge, no black outline; hit/impact = 6-10 point starburst, white/yellow core, orange rim, ring breaks open on the last frame; smoke/dust = round lumpy puffs, 2-3 tones (cream/grey) with darker underside, no black outline; sweat drop = small teardrop, blue with white glint and dark outline; emotes (!) have black outline + white fill.
## Step 2: tooling + slash drafts
- fx_palette.json (14 colours: K W p n b | y o | u U g | c B | a A; K/W/n identical to pk_palette).
- tools/fxlib.py: multi-frame char-map format ('# frame N MSms'), render/gif/lint, outline(), afterimage(rgba, alpha step 1/.75/.5/.25, 2tone or 1tone), whiteflash(rgba).
- tools/gen_slash.py: procedural crescent drafts (ellipse path, thin tail -> thick lead, W outer edge / p / n / b inner rim; f1 thins+breaks, f2 fragments) -> draft/slash_{h,diag,over}.txt, board draft/board_slash.png. Used as layout guides for the Opus pixel artist.
## Step 3: TASK A slash smears (hand-cleaned)
- maps/slash_{h,diag,over}.txt + .anchors.json; 3f 40/60/60; colours W p n b only; lint 0 isolated.
- Construction: moon crescent = outer ellipse minus offset inner circle (work/crescent.py, convex edges -> even step runs) + 1 px W tail along the outer edge; then every row hand-fixed via span specs (work/slash_*.spec -> work/paint.py): monotone inner/outer runs, consistent bands (W 2 px outer, p, n, 1 px b rim only where t>=7), pointed lead tips, 3->2->1 tail taper.
- f1: thickness ~4-5, tail removed, gap splits into 2 pieces with slanted ends; f2: 3 W+p slivers along the outer edge near the lead.
- Sizes: h 42x16 arc (chest, cell y33-48); diag 30x33 (above-behind head -> low front y53); over 38x41 (over the bow y13 -> shin y54; translated +3,+2 so it clears the face).
- Context check: png/slash_context.png (f0/f1 over C_r3, red px = pivot). Board: png/board_slash.png.
## Step 4: TASK B impact + hurt
- work/taskB.py (hand-placed pixel lists / stamps, 8-fold mirror for the spark) -> maps/{hit_spark,hit_flash,hurt_star,sweat_drop}.txt + anchors.
- hit_spark 21x21 (40/60/80): f0 19px W core + 4 long W/y/o cardinal rays + 4 short y/o diagonals; f1 W/y ring (hollow) + detached rays; f2 6 y/o sparks + 2 W glints.
- hit_flash 15x15 (40): W disc d11, p rim upper-left / n rim lower-right, 4 cardinal spikes.
- hurt_star 22x16 (60/120), pivot (11,15) bottom centre: 9px + 2x7px K-outlined y/o stars with W glint, W flash spikes; f1 7px stars + 3x3 twinkles scattered.
- sweat_drop 9x11 (120/120/200): 7x9 c/B/W/K drop, slides 0/1/3 px, f2 squashed 9x8; offset_from_head_top [14,2] (cell 46,16, beside front of hair).
- Context: png/taskB_context.png; board png/board_taskB.png. Lint: 0 isolated except 2 deliberate glints in hit_spark f2.
## Step 5: TASK C dust
- maps/dust_{step,land,skid}.txt + anchors (attach feet, ground_y). Colours u/U/g only, no K. step hand-drawn; land/skid via hand-drawn puff stamps placed in painter's order (work/taskC.py).
- step 14x7 (80/100/120), pivot (11,6), layer over_character (heel puffs hide behind the foot otherwise). land 36x10 (60/80/100/120), widths 16/24/30/33, pivot (18,9), behind. skid 28x9 (70/70/90), pivot (25,8) = trail front at heel, heel_offset_from_feet [-4,0], behind, pebbles g/Ug chips.
- Context: png/taskC_context.png; board png/board_taskC.png; lint 0 isolated.
## Step 6: TASK D dash + jump
- work/taskD.py (line specs + mirrored swish stamps + ellipse outline from work/ell.py) -> maps/{speed_lines_long,speed_lines_short,jump_whoosh,land_ring}.txt + anchors. Colours W/p/n (+u ring); lint 0 isolated.
- speed_lines_long 22x29 (40/40): f0 5 lines 13-18 px (one 2 px wedge), f1 4 lines shifted/re-lengthed; W~35% head, p, n tail. short 12x29 same rows, 5-9 px. attach body_centre (cell 32,40), pivot (21,14)/(11,14) placed at body_centre+[-13,-2] = cell (19,38) behind her back; lines span cell y24-52.
- jump_whoosh 31x18 (50/80), pivot (13,5) -> cell 32,62: 3 vertical lines below feet (6/8/6) + 2-2-2 W/p/n ground flicks; f1 9 px lines 2 px lower, gap-broken, flicks p/n drift out+up.
- land_ring 32x12 (60/80/100), pivot (16,5): ellipses 14x5, 24x8, 30x10 (far arc p, front u + n underside); f2 angle-cut p/n dashes.
- afterimage(): checked with C_r3 (pk palette) RGBA -> a/A two-tone ghost at alpha 0.5, works unchanged. Context: work/ctxD.png; board png/board_taskD.png.
## Step 7: round-1 critique (crit/r1_argon.txt, crit/r1_opus.txt) + lead size switch
- Argon: slash 3-4, hit_flash 3, spark 5, hurt_star 5, sweat 4, dust 5-6, speed lines 2, whoosh 3, ring 3. Opus: slash 5-6, flash 4, spark 7, hurt_star 4, sweat 7, dust 5, speed 5, whoosh 3, ring 6.
- Shared faults: 1 px hairline slash tails with uneven steps; slash_h too thin (bowl); f1 = erased gap instead of thinning; hit_flash soft AA blob -> hard 4/8-point star; spark rays need 2 px roots + thicker ring; hurt_star stray grey marks under stars; dust puffs flat/no rim + chip noise; speed lines uniform UI rules; jump_whoosh reads as glyphs; ring f0 too small.
- Rejected: Argon's bronze outline for hurt stars (sprite + PMD emotes use black), "cut speed_lines_short" (required by the brief).
- Lead: primary target is now the PMD-true 32 px figure (style/tests/A_r3, 40x40 cell); 48 px set is secondary. r1 48 px maps moved to maps48/NAME_48.txt; r1 renders to r1/.
## Step 8: TASK A2 slash smears redrawn for the 32 px figure (A_r3 / A_slash_f*)
- maps/slash_{h,diag,over}.txt + anchors, 3f 40/60/60, W/p/b (+n tail only); hand-typed rows in work/r2a/hand.py (gen.py/paint2.py were drafts only; outer-edge runs hand-set, monotone inner b rim).
- Sizes: h 28x8 (flat crescent, belly 3->4->5 px at lower-right near lead, cell y31-38); diag 23x24 (from just above front of hair, top y13 -> lead tip 46,36); over 26x30 (top y7, tail >=2 px above bow, side runs 2-3-6-3-3 so no straight wall).
- Profile: 1-2 px n/W tail tip -> 2 px W+n -> 3 px W/p/b -> 4-5 px WWWpb near lead -> 4,3,2,1 pointed lead. f1 = same outer edge, 2-3 px pW(W), tail retracted ~35%; f2 = 4 lens chips (W/pW/pW/W) evenly spaced along the outer arc toward the lead.
- Anchors: pivot = sword hand, cell_offset [44,32] in the 64x48 action cell; arc_start/end/centre/mid as [dx,dy] from pivot; layer over. Context work/ctx_r2_A2.png (f2 with its baked blade smear masked: work/r2a/A_f2_noblade.txt). Lint 0 isolated.
## Step 9: TASK B2 impact + hurt redrawn for the 32 px figure (A_r3)
- maps/{hit_spark,hit_flash,hurt_star,sweat_drop}.txt + anchors; hand-typed grids/stamps in work/b2/make.py, anchors work/b2/anchors.py, context work/b2/ctx.py -> work/ctx_r2_B2.png. Lint 0 isolated.
- hit_spark 14x14 (40/60/80), pivot (6,6) = 2x2 centre: f0 4x4 W core, 2 px W-root rays up5/right5/down4/left3 -> y -> o, 4 diagonals (SE longest); f1 8 px W/y ring 2 px thick + 4 detached 2 px pinwheel rays; f2 6 2x2 y/o chips at 60 deg, r~6. hit_flash 9x9 hard 4-point star W + 1 px y edge.
- hurt_star 24x13 (60/120), canvas at cell (8,-5), pivot (12,11) = head top (20,6); ellipse a9 b3, angles 90/210/330 -> 150/270/30; front = 5 px 5-pt star (W glint), back = 3 px diamond star (3 px 5-pt read as flames, rejected). No twinkles/grey.
- sweat_drop 4x9 (120/120/200), K/c/W/B, tip kept every frame, slides 0/1/2, f2 +1 px neck; offset_from_head_top [10,2] -> cell (30,8).
## Step 10: TASK C2 dust redrawn for the 32 px figure (A_r3)
- maps/dust_{step,land,skid}.txt + anchors; hand-typed puff stamps (4x3..7x6, g rim / u lit top-left / U body / g underside) in work/c2/make.py, anchors work/c2/anchors.py, context work/c2/ctx.py -> work/ctx_r2_C2.png. Lint 0 isolated, colours g/u/U only, no chips.
- step 10x9 (80/100/120), pivot (12,8) -> cell (20,37), layer over: 5x4 puff behind the back heel -> 7x6+4x4 rising back-left -> 4x4+4x3 higher. land 24x7 (60-120), pivot (12,6), widths 12/18/22/24, lift 0/0/1/2, light kept top-left on both sides (not mirrored), layer over.
- skid 20x7 (70/70/90), pivot (19,6) = back heel cell (16,37), layer behind: 3-row g/u/g ground streak + 2-3 lifted puffs, back puff curls highest; f2 streak breaks into two 4x3 ground puffs. ground_y in every anchors file.
- Known limit: the g rim is low contrast on #6e6e6e (palette-fixed); the read comes from u/U fill. Step/land are drawn over the feet because behind-layer hid them in context.
## Step 11: TASK D2 dash + jump redrawn for the 32 px figure (A_r3)
- maps/{speed_lines_long,speed_lines_short,jump_whoosh,land_ring}.txt + anchors; specs in work/d2/make.py, anchors work/d2/anchors.py, context work/d2/ctx.py -> work/ctx_r2_D2.png + work/dash_ghost_r2.png. Lint 0 isolated.
- speed lines 18x18 / 11x18 (40/40), attach body_centre (cell 20,22), behind: 4 lines at cell rows 13/18/22/29 (gaps 5,4,7), lengths long 12/8/14/10 -> 10/13/9/12, short 6/4/7/5 -> 5/7/4/6; 2-row W head at the body, 1 px p then n tail; f1 shifted back 2-3 px. With ghosts, add [-12,0] to cell_offset.
- jump_whoosh 15x9 (50/80), pivot (7,8) = take-off point, ground-anchored: mirrored "( )" p-outer/W-inner, 2 px base -> 1 px tip, inner bases at cell x15/x25; f1 8 px tall, lifted, broken into 3 evenly spaced thinning pieces. 1 px launch streaks under the shoes.
- land_ring 20x5 (60/80/100), pivot (10,2) = ellipse centre on the sole row: 12x3 -> 16x5 -> 18x5 four arcs; n far arc, u ends/shoulders, W near bottom; ends 2 px, top/bottom 1 px; layer_split rows 0-1 behind / 2-4 over.
- dash_ghost_r2: afterimage() on A_r3 at alpha .75/.5/.25, 4 px apart, works unchanged.
## Step 12: lead correction #2 + reorg
- Lead: final figure size is 44-48 px in 64x64 -> 48 px set is PRIMARY again; the r2 32 px set (steps 8-11) kept as secondary in maps32/NAME_32.txt (+anchors). r1 48 px maps archived in r1/maps48/. Primary r2 48 px redraw goes to maps/NAME.txt.
## Step 13: TASK A3 slash smears redrawn for the PRIMARY 48 px figure (C_r3, 64x64 cell)
- maps/slash_{h,diag,over}.txt + anchors, 3f 40/60/60, W/p/b (+n tail only). Outer/inner contours hand-typed as even run lists (work/r3A3/shapes.py), bands from BFS distance to the outer edge (W 2-3 / p / 1 px b), f1/f2 derived from the f0 outer band (work/r3A3/make.py; h f2 hand-typed; chip gaps tuned with gaps.py to 2 px each). Lint 0 isolated.
- h 40x12 (origin cell 12,40; hand 44,44): tail 1->2->3 px with n, belly 7 px at x27-34 near the lead, lead curls up to a 1 px tip. diag 32x36 (origin 31,11; hand 44,45): tail 1 row above the bow's right end, 6 px max lower right. over 38x40 (origin 20,7; hand 44,45): tail behind the bow, inner edge >= 2 px clear of bow/head (checked), 6 px max rows 19-29, 5-4-3-2-1 lead taper.
- f1 = same outer edge, 3 px W W p, tail cut ~36% with n 1->2 taper; f2 = 4 lens chips (1-2-1 px W/p) evenly spaced back from the lead tip.
- Anchors: pivot = sword hand on f0, arc_start/end/centre/mid as [dx,dy]; layer over. Context work/ctx_r3_A3.png (over plain C_r3; its resting sword is not hidden).
## Step 14: TASK B3 impact + hurt redrawn for the 48 px figure (C_r3, 64x64 cell) — primary set
- maps/{hit_spark,hit_flash,hurt_star,sweat_drop}.txt + anchors; hand-typed grids/stamps in work/r3B3/make.py (ring rows typed as run tables, y/W rim by 4-adjacency), anchors work/r3B3/anchors.py, context work/r3B3/ctx.py -> work/ctx_r3_B3.png (4x); board work/r3B3/board.png. Lint 0 isolated.
- hit_spark 19x19 (40/60/80), pivot (8,8) = UL of 2x2 centre, cell_offset (32,44): f0 6x6 rounded W core + 2 px W-root rays (up7/right9/down6/left7, y flare at root, staggered 2-row y/o tips) + 4 short y/o diagonals; f1 12 px ring / 8 px hole (2-3 px, y outer W inner) + 4 detached 2x2 pinwheel rays; f2 6 2x2 y/o chips at 30+60k deg, r~8.
- hit_flash 13x13 hard 8-point star (yWy arms to the edge, 1 px y diagonal spikes), W/y only. hurt_star 35x19 (60/120), canvas at cell (15,-4), pivot (17,18) = head top (32,14); ellipse a13 b4, 90/210/330 -> 150/270/30; front 9x9 (7 fill) / back 7x7 (5 fill) K-outlined y/o + W glint, front bottom 3 px above head top.
- sweat_drop 6x11 (120/120/200) K/c/W/B, tip kept, slides 0/1/2, f2 +1 px neck; pivot (2,0), offset_from_head_top [13,3] -> cell (45,17).
## Step 15: TASK C3 dust redrawn for the 48 px figure (C_r3, 64x64 cell) — primary set
- maps/dust_{step,land,skid}.txt + anchors; 9 hand-typed round masks (4x4..10x9, even 1-1/2-2/3 step runs) shaded by rule in work/r3C3/make.py: 1 px G rim all round, u lit top-left, U body, g underside/lower-right crescent; anchors work/r3C3/anchors.py, context work/r3C3/ctx.py -> work/ctx_r3_C3.png (4x, rows 30-64 crop). Lint 0 isolated, colours G/u/U/g only, no chips.
- step 14x14 (80/100/120), pivot (11,13) -> back heel cell (28,61), over: 7x6 at heel -> 10x9 risen 2 px / 4 px back + 5x5 at heel -> 6x6 + 4x4 higher back.
- land 34x10 (60-120), pivot (17,9) -> cell (34,61) (feet span centre), over: widths 18/26/32/34, lift 0/0/1/3, 3/3/3/2 puffs per side (small top puff behind in f0/f1), light top-left on both sides.
- skid 27x11 (70/70/90), pivot (26,10) -> cell (30,61) under the back heel, behind: 4-row G/u/U-g streak thinning to 1 row at the back + 2-3 puffs, back puff 8x8 highest (3 px lift); f2 = two 6x5 ground puffs + 5x5/4x4 lifted. ground_y in all anchors.
## Step 16: TASK D3 dash + jump redrawn for the 48 px figure (C_r3, 64x64 cell) — primary set
- maps/{speed_lines_long,speed_lines_short,jump_whoosh,land_ring}.txt + anchors; specs in work/r3D3/make.py, anchors work/r3D3/anchors.py, context work/r3D3/ctx.py -> work/ctx_r3_D3.png + work/dash_ghost_r3.png (afterimage() .75/.5/.25, 5 px apart, lines at cell_offset +[-10,0]). Lint 0 isolated.
- speed lines 22x27 / 15x27 (40/40), body_centre cell (32,44), offset_from_body_centre [-32,-22] / [-25,-22], behind: 5 lines at cell rows 22/28/32/40/47 (gaps 6,4,8,7), heads end x17-20 (2-3 px behind the silhouette); long 16/12/20/14/17 -> 13/17/15/18/12, short 8/6/10/7/9 -> 7/9/6/10/8; f1 shifted back 3/2/4/2/3. W head 2 rows (top run 2-4 px), 1 px p then n tail.
- jump_whoosh 23x12 (50/80), pivot (11,11) -> cell (34,61), ground-anchored, behind: "( )" p outer/W inner, 2 px rows at the base (beside the shoes, x25-26/42-43) -> 1 px W -> p curl, outer x runs 2-2-4-2; 2 W/p/n launch streaks under the shoes. f1 11 px tall, lifted 1 px, 3 pieces with even 1-row gaps, streaks 1 px lifted 3.
- land_ring 27x9 (60/80/100), pivot (13,4) -> cell (34,61): 19x5 -> 25x7 -> 27x9 four arcs (runs 4-4-4, 3 px / 3-row gaps); n far arc, u ends + near shoulders, W near bottom; layer_split rows 0-3 behind / 4-8 over. Canvas reaches cell row 65 (don't clip to the cell).
## Step 17: r2 48 px assembled
- maps/*.txt (14 effects, lint 0 isolated), gifs gif/NAME.gif. Boards work/r2_48_a.png, work/r2_48_b.png; tools/context.py -> work/ctx_r2_48_{L,R}.png (f0 of each effect on the 48 px C_r3 and the 40 px A_r1 figure, offsets scaled 40/48): all read at both sizes; slashes are big but valid at 40 px. Palette fx_v2 adds G #4c4038 dust outline.
## Step 18: round-2 critique (crit/r2_argon.txt, crit/r2_opus.txt) on the 48 px set
- Argon: diag 7, h 6.5, over 7.5, flash 6, spark 7.5, hurt_star 8, sweat 8, land 6.5, skid 6, step 7.5, speed 5.5, whoosh 5, ring 7, ghost 8.5. Opus: diag 7, h 5, over 7, flash 7, spark 7, hurt 7, sweat 7, land 7, skid 5, step 6, speed 6, whoosh 4, ring 7, ghost 8; "~70% PMD, pixels clean now".
- To fix (r3): slash tails still 1 px hairline for ~8 px; slash_h f1/f2 hook up into a "J"; over f2 chips 1 px; flash orange diagonal tips; spark f2 clock-face chips; hurt back star too big / floats 6 px high; sweat frames too similar; dust_land f3 single dots; skid plank streak; step f0 pebble; speed lines "=" menu icon / club heads, detached from body; whoosh reads as "( ' ' )" face; ring f0~f1 too similar.
- Rejected: brown/navy outlines on stars/sweat (sprite + PMD emotes use pure black); saturated cyan/yellow slash rim (brief asks W / pale steel / light blue-grey).
## Step 19 (A4): slashes round-3 polish (work/r4A4/: h.py, diag_final.py + d4.py/runsd.py run-list edges, over.py; before/after.png, ctx_slash.png)
- slash_h 40x7: hook removed, flat crescent (outer runs 2-3-4-5-6-7-8 / 3-2, lead tip 3->2 px pointing right), tail n 1-2-3; f1 3 px band same tip; f2 chips 6/5/4/3. cell_offset y 44->41 (+ re-cut 5 rows higher): cell y36-42, above the obi (43-46). On the 40 px figure it now sits at chin level.
- slash_diag redrawn 37x32: 45 deg chord from right of the head (cell 60,23) bulging down-right over the right hand to the lead tip at the sword hand (pivot = lead tip, cell_offset 28,54); edges typed as even run lists, f1 inner edge 1-2-2-1-1.., f2 chips 6/5/4/3.
- slash_over: f0 tail n(1)-W/p(2)-WWb(3) (no n hairline), f1 tail nn / WW / pWWW, f2 chips 2 px thick 6/5/4/3, gaps 3. Lint 0 isolated on all three.

## Step r4-B4: hit_flash / hit_spark / hurt_star / sweat_drop polish (work/r4B4/make.py, board work/r4B4/board.png)
- hit_flash: diagonals now 2 px W-cored spikes (W at (4,4),(3,3) + y rims, y tip at (1,1)) grown out of a 5x5 W core, so cardinal->diagonal is no longer a hard stair-step; W/y only (no o).
- hit_spark f2: 6 chips (3x 2x2, 3x 2 px), radii 6-9, irregular angles. hurt_star 35x15, canvas at cell (15,0), pivot (17,14): flat orbit (a11 b1.5), sizes 7/5/3 per frame (left side nearer), bottoms 2-3 px above the bow.
- sweat_drop 6x12: slide 0/1/2, f1 W highlight -> 2 px streak, f2 neck +2 (bottom moves 0/1/4 = accelerating). K outlines kept pure black (Step 18). Lint 0 isolated.

## Step r4-C4: dust polish (work/r4C4/: land_hand.py, skid.py + lobes.py, step.py; originals in work/r4C4/orig/, boards b2-b4.png, ctx.png)
- dust_land: each side redrawn by hand as one billow (single outer G, internal G removed; lobes separated by u/U seams + 1-2 px g creases); f3 = merged 3x3 + 2x2 puff pair per side instead of single dots. (Auto disc-union attempt, puff.py, read as rocks: rejected.)
- dust_skid: plank + lifted balls replaced by one merged trail of low lobes (2-3 rows, scalloped top), largest at the heel and shrinking toward the back; f2 lifts and rises toward the back. Same canvas/pivot.
- dust_step: f0 = two merged puffs (heel + one up/back); f1 small puff overlaps main by 2 px with a bridged u core; f2 pair overlaps too. Lint 0 isolated on all three; sizes/pivots unchanged.

## Step r4-D4: speed lines / jump_whoosh / land_ring polish (work/r4D4/: make.py, anchors.py, ctx.py -> ctx_D4.png, board.png; work/dash_ghost_r4.png)
- speed_lines_long 22x25 / short 15x25: 4 lines, 1 px tall, W front / p mid / n tail, at cell rows 23/31/40/46. Lengths 20/12/16/8 and 10/6/9/4, so the x-starts are staggered. Only line 1 of the long set has a swell (6 px p over the middle, 1-2-1). f0 heads end 1 px inside the back K edge. f1 is shifted back 2-3 px and re-lengthed. Pivots are now (29,22) / (22,22).
- jump_whoosh 23x16, pivot (11,15): the inner ticks are gone. Two outward-angled p/W arcs, open at the top, join a 2-row cup under the shoes ("\_/"). f1 is 16 rows tall, cut into even 3-on/2-off pieces along the stroke; the lower pieces are n/p.
- land_ring 31x9, pivot (15,4): widths 17/27/31 (shoes are 13). f2 has 6 evenly spaced dashes with 3 px gaps, mirrored on both sides. In dash_ghost_r4 the lines sit at offset +[-15,0], drawn behind and clipped to outside the ghost/figure alpha. Lint: 0 isolated on all four.

## Step r4-E5: slash_h crescent / jump_whoosh V / dust_land f3 (work/r4E5/make.py; originals work/r4E5/orig/, ctx_E5.png, board.png)
- slash_h 42x12 redrawn from work/h_try.txt as typed run lists: outer edge 2-2-2-2-3-3-3-6-3-3-2-2-2-1-1-1-1-1-2 (45 deg lead tip, no hook), inner rim 6-8-6-4-3-3-3-3-6; W 2-3 / p / 1 px b, belly 7, n tail ending in a 2 px point. f1 = same outer edge 3 px (pWW), tail cut to x12; f2 4 chips 2 px, ~5 px apart. Pivot (35,4) = 6 left / 4 below the tip, cell_offset [44,40], arcs recomputed.
- jump_whoosh: two separate '\ /' strokes (2 px p/W base at x3-4 / x18-19, 1 px p tip, not joined) + 2 np ground flicks; f1 13 rows, 3 evenly spaced 3-row dashes per side. dust_land f3: one merged 2-lobe wisp per side (8x5 with G), rows 2-6 (lift 3). Lint 0 isolated on all three.
## Step 21: round-3 critique (crit/r3_argon.txt, crit/r3_opus.txt) on the full 48 px sheet
- Argon overall 8.5/10 "shippable" (slashes 8, spark 9, flash 9, dust 8-9, whoosh 7, ring 8, star 9, sweat 9). Opus overall 7/10 "shippable as v1" (flash 8, spark 7, diag/over 7, slash_h 6, hurt 7, sweat 8, land 8, skid 6, step 6, whoosh 5, ring 7, speed 7, ghost 8).
- Final polish (r5): slash_h f1 tip still climbs + detached n tail; spark f0 asymmetric; whoosh strokes read as extra blades; skid even loaves; step f1 single blob reads as rock; hurt_star floats too high. Slash saturated rim rejected again (brief: white / pale steel / light blue-grey).

## Step r4-F6: final polish slash_h / hit_spark / jump_whoosh / dust_skid / dust_step (work/r4F6/make.py; originals work/r4F6/orig/, before/after.png, zoom.png ctx)
- slash_h: f0 tail joined (2 px n tip rows 4-6 running into the W/p bands, no 6 px hairline); f1 rebuilt as a 3 px band on a flatter edge, lead tip lowered to row 3 at 2 px/row (~27 deg), outer runs 1-2-2-2-3-3-3-3-6 (no 4 px flat step). hit_spark f0: 4-fold rotational star about the core centre (8.5,8.5), canvas trimmed 19->18 (anchors size), pivot unchanged.
- jump_whoosh: '( )' air cups in u/W only (2 px W/u base -> 1 px u tip, outer steps 1-1-2-4-2-1, curl back in); f1 risen 3 px, 3 curved 3-row pieces with 1-row gaps. dust_skid: separate tapered puffs, heel 9x7 / 10x8 with a shoulder lobe, then 6x5-6 and 5x4, gaps 2/1 and 1/2; f2 lifts 1/3/5. dust_step f1: 8x7 front puff over a 6x6 back puff (up-left). Lint 0 isolated on all five.
## Step 23: final build
- tools/build.py -> gif/NAME.gif (6x, #6e6e6e, per-frame ms + 200 ms blank) and png/NAME_fN.png / NAME_strip.png for all 14 primary (maps/) + 14 secondary 32 px (maps32/*_32) effects; atlas_48.png / atlas_32.png (1x, rects in manifest); sheet_48.png / sheet_32.png (4x labelled, red = pivot); context_48.png (f0 of each effect on the 48 px and 40 px figures); manifest.json (anchors, ms, attach, cell_offset, arc_* for slashes, layer, mirror rule, afterimage/whiteflash functions).
- Lint: all maps palette-clean, 0 isolated pixels (except deliberate glints). Final scores r3: Argon 8.5/10, Opus 7/10 (both "shippable"); r5 polish addressed the Opus r3 list (slash_h hook/tail, spark symmetry, whoosh as wind cups, skid taper, step split).
- Known limits: 32 px set stopped at r2 (secondary); slash rims stay W/p/n/b per the brief (Opus prefers a saturated rim); speed-line pivots sit outside their canvas (by design, see offset_from_body_centre).
## Step THROW-FX: charm-orb throw group (work/throw/make.py, anchors.py, board.png)
- throw_orb 7x7 4f 60ms loop (K outline, r/R top, k band with a W charm pixel sliding x3->x4->back->x2, W/w bottom; no button), attach ball, pivot centre; flight_per_unit [25,-5].
- throw_trail 26x14 (40/60) overhand smear n tail behind the head -> W/p head 4-5 px at the release hand, pivot (23,12), cell_offset [55,35]; throw_sparkle 9x9 W/y 4-point glint shrinking (40/60/60), attach hand.
- throw_pop 18x18 (40/60/80/80) W/y flash -> W/w ring + r/R & W/w chips -> scattered chips; pivot (8,12) on the ground, burst centre 3.5 px above. Lint: palette-clean, 0 isolated on all four.
