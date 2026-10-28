# Akane chibi 3D model: running log

## How to build, render and test
```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/build_character.py       # -> model/character.blend (~4 s)
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/render_turnaround.py [-- --round N] [--iso | --noanim | --quick]   # default round 5, ~2.5 min full (186 sprite cells)
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/rig_stress_test.py [-- --out DIR]   # default renders/model_round_5/stress; exit code 1 on any FAIL gate
.venv/bin/python model/sprite_post.py renders/model_round_N     # called by render_turnaround (clean-up + outline + checks.json)
.venv/bin/python model/make_sheet.py renders/model_round_N N    # called by render_turnaround (sheet.png, sheet_readability.png, anim strips)
```
- The build is fully procedural and deterministic. Two consecutive builds give the same mesh + pose hash (checked in round 3). It uses no randomness and no external assets, and reads only `docs/palette.json`.
- Round-1 scripts are in `model/archive/`. Round-2 scripts are in `model/archive/round2/`, round-3 scripts in `model/archive/round3/`.
- Round 4: two consecutive builds give the same vertex + Action hash (`9efe7f48…`, 34 Actions).
- Round 5: two consecutive builds give the same vertex + Action hash (checked, 38 Actions, 74 bones). Build ~60 s (sword / hook searches). Round-4 scripts are in `model/archive/round4/`.

## Conventions
- **Units:** 1 Blender unit = 1 H, where H is the bible head height.
  - Round 3: the whole head group is built at bible size and then scaled ×1.12 about the chin (0, 0, 1.80). The group is head, face, hair, bun and bow (`HEAD_SCALE`).
  - Crown is at about 2.86, and the bun + bow top at about 3.3.
  - At sprite scale the head (hair + bun + bow + face) is 46–52 % of the body height, not counting the sword (`head_ratio` in checks.json).
- **Orientation:** she faces **-Y** (S iso direction), origin at her feet.
  - **+X = her LEFT:** katana hand, thigh strap, skirt slit.
  - **-X = her RIGHT:** arm ornament, hip pouch, chest flower, bow.
- **Iso camera:** orthographic, rot X = 60° (30° elevation), **ortho_scale 7.3 H (round 4; was 6.5)**. That is 17.5 px/H in the 128 cell (bible §5: H ≈ 17 px), and the world origin lands on the pivot (64, 104). Stored as `rig["iso_ortho"]`; render_turnaround and the build's sword solvers read the same value.
  - The character rotates and the camera stays: yaw = index × 45° for S, SE, E, NE, N, NW, W, SW.
- **Sprite cells (`*_64.png`)** are 128×128 cells rendered directly at sprite scale.
  - Render settings: no AA, sprite katana, inverted hull off.
  - Round 3: the material rim is also off (`rim_thresh` node raised to 2.0), and the chest cord and the tassets (`corset_tabs`) are hidden, since the bible marks them [DROP]. All of this is switched by `render_sprite()`.
  - Each cell also gets an **object-ID pass**: a view-layer material override that emits the object colour, with R = group id × 10. It is occlusion-correct. Groups are listed in `_masks/id_groups.json`. `sprite_post.py` uses it for the per-region clean-up.
- **Pose:** ortho and iso renders use **`pose_idle_<DIR>`** (one Action per direction, see "Idle sword").
  - The ortho views use: front = S, side (seen from her left) = W, back = N, 3/4 = SW.

## Materials (all colours from docs/palette.json v2, exact hex output)
Each material is Diffuse → Shader-to-RGB → constant ColorRamp → Emission, with the Standard view transform. A camera-locked key light comes from the top-left. Every material writes a `matid` AOV and carries the custom props `palette_ramp` and `mat_id`.

| material | colours | use |
|---|---|---|
| M_skin | skin 3 | body, arms, legs |
| **M_skin_face** (r3) | **flat skin[1]**; skin[0] only where world normal.z < -0.88 (jaw underside) | head, ears. No diffuse terminator on the face |
| **M_hair** (r3) | **hair[0] shadow / hair[1] lit base** (bible ramp restored) + pink[0] rim | cap, bangs, strands, bun |
| **M_hair_sheen** (r3) | **flat hair[2]** | ONE continuous angel ring on the hair (ray-cast onto cap + bangs) + one ring on the bun |
| M_red | red[1..3] | collar, bodice, chest flower |
| **M_red_skirt** (r3) | **red[1] crimson body, red[2] only where lit (>0.78)** | skirt_outer: one ramp step darker than the sleeves |
| **M_red_sleeve** (r3) | **red[2] base / red[3] coral (>0.42)** + rim | sleeves (outer) |
| M_red_rim | red[1..3] + rim | bow |
| M_red_under | red[0..1] violet/crimson | skirt + sleeve inner shell (cuff interiors), under-skirt, bow knot + loop openings |
| M_red_inner | red[1..2] | collar inner face |
| M_leather | leather 3 | corset, straps, belt, pouch, tabs, thigh strap |
| M_dark | dark 2 | gloves, shorts, choker, hero tsuka |
| **M_dark1_flat** (r3) | flat dark[1] | sandal sole, vamp, straps, ankle ring |
| M_steel / M_steel1_flat / M_steel0_flat | steel | hero blade, guard + kagi, buckles / sprite guard |
| M_glint | steel[2] flat | eye sclera/glints, sprite blade (sprite_post re-shades it to steel[1] + 1 px steel[2] lit edge) |
| **M_pink** (r3) | **pink[0] base, pink[1] lit edge (>0.8)** | scarf ribbons: darker + more saturated than skin[1] (GD) |
| **M_scarf_under** (r3) | flat red[0] violet | scarf back face (Solidify shell) |
| M_purple | purple | arm lacing, ribbon, chest gem (model only) |
| flat decals | eye[0], eye[1], ink, pink[0] blush, skin[0] mouth, red[2] tsuka bands | face / tsuka |
| M_ink | outline #1a1220 | lashes, pupils, **stiletto heel point** |
| M_outline | #1a1220 | inverted hull for the 512/1024 renders only |

## Rig ("rig", 72 bones; 57 deform in round 4 -- see "Round 4 rig bone list" below for the current list; this section describes the round-3 base)
- **Torso and head:** root, cog, hips, spine, chest, neck, head, bun, bow.
- **Arms:** shoulder.L/R, upper_arm.L/R, upper_arm_help.L/R, forearm.L/R, hand.L/R, sleeve.L/R (cuff tips).
- **Legs:** thigh.L/R, thigh_help.L/R, shin.L/R, foot.L/R, toe.L/R.
- **Scarf:** scarf.L.001-005, scarf.R.001-005.
- **Skirt:** skirt.F, skirt.F.001, skirt.L(.001-.002), skirt.R(.001-.002), skirt.B, skirt.tail.001-003.
- **Props:** sword (child of hand.L), sheath.
- **Controls:**
  - foot_ctrl.L/R › toe_pivot.L/R › foot_ik.L/R, plus knee_pole.L/R
  - hand_ik.L/R, elbow_pole.L/R
  - sword_grip.R
- **Custom props:**
  - IK/FK and grip: `ik_leg.L/R` (1), `ik_arm.L/R` (0), `two_hand`, `skirt_follow`.
  - Expressions: `expr_wide/frown/smile/hurt`.
  - Data: `idle_sword_dir` (JSON per direction: [arm variant, azimuth, down]), `poses` (JSON), `cycles` (JSON, cycle metadata).
- **Round-3 rig changes:**
  - **Cuff pull-back:** a driver scales sleeve.L/R along the bone Y to 1 − 0.35·two_hand. With two_hand = 1 the hanging furi folds toward the wrist, so both gloves show on the tsuka.
    - This is length-only on purpose. A uniform scale collapsed the cuff to a 12× edge ratio.
  - **IK hand orientation:** IK_rot (hand copies hand_ik rotation) is now driven as 0.65 × ik_arm. The rest of the wrist twist stays in the forearm, so the two-handed grips no longer candy-wrap the wrist and cuff.
  - **Head collider:** `head_collider` is a hidden ellipsoid around hair + face, rigid to the head bone. A Shrinkwrap (OUTSIDE, offset 0.015) after the Armature on sleeve.L/R, arm.L/R and sleeve_band.L/R pushes raised sleeves and arms out of the head.
- **The sword stays in hand.L** (bible: left hand, always drawn). The `to_sheath` constraint and the hidden saya mesh are kept for a sheathed variant. The bible says there is no sheath, so the saya stays hidden.

## Actions
- **Pose library (1 frame each, CONSTANT, fake user):**
  - `pose_rest`, `pose_idle` (= idle_S), `pose_idle_S/SE/E/NE/N/NW/W/SW`
  - `pose_sword_ready`, `pose_walk_contact`, `pose_run_stride`, `pose_jump_apex`
  - `pose_overhead`: in round 3 this became a high hasso-style guard. With the bigger chibi head the hands cannot reach over the crown.
  - **`pose_attack_slash_mid`** (new, GD)
- **Keyframed cycles (new, TA):**
  - **`anim_idle`** (8 f, Bezier, loop, play 1-8): 1 px breathing bob, chest/head counter-motion, lagging scarf / sleeve / tail drift. IK feet planted.
  - **`anim_walk`** (8 f, linear, loop, play 1-8): in place, contacts at f0 (L) and f4 (R), stride 1.0 H.
    - The stance foot's heel and ball are planted, and slide back at constant speed (0.125 H/frame = walk speed), with heel-strike toe lift and toe-off heel lift.
    - Also: hip sway and twist, chest counter-twist, arm swing, scarf/tail lag.
  - Both use the S idle sword aim.
  - Frame 9 = frame 1 (loop seam). `use_frame_range` is 1–9, so render frames 1–8.

Apply one with `rig.animation_data.action = bpy.data.actions[name]; scene.frame_set(f)`.

## Weights (analytic, per-vertex at generation time)
- **Shoes (r3):** the sole, stiletto and vamp are 100 % foot, and the toe region is 100 % toe. The straps and the ankle ring are also 100 % foot.
  - Result: shoe max edge ratio is 1.0 in every Action. Round 2 was 3.3.
- **Shorts (r3):**
  - The waistband is 100 % hips.
  - Over the leg openings the weights blend hips › thigh_help › thigh.
  - The centre seam blends both legs and keeps at least 0.5 hips.
  - The crotch panel is shortened (to z 0.86) and is at least 0.78 hips.
  - Result: shorts p99 is 1.76 in sword_ready, 1.63 in run_stride and 1.94 in FK run. Round 2 was 4.42 in sword_ready.
- **Sleeves:** linear skinning (DQS off; DQS plus the cuff scale collapsed edges). Weights by ring parameter: upper_arm › forearm › sleeve tip.
- Everything else is as in round 2: chain_w rigid segments with smoothstep joints, helper half-rotation bones, skirt angle × depth weights plus thigh follow, and rigid head parts.

## Objects (round 3; round 4 adds katana_sprite_kagi)
- **Body:** arm.L/R, hand.L/R, leg.L/R, foot.L/R, shoe.L/R, body_torso, neck, head, ears.
- **Face:** face_decals.
- **Hair:** hair_cap, hair_sheen (ring), bangs, hair_strands, bun, bun_sheen (ring).
- **Upper costume:** bow, collar, choker, bodice, chest_flower, chest_cord.
- **Sleeves:** sleeve.L/R, sleeve_band.L/R, arm_ornament.R.
- **Waist:** corset, corset_buckles, belt_pouch, **corset_tabs** (split out in round 3).
- **Lower costume:** skirt_outer, skirt_under, shorts, thigh_strap.L.
- **Scarf:** scarf.L/R.
- **Props:** katana, katana_sprite, saya (hidden).
- **Helper:** **head_collider** (hidden).

## Round 5 log (response to the AD / GD / TA / Gemini round-4 reviews)

Renders: `renders/model_round_5/` (sheet.png, sheet_readability.png, sheet_anim8.png, checks.json for 186 sprite cells, stress/stress.json). New strips: `anim_run_SE.png`, `anim_jump_SE.png`, `anim_slash_SE.png`, `anim_overhead_slash_SE.png` / `_NW.png` (+ `_strip64`).

### Hair and head (AD blocker)
- **Side hair pulled up (no hood).** The hair cap is now built row-by-row down to an explicit hairline, so the edge is smooth (no face-cut stair steps):
  - front 2.47 (under the bangs), temple 2.47 -> 2.30 (short sideburn), over the ear 2.39, then it drops right behind the ear (az 99-112 deg) to the nape (2.00, under the collar).
  - Below the temple, over the ear zone (az ~35-110 deg), the cap hugs the skull (head + 0.016 H, Solidify 0.016). The back keeps its volume. The temple / back puff is gone; only a small crown puff remains, and the back-of-skull bulge is smaller (C.y 0.025 -> 0.012, R.y 0.50 -> 0.488).
  - **Ears** are bigger and stand clear of the skull (flared back 20 deg). They are visible in side, 3/4, SE, SW and in the front ortho. On sprites they have their own object-ID (`ear`) and a 1 px skin[0] inner line (`ear_pass`).
  - **One face-framing lock per side** (`hair_strands`): thin, tapered, lying over the outer cheek in front of the ear (phi 1.10 -> 1.06), and lifting off the cheek toward the tip, so it does not join the hair outline. The two long bang side locks and the short lock behind the ear are removed.
  - **Pulled-up streaks** (`hair_streaks`, new): 10 slim raised locks from behind the ears and the nape sweeping up to the bun base. They read as "gathered into the bun" in the side / back / 3/4 orthos. Model only: listed in `SPRITE_DROP`.
- **Bangs rebuilt.**
  - 8 locks, part at her left (phi +0.45). The long locks sweep to HER RIGHT (screen-left in the front view).
  - The tip line is asymmetric: shortest at her left temple (2.28), longest just right of centre (2.15). The tips touch or overlap the upper lash line, so there is no bare-skin band. The back layer hem sits behind the locks (2.37-2.43), so the locks define the hem.
  - **Lock roots are buried** under the cap (out0 0.070 -> 0.030), so the side profile has no sliced root strips. The back layer spans phi ±1.18 (was ±1.42), so the temples stay clear for the ear.
  - M_hair_bangs threshold 0.70 -> 0.76 (more hair[0]; AD "push the hair darker").
- **Bun vs cranium (AD/GD "snowman").**
  - The bun is higher and a little forward: BUN_C (0, 0.25, 2.89) -> (0, 0.21, 2.95). The bow follows (BOW_K z +0.055).
  - ONE messy loop bun: a round core plus a single twisted loop with a pinched notch, and a short flyaway. The second curl torus is gone.
  - New material **M_hair_bun** (hair[1] above 0.58), so the bun is lighter than the skull and reads as a second circle.
  - **Crease ring** `bun_crease`: a thin flat hair[0] tube ray-placed on the skull where the bun sits.
  - The bun sheen is one short arc (70 deg, high on the bun).
  - Sprites: the bun has its own object-ID group `bun`. `bun_pass` gives it hair[1] on the lit upper-left and hair[0] on the lower-right, at most 3 hair[2] sheen pixels on the upper-left, and a **1 px outline crease wherever bun pixels touch skull hair**. N: bun 97 px with a 15 px crease, and it rises about 4 px above the skull contour.
- **Lash flicks shortened** (0.045 -> 0.022 H), so they no longer read as a second winged eyebrow.
- **NE / NW head turn 16 -> 3 deg** (chest 12 deg kept). With the ear exposed, 16 deg showed a 6 px cheek + ear patch. Now NE shows a 1-3 px cheek sliver. NW still shows a ~4 px cheek + ear (ear line drawn).

### Sprite eyes (AD must-fix)
- `stamp_eyes` in sprite_post hand-pixels the eyes on the rendered eye positions (blue-pixel blobs inside the face id):
  - **near eye 3 x 4**: 1 px outline lash row, eye[0] upper rows with 1 steel[2] glint on the key-light (left) side, eye[1] bottom row.
  - **far eye (SE / SW) and profile eye (E / W) 2 x 3**: lash, eye[0], eye[1].
- S gets two 3 x 4 eyes, with at least 1 skin px between them.
- Eyes overwrite face pixels and single bang-tip pixels (Gemini: hair splitting the iris). Directions are parsed from the cell name, so the stamp also runs in every anim / pose cell.
- `eye_px` / `eye_boxes` in checks.json: S 23 px, SE 15, SW 17, E/W 6. Every S/SE/SW idle and walk cell has >= 9 eye px.
- The **mouth** pixel search is wider, so SE and SW now have a 1 px skin[0] mouth (`mouth_px` 1 in S, SE and SW). In E/W the mouth is intentionally absent (profile, no front face plane).

### Sleeve cuffs (AD must-fix)
- **Trumpet bell:** the radius grows fastest near the wrist (exponent 1.7, hem radius 0.262 = 0.52-0.55 H across with folds), and the lip rolls out 9 % over the last 10 %.
- The folds are gentler (0.075 -> 0.05).
- **Curved U hem:** the front and back hang lowest and the inner and outer edges rise, so the hem reads as a rounded bell from the front and side instead of a planar slanted cut.
- **Interior:** the new **M_red_cuff_in** is red[2] lit inside, red[1] mid, and red[0] violet only in the deep occluded part (< 0.10).

### Front skirt panel (AD must-fix)
- **Wrap panel:** the hem dips a little at her right-front and rises diagonally (+0.075 H) to the overlap edge at the slit on her left.
- The front hem flares out 8 %, and the overlap edge stands 3.5 % proud of the layer below.

### Blade pixels (AD must-fix)
- `blade_redraw` re-rasterises the sprite blade as a **constant 2 px line**, fitted (PCA) to the rendered blade pixels:
  - one pixel per major-axis step plus its neighbour: steel[2] on the lit top/left side, steel[0] on the spine side, 1 px tip;
  - it is drawn only where the blade was visible (it never paints over body parts that hid it) and never over the hand / tsuka / kagi.
- The outline pass draws **no lit-side outline along the blade** (shadow-side ink only), so there are no notches.
- The hook check uses the redrawn blade mask.

### Kagi / hook (AD + GD + TA)
- **Lopsided guard:** the sprite guard bar's spine-side stub is 0.09 H (was 0.17), about 1 px, so the guard reads as a one-sided hook, not a cross.
- **NE idle:** new per-direction hand nudge `IDLE_HAND_DIR_OFF["NE"] = (0.32, -0.02, 0.10)`: outward and slightly forward, not back (GD).
  - The NE sword is re-solved with the nudged hand: **screen angle 29.4 deg** (was 43).
  - `solve_hook_roll` then searches an extra blade roll that maximises the projected kagi cells clear of the silhouette (NE +10 deg, E +10 deg). The roll is applied to the NE / E idle pose and to every frame of the NE / E cycles (`HOOK_ROLL`).
- **Pose cells:** `solve_pose_hook_roll` rolls the blade so the kagi is clear in both SE and NW (it maximises the worst view).
  - This applies to every `solve_pose_sword` pose, plus walk_contact and attack_slash_mid.
  - Two-handed grips keep their authored roll unless the kagi is hidden; then they search only ±30 deg, because the right hand follows the tsuka.
- Result: `hook_fail` drops from 9 to 6 of 186 cells:
  - **iso_NE and all 8 anim_idle_NE frames pass**, and so do walk_contact SE, slash NW and overhead NW.
  - Still failing: anim_walk_E f2 / f7, pose_jump_apex_NW, pose_run_stride_NW, and anim_overhead_slash_NW f6 / f7 (new cells).

### SW legs (AD must-fix)
- Legs have per-side object-ID groups (`leg_L`, `leg_R`, each with leg + foot + shoe). `leg_split` draws a 1 px outline on the far leg wherever it touches the near leg horizontally. The near leg is the one whose lowest pixel is lower on screen.
- SW: 4 px of separation. Both feet and ankles now read separately.

### Rig: overhead range (TA must-fix)
- **New head-clearance layer `arm_clear.L/R`** (non-deform) sits at the shoulder joint, between shoulder and upper_arm. upper_arm and upper_arm_help are now its children.
  - A driver reads the RAW FK channels of upper_arm (quaternion angle or Euler magnitude, never evaluated data, so there is no dependency cycle).
  - It swings the arm outward about the body's forward axis by `min(50, 1.0 x max(0, angle - 90))` deg (`rig["arm_clear"]`). It is off in IK, where hand targets are authored.
- **Clavicle translation:** `shoulder.L/R` location drivers lift the shoulder joint up and back by up to 0.04 H, ramping in from 100 deg. The clavicle rotation factor is lowered from 0.6 to 0.3 (`rig["shoulder_autoraise"]`).
- Result (rig_stress_test, gated now):

| test | arm/sleeve p99 | head penetration | achieved elevation |
|---|---|---|---|
| FK forward 150 | **1.92** (was 5.4-5.9) | **0** (was 328) | 131 deg, arm carried out beside the head |
| FK side 150 | **1.79** | **0** | 127 deg |
| FK forward 120 | 1.95 | 0 | 116 deg |
| anim_overhead_slash (all 8 f) | max **2.51** | **0** | grip at jaw height front-left, blade up and back over the head |

- Honest limit: a commanded 150 deg raise lands at 127-131 deg. The chibi head (1.24 H wide) physically blocks a straight-up arm, and arm_clear carries the arm beside the head instead. A literal vertical thrust or victory pose still needs either the GD's "head scale 0.95 in high poses" or authoring the hand IK beside the crown.
- `fk_arms_overhead` (raw Euler X +150 on both arms, the round-3 test) is kept for reference, marked LEGACY and not gated: with the mirrored roll the right arm swings across the face.

### Timed Actions (TA must-fix + nice-to-have)
| Action | frames | metadata (`rig["cycles"]`) |
|---|---|---|
| `anim_overhead_slash` | 8, non-cyclic | windup f2-4 (above the head), active f5-6, recovery f7-8 |
| `anim_slash` | 6, non-cyclic | windup f2, active f3-4, recovery f5-6 |
| `anim_run` | 8, cyclic | contacts f1 / f5, flight phase, stride 1.8 H; sword trailing (solved for SE + NW) |
| `anim_jump` | 8, non-cyclic | anticipation f1-2, air f3-6 (apex f4-5), landing f7-8, `cog_dz` list |

- All are in place, S facing. They are rendered from SE (overhead slash also from NW) at 256 px and at sprite scale. rig_stress_test checks every frame: penetration 0, sword-through-body 0, foot slide run 0.018 / others <= 0.009, leg worst 2.56 (jump apex).
- `foot_pivot_ok` now gates only idle / walk / run cells; jump air frames and lunges leave the pivot row by design.

### Mesh clean-up (TA must-fix)
- **Deltoid caps:** the deltoid ellipsoid's poles now point along the arm axis instead of straight up, which removes the peaked nub. The shoulder top is one dome. Parity is 0.
- **Corset hoops:** the three straps and the top piping are closed rings (`tube(closed=True)`) at offset 0.040 (was 0.05), with a thinner section. No open ends poke past the torso contour.
- **Skirt back notch:** the under-layer points now sit behind the outer tails (148 / 212 deg), and its back-centre hem stays just under the outer gap hem (0.60 - 0.04). No violet box shows through the back-centre gap.
- **Bang roots:** buried under the cap (see Hair).
- **Loose vertices:** `tube(closed=True)` no longer adds the duplicate seam ring, which was the 18 loose bun verts (and others on the corset rings). rig_stress_test has a new **loose-geometry gate** (loose verts or edges on any visible mesh = FAIL). Result: none.
- **Scarf tips (Gemini):** a clean swallowtail. The two points extend past the end, and the V centre stays ahead of the previous row, so there are no folded faces or notches.

### Stress gates (this run, exit 0)
- `FAIL []`, 0 loose geometry, parity 0 for all closed shells.
- walk leg worst 1.93, run (FK) 2.31.
- fwd150 p99 1.92 / head 0, side150 1.79 / 0, overhead slash 2.51 / 0.

### checks.json summary (186 cells)
- Palette exact, binary alpha, 17-22 colours per cell, foot_pivot_fail [].
- char height 51-61 px.
- `blade_outside_fail`: 3 cells: anim_slash SE f1 (windup behind the body), anim_overhead_slash NW f6, pose_walk_contact SE.
- `scarf_near_arm_fail`: 15 cells, mostly walk SE/SW/NE frames and the new attack strips. This is still open.

### Not done / open (round 5)
- Scarf next to the raised arm: overhead NW and jump NW still fail the 6 px rule, plus some walk frames and the new attack strips. The ribbon root move into the collar back wing was not done this round.
- Bow knot red[1] pixel between the loops in S/SE (AD nice-to-have): not done.
- Idle sword pointing toward the facing (GD idea): not done. The idle angles stay at about 30 deg in all 8 directions, NE now included.
- Sprite head band: the N/NE height is still 51-52 px against 55-61 px elsewhere (pivot-anchored UI recommended, as in round 4).
- Gemini conflicts that are still rejected by AD ruling: centring the bow, removing the rim, rounded skirt scallops, hilt ribbon.
- Open shells (bangs, face_decals, skirt_outer, scarf) are still single-sided cards with Solidify thickness. The inverted-hull outline only runs on the 512/1024 renders; sprites use the 2D outline pass, so the sprite read is the same in every direction.

### Round 5 rig bone list (74 bones, 57 deform)
Round 4 list plus **arm_clear.L/R** (non-deform, parent shoulder.L/R; children upper_arm.L/R and upper_arm_help.L/R).
- Constraints and drivers: as in round 4, plus 4 quaternion drivers per arm_clear and 3 location drivers per shoulder (clavicle lift).
- New rig props: `arm_clear` (JSON).

### Round 5 Actions (38)
Round 4's 34 plus anim_run, anim_jump, anim_slash, anim_overhead_slash.

### Round 5 materials (32)
Round 4 list plus:
- **M_hair_bun**: hair[0] / hair[1] at 0.58, plus rim.
- **M_hair0_flat**: flat hair[0], for the bun crease.
- **M_red_cuff_in**: red[0] / red[1] / red[2] at 0.10 / 0.40, for the sleeve interior.

M_hair_bangs threshold is now 0.76.

### Round 5 objects (52)
Round 4 objects plus **hair_streaks** (model only, sprite-dropped) and **bun_crease**.
- New object-ID groups: `bun`, `ear`, `leg_L`, `leg_R`. These replace `leg` / `shoe`, and `bun` is split out of `hair` / `sheen`.

## Round 4 log (response to the AD / GD / TA / Gemini round-3 reviews)

Renders: `renders/model_round_4/` (sheet.png, sheet_readability.png, **sheet_anim8.png** (new: both cycles × 8 directions), checks.json for 148 sprite cells, stress/stress.json).

### Sprite height (AD must-fix) — camera, not a bible amendment
- Iso ortho scale 6.5 → **7.3 H per 128 cell = 17.5 px/H** (bible §5 H ≈ 17 px). The cell size, pivot (64, 104) and tile ratio are unchanged.
- Char height (sole → bow top, body mask) per direction: S 58, SE 57, E 54, NE 51, N 51, NW 57, W 59, SW 60 (`checks.json char_height_px`, summary `char_height_px_range`). Front/side directions sit at 56–60, as the bible asks. N/NE are lower because the bow is behind or under the bun projection from behind. This spread is expected; engine hitboxes and name plates should anchor to the fixed pivot plus a constant 58 px band, not to the per-frame bbox.

### Bow (AD must-fix ×2)
- **Camera-facing bow:** the `bow` bone has a **Locked Track** constraint (track = bone Z, the bow front; lock = bone Y, up) toward `cam`. Its influence is driven by the new rig prop `bow_face_camera` (default 0.85).
  - The stiff ribbon bow is presented to the camera like a 2D sprite, so both loops and the red[0] openings read in all 8 directions.
  - The knot stays at her right bun base, so its screen position still separates NE / N / NW.
  - The mesh keeps a 20° front-right turn of its own (round 3: 35°). The loops' V is wider: direction (0.70, 0.10, 0.72), was (0.62, 0.10, 0.78).
- **Bow value:** the bow ramp is red[1] < 0.30 < red[2] < 0.97 < red[3]. sprite_post caps coral at 12 % of the bow and removes any rim except the 1 px right-hand contour.
  - `bow_red12_frac` (red[1] + red[2] share of bow pixels): 0.73–0.92 in every iso cell. The minimum is NW at 0.725, which is ≥ 0.70.
  - W and SW now show two separate loop tips.

### Katana hook guard (AD + GD must-fix)
- **Separate object:** the sprite kagi is now its own object, `katana_sprite_kagi`, with object-ID group `kagi`.
- **Bigger crescent:** hook_r 0.135, about 0.30 H tip to tip. It sits off the edge-side end of the bar and its long horn curves back toward the blade.
- **Shorter bar:** the spine-side arm of the bar is shorter. At 64 px it used to read as a second prong, so the guard looked like a "fork".
- **Same orientation on the hero katana:** the hero (non-sprite) katana uses the same crescent orientation.
- **Blade roll toward the camera** (new `flat_to_camera_edge`, `set_sword_dir(..., yaw=...)`):
  - The blade flat faces the camera in every idle, cycle and pose cell, so the crescent shows in full profile instead of edge-on.
  - In idle and cycle cells the hook side points away from the body on screen.
  - Pose cells are shown from both SE and NW, so there the hook takes the world-down side.
- **Sprite blade:** 2–3 px wide for the first 60 % from the guard (radius 0.078 × 0.064), then tapers. The tsuka is 7 alternating ink/red[2] bands.
- **Outline:** sprite_post draws a **steel[0] outline around the kagi** (`kagi_outline_px`).
- **New check in checks.json for every cell:** `hook_px` (largest connected kagi component), `hook_free_px` (kagi pixels with no blade pixel within 1 px), `hook_connected`, and `hook_ok` (≥ 3 px, connected, ≥ 2 free px).
  - Result: **139 / 148 cells pass**, including 7 of 8 iso cells (10–12 px each).
  - Failing iso cell: NE (6 px; the hand splits it).
  - Failing anim cells: 4 of the 8 anim_idle_NE frames.
  - Failing pose cells: slash / jump / overhead NW and walk_contact SE. In these the guard is inside the sleeve cuff and hand cluster.

### Sleeve value (AD must-fix) and red mass separation (GD must-fix)
- **M_red_sleeve:** red[1] < 0.07 < **red[2] base** < 0.86 < red[3].
  - sprite_post caps red[3] at 25 % of the sleeve, keeping the top-left-most pixels.
  - It also draws a red[1] interior line where a sleeve pixel touches a lit red[2] skirt pixel.
  - `sleeve_red3_frac` is 0.05–0.24 in every iso cell.
- **Collar (new M_red_collar):** red[1] with a red[2] lit sliver, and the inner face is red[1]/red[2]. It is now one value step under the red[2] bodice and sleeves, and frames the face.
- **Skirt:** unchanged, red[1] body with red[0] undersides.

### S chest cluster (AD must-fix)
- `chest_flower` is dropped on sprites, in `SPRITE_DROP` together with the cord and tassets.
- sprite_post:
  - The torso reds become a **flat red[2] bodice** with a **1 px red[1] collar-base line**.
  - The arm-flower cluster keeps ≤ 3 red[3] px next to the purple, and the rest of its petals take red[2].
  - Purple is capped at 3 px; the lowest pixels are kept, so the dangling ribbon still reads.
- The 1–2 px bare-shoulder skin shows on both sides in S.

### Hair (GD must-fix: bangs + value; Gemini; AD nice-to-have)
- **Bangs rebuilt as parted, side-swept anime bangs:**
  - A smooth back layer, plus 10 pointed locks. The locks part at her left (phi ≈ +0.3) and sweep away from the part, with an almost linear taper (`hair_lock(..., taper=0.6)`).
  - The longest lock sits between the eyes. The locks over each eye are shorter, so a 1–2 px brow gap shows over the near eye in SE (her right) and SW (her left).
  - Two long side locks (to z 2.03) frame the cheeks, and the jaw strands are fuller (0.068).
  - The tips sit at the brow line. The back layer behind the gaps is hair, not skin, so there is no bowl hem and no bare forehead.
- **Darker brunette:**
  - M_hair: hair[0] is the dominant base, and hair[1] only shows above 0.92 lit (was 0.30). The S hair is about 2:1 hair[0]:hair[1].
  - The bangs get their own `M_hair_bangs` (threshold 0.70), so the pointed clumps read against the dark cap at 64 px.
- **Angel ring:**
  - Hair ring: an **arc on the key-lit side only** (azimuth −125…+20°) with a lock scallop, not a full "tonsure" band (Gemini).
  - Bun ring: also an arc (−150…+40°).
- **Pink rim (AD):** sprite_post draws the rim only on the right (back-right) contour, and only between 15 % and 75 % of the hair height. There is no crown-top rim any more in N/NW.

### Face (AD/Gemini nice-to-have)
- **Eyes:** the calm upper lid is 0.31 (was 0.20), about 12 % lower, for the half-lidded refs/1 look. EYE_Z is 0.013 H lower and the lash curve is wider.
- **Head shape:** the cheeks are less bulbous (0.045 → 0.022) and the jaw tapers a little more.
- **Mouth (GD/TA):** sprite_post places a 1 px skin[0] mouth under the eyes when none survived (`mouth_px`). This works in S and SE. In SW the target pixel falls on the collar, so SW still has no mouth.

### Collar (AD nice-to-have)
- The side wings are about 0.055 H higher toward the jaw-height funnel. The front V is unchanged, so the mouth still reads.

### Legs and walk (GD must-fix)
- **Skirt front:** the front panel hem is at 0.69 H (was 0.60) and the slit opens 56° → 72°.
- **Idle A-stance:** each heel is 0.045 H further out and the toes turn out 8° (`idle_feet`). A background gap now shows between the legs in S/SE/SW (Gemini "fused legs").
- **Walk:** WALK_STRIDE is 0.50 → 0.64 (stride 1.28 H; about 8 px horizontal and 4 px vertical foot spread at contact in SE). Swing lift is 0.13 and the bob is a little deeper.
- **Walk stress:** foot slide is still 0.014 H/frame and penetration is 0.

### Back facings NE / N / NW (GD must-fix)
- New `dir_turn(rig, dir)` is used by both the idle poses and every per-direction cycle.
- **NE/NW:** hips 8°, chest 12° and head 16° turn toward the camera. One shoulder blade and sleeve lead, and a sliver of cheek (plus the eye corner in NW) shows on the facing side. The scarf tails swing to the opposite side.
- **SE/SW:** the ribbons swing to the far side, off the near bare arm.
- **N** stays symmetric.

### Scarf (TA/GD must-fix, AD nice-to-have)
- **Roots:** moved down and inward behind the collar's back centre (z 1.86, x ±0.028), tied narrower (half-width 0.030 → 0.078 at the tails).
- **Back view:** the ribbons follow an out-in-out S-curve, on top of the existing twist.
- **Poses:** walk_contact streams the ribbons back (+X curve), overhead hangs them down the spine, and jump lifts them less (14°, was 30°).
- **`scarf_near_arm_max_run`:**
  - iso: N 4 (was 9), NE 5, SE 1, SW 1, all others 0.
  - pose_test: 5 (was 13). walk_contact SE: 0.
  - Still above 6: overhead NW 10 (was 18) and jump NW 9 (was 10). In both, the ribbon root under the collar sits next to the raised arm's deltoid cap (map in the review notes). 8 of the 64 walk cells score 7–8.

### Direction-consistent sword / arm (TA + GD must-fix)
- **One idle arm variant for all 8 directions.**
  - `solve_idle_sword` scores four IK variants (`IDLE_HAND`: hang / front / front_out / side_high) over all 8 directions and keeps the variant with the lowest total.
  - The winner is **side_high**: the relaxed left hand rests at the side of her left hip, (0.43, −0.13, 1.03).
- **Screen angle from vertical:** S 30, SE 30, E 36, **NE 43 (was 54)**, N 30, NW 30, W 30, SW 30.
  - NE trails slightly backward (az 85°). The TA accepted a slight tail.
  - Every direction is now within 13° of the 30° target. NE does not meet the GD's 10° target; the TA's 15° limit is met.
- **Per-direction cycles (new Actions):** `anim_idle_<D>` and `anim_walk_<D>` for all 8 directions, each with that direction's sword aim, arm variant and dir_turn. `anim_idle` / `anim_walk` are the S versions.
  - In walk the IK hand swings ±0.05 H.
  - `rig["cycles"]` marks every Action cyclic or not (poses are non-cyclic).
  - All 128 cycle cells are rendered (`anim_<idle|walk>_<D>_f<k>_64.png`) and collected in `sheet_anim8.png`.

### Rig (TA must-fix)
- **Knee helper:** `knee_help.L/R` is a child of the thigh at the knee and copies half of the shin's local rotation. The leg weights blend thigh → knee_help → shin over ±0.06 H.
  - anim_walk worst leg edge ratio: **9.2 → 1.93** (every frame).
  - fk_run_stride leg worst: **9.06 → 2.31**.
  - jump_apex leg max: 3.2. fk_jump_tuck (90° / 100° crouch) leg max: 6.77 (was 9).
- **Elbow helper:** `elbow_help.L/R` (half of the forearm) is used by both the arm and sleeve weights. It fixes a sleeve-fold collapse in bent-elbow idles; idle sleeve max is 1.7 in every direction.
- **Clavicle auto-raise:** drivers on `shoulder.L/R` (w + z quaternion components, simple expressions, so no Python auto-run is needed).
  - The raise is `0.6 × max(0, elevation − 85°)`.
  - Elevation is the FK upper_arm angle, taken from the quaternion, or from the Euler magnitude when the channel is in Euler mode. In IK it is the hand_ik height above the shoulder.
  - The drivers never read the evaluated arm, so there is no dependency cycle.
  - Settings are stored in `rig["shoulder_autoraise"]`.
- **Raised-arm results — honest status:**
  - The TA's X +150 test: head penetration 328 → 2 vertices, but p99 4.15 → 6.18, because the clavicle swing compresses the sleeve band and deltoid.
  - New anatomically aimed tests in `rig_stress_test.raise_arm`: forward 120° p99 2.47. Forward 150° and side 150° still put the arm inside the 1.12× head (p99 5.4–5.9, 328 vertices).
  - Scanning the factor from 0.3 to 1.0 made no setting pass.
  - Conclusion: with a 1.24 H-wide head and 0.25 H shoulders, a > 120° raise cannot clear the head.
  - **The rig envelope for sword work is ≤ 120° elevation, or IK high guards** (pose_overhead p99 2.33, head pen 0). Rising and overhead slashes should arc out to the side of the head, not over it. A true fix would need a clavicle *translation* rig layer or a smaller head, which is an AD/GD call.
- **Normals:**
  - New `fix_closed_normals()` gives every closed manifold island of every mesh consistent outward winding. It re-wound belt_pouch, bow, buckles, tabs, katana, katana_sprite and thigh_strap, which had inward box/cap winding.
  - The bun curls are built as truly closed tori: `tube(closed=True)` welds the seam ring, followed by `recalc_normals` on the bun.
  - rig_stress_test now runs a **per-island ray-parity test** (odd number of hits = inward face; the face's own triangles are ignored). The result is **0.000 for all 21 closed meshes, bun included**.
  - The centroid test is kept for the open head shells (all 0.0). The bun's centroid value of 0.222 comes from its curl inner faces and is superseded by parity.
  - The stress test **exits with code 1** and prints FAIL lines if any shell is above 0.02, or if the walk-cycle leg worst is ≥ 3.0. This run: exit 0.

### Not done / open
- **Sword guard ribbon (Gemini, refs/1):** the long pink ribbon tied at the guard is not modelled. The bible has no hilt ribbon, so this needs an AD call; it is easy to add as a 3-bone chain on the sword.
- **Gemini requests that conflict with the bible:**
  - Centring the bow: the bible puts it on her right side.
  - Rounded skirt scallops: the bible asks for pointed petal tails.
  - Removing the rim light: the bible requires it.
- **The hook still fails in some cells:** NE idle frames and the NW two-hand poses, where the guard sits inside the cuff and hand cluster.
- **Ribbon next to the raised arm:** overhead NW (10) and jump NW (9) are still above the 6 px rule.

### Round 4 rig bone list (72 bones, 57 deform)
root, cog, hips, spine, chest, neck, head, bun, bow, scarf.L.001-005, scarf.R.001-005, shoulder.L/R, upper_arm.L/R, upper_arm_help.L/R, **elbow_help.L/R**, forearm.L/R, hand.L/R, sleeve.L/R, sword (child of hand.L), sword_grip.R, sheath, thigh.L/R, thigh_help.L/R, **knee_help.L/R**, shin.L/R, foot.L/R, toe.L/R, skirt.F, skirt.F.001, skirt.L/.001/.002, skirt.R/.001/.002, skirt.B, skirt.tail.001-003; controls hand_ik.L/R, elbow_pole.L/R, foot_ctrl.L/R, toe_pivot.L/R, foot_ik.L/R, knee_pole.L/R.
- Constraints and drivers:
  - Leg/arm IK with poles and foot roll.
  - half_rot helpers: thigh_help, upper_arm_help, knee_help, elbow_help.
  - Hands: `to_tsuka` two-hand, cuff pull-back driver.
  - Skirt follow.
  - **bow `face_camera` Locked Track** (prop `bow_face_camera`).
  - **shoulder auto-raise drivers**.
  - Sword `to_sheath` (influence 0).
  - Expression shape-key drivers.
- Rig props: ik_leg.L/R, ik_arm.L/R, two_hand, skirt_follow, expr_wide/frown/smile/hurt, **bow_face_camera**, idle_sword_dir, poses, cycles, **shoulder_autoraise**, **iso_ortho**.

### Round 4 Actions (34)
- pose_rest, pose_idle, pose_idle_S/SE/E/NE/N/NW/W/SW
- pose_sword_ready, pose_walk_contact, pose_run_stride, pose_jump_apex, pose_overhead, pose_attack_slash_mid
- anim_idle + anim_idle_S…SW (8 f, Bezier, cyclic), anim_walk + anim_walk_S…SW (8 f, linear, cyclic)

### Round 4 materials (28)
- M_skin, M_skin_face, M_hair (hair[0]/hair[1] @0.92 + rim), **M_hair_bangs** (hair[0]/hair[1] @0.70 + rim), M_hair_sheen
- M_red (red1-3), **M_red_collar** (red1/red2 @0.88), M_red_inner (red1/red2 @0.80), M_red_skirt (red1/red2 @0.78), M_red_rim (bow: red1/2/3 @0.30/0.97), M_red_sleeve (red1/2/3 @0.07/0.86 + rim), M_red_under (red0/1)
- M_leather, M_dark, M_dark1_flat, M_steel, M_steel1_flat, M_glint, M_pink, M_scarf_under, M_purple
- Decals: M_eye_dark, M_eye_light, M_ink, M_blush, M_mouth, M_red_flat
- M_outline

## Round 3 log (response to the AD / GD / TA / Gemini round-2 reviews)

**Head and face**
- **Head ×1.12 about the chin (GD).** Measured at sprite scale, the head is 46–52 % of body height.
- **Profile (AD).** `head_deform` now models a rounded face volume:
  - Cheeks are widened about 4.5 %.
  - The face sides come slightly forward (a flatter front, so the far eye stays visible in 3/4).
  - The mid-face swells forward below the eyes (cheek and mouth), and there is a soft chin point.
- **Eye decals (AD).** They are 0.003–0.012 H off the skin (round 2: up to 0.022), slightly narrower (0.21 H wide), and 0.41 H apart. In the side view they sit inside the silhouette. Gemini round 3 rated this FIXED.
- **Face shading (AD/TA).** The face is a flat skin[1] (M_skin_face). The only shadow is the jaw underside, so the wedge is gone.
- **Bangs (Gemini/AD/TA).** The hem is lowered to the eye-top line with shallow lock gaps, so there is no bare forehead. The outer-eye locks end above the lash line.
- **Head turns toward the camera:**
  - idle_E/W: chest 10° and head 12° toward the camera, so the eye and the face edge read (GD).
  - idle_SE/SW: head 10° toward the camera, so both eyes read (AD/TA one-eyed SE).

**Hair**
- The bible ramp is back: hair[1] is the lit base and hair[0] the shadow. The outline colour is no longer used inside the hair.
- The angel ring is **one continuous hair[2] band** (round 2 had 6 arcs). It is ray-cast onto the real cap + bangs surface. The bun has one ring as well.
- The bun is about 11 % bigger and its spiky twigs are removed (Gemini). Two curl loops give the messy read instead.
- Normals: bangs, hair_strands, hair_sheen and bun_sheen were rebuilt facing outward (`MB.build(outward=…)`); the Solidify offsets were re-signed to keep thickness inside.
  - The inward fraction is 0.0 for every head shell (stress.json `normals_inward_fraction`).
  - The bun reads 0.22 because of its torus curl loops: their inner faces legitimately face the bun centre.

**Bow**
- Moved back and to her right, to the right base of the bun.
- Turned 35° to face front-right, with loops more upright (0.45 H long). It reads as two loops in the front and side views. The loop pair also shifts between NE, N and NW (GD facing cue).

**Collar**
- The front and side wings are lower (front edge about 1.82 at the chin), so the chin and mouth show in S/SE/SW at 512. At 64 px the mouth is still at most 1 px.

**Idle sword (AD/GD)**
- The horizontal hip "spear" is replaced by a per-direction **geometric search**, `solve_idle_sword`, with these rules:
  - It targets a 30° screen angle from vertical, with the blade hanging down and out.
  - The tip stays at z ≥ 0.03, the blade stays ≥ 0.05 H clear of every body mesh, and at least 40 blade px must fall outside the silhouette (projected-vertex mask).
  - "Tail" aims are penalised hard: backward in 3D *and* against the facing side on screen.
  - Two arm variants are tried. "hang" is FK, arm hanging. "front" uses IK and the relaxed hand rests in front of her left hip.
- Results (screen angle from vertical):

| dir | variant | az / down (°) | screen | px outside (render) |
|---|---|---|---|---|
| S | hang | -60 / 27.5 | 30° | 61 |
| SE | front | -110 / 17.5 | 30° | 46 |
| E | front | -155 / 17.5 | 30° (forward-down, facing side) | 50 |
| NE | front | -160 / 27.5 | 54° (forward-down, facing side) | 42 |
| N | hang | 60 / 27.5 | 30° | 50 |
| NW | hang | 15 / 27.5 | 30° | 59 |
| W | hang | -25 / 17.5 | 30° | 42 |
| SW | hang | -20 / 17.5 | 30° | 42 |

- **Geometric limit (important for the animation stage):** the grip is at about 0.9 H and the blade tip is 1.70 H from the grip. The blade can therefore never be steeper than about 60° from vertical *in 3D*. A ~30° look on screen only comes from aiming partly toward the camera. In NE that is only possible with a trailing (backward) blade, so NE uses forward-down at 54° instead of a tail.

**Pose readability**
- run_stride, jump_apex and overhead aims come from `solve_pose_sword`: the blade must break the silhouette in both SE and NW (at least 40 px, approx mask), plus a per-pose acting preference.
- Rendered blade px outside the body (checks.json):
  - run 45 / 60, jump 55 / 70, overhead 66 / 52
  - sword_ready 70 / 62, slash 67 / 59, walk 33 / 52
- All pose cells pass the gating rule of ≥ 30 px outside.
- The jump sleeve flare is reduced (60° → 32°), so jump SE is no longer a cuff blob.

**Scarf (GD/TA)**
- About 4 px wide at the tails (tied narrow at the collar) with a deep swallowtail.
- Darker pink[0] base with a pink[1] edge and a violet red[0] back face.
- Rest curve: from the collar it streams **back** and down, about 0.95 H long, staying within ±0.18 of the spine so it never runs beside the arms in the front views.
- checks.json `scarf_near_arm_max_run` (scarf pixels within 2 px of skin-arm/glove pixels; must be ≤ 6):
  - 0 in S/SE/E/NE/NW/W, 1 in SW.
  - **9 in N**: the ribbon roots cross the bare shoulder tops while running down the back. It reads as a ribbon over the back, not a limb.

**Sleeves vs skirt (GD)**
- The bell cuffs are about 20 % smaller (0.235) and end at the wrist, so the glove shows below the cuff.
- Value split: the sleeves are red[2]/red[3] and the skirt is red[1] crimson with red[2] only on lit planes. The cuff interiors are violet/crimson.

**Skirt**
- 4 wider petal tails (18°) on taller gaps (base 0.67 at the back). The back tails go down to 0.20 H.
- Fold ripple is reduced, so the hem is cleaner.

**Sandals**
- Thin dark[1] sole, a dark[0] stiletto point, a dark[1] vamp and straps, and one thin ankle ring.
- There is no heel counter, so the skin heel and ankle read from the back.

**Pouch / tassets**
- Shorter, flatter tabs, split into `corset_tabs` and dropped on sprites. The plate rivets are removed.

**sprite_post.py clean-up (AD)**
- Pink rim: a continuous 1 px run on the rim-light side of the hair + bow silhouette (right contour + right half of the top), with components under 3 px removed. `rim_orphans` = 0 in every cell.
- Stray violet: purple outside the ornament is replaced, along with lone red[0] specks on the sleeves. `violet_outside_ornament` = 0.
- Corset: a solid leather[1] band with a 1 px leather[2] top line and ≤ 2 steel[1] buckle pixels. The pouch is flat leather[1] with a leather[2] top.
- Skirt hems: 1 px teeth removed and 1 px notches filled.
- Cloth orphan pixels are fixed.
- The angel ring is thinned to 1 px, with fragments under 3 px removed.
- Blush is capped at 2 px per cheek.
- Sprite blade: steel[1] body with a 1 px steel[2] lit edge (TA/Gemini).
- checks.json now covers **every** `*_64` cell (iso, pose and anim frames), 36 cells in all. Summary: palette exact, 0 semi-alpha, no blade-outside failures, no foot-pivot failures.

**Stress test (`renders/model_round_3/stress/stress.json`)**

| Action | arm/sleeve p99 | shoes max | shorts p99 | sleeve-head pen. |
|---|---|---|---|---|
| sword_ready | 1.70 | 1.0 | 1.76 | 0 |
| run_stride | 1.48 | 1.0 | 1.63 | 0 |
| walk_contact | 1.18 | 1.0 | 1.27 | 0 |
| jump_apex | 1.55 | 1.0 | 1.11 | 0 |
| attack_slash_mid | 1.83 | 1.0 | 1.61 | 0 |
| overhead (high guard) | 2.41 | 1.0 | 1.56 | 0 |
| idle_* | ≤ 1.65 | 1.0 | 1.10 | 0 |

- Cycles:
  - anim_idle: foot slide 0, skirt-through-leg 0, sword-through-body 0 over all frames.
  - anim_walk: planted-foot deviation from treadmill speed ≤ 0.014 H/frame, skirt-through-leg 0, sword-through-body 0.

### Known issues / next round
- **FK arms-overhead at 150° (TA test):** p99 4.2, max 16×. 328 vertices are still inside the head volume (stress image).
  - Cause: forward flexion past about 120° drives the upper arm straight through the 1.12× chibi head. The collider pushes vertices out but cannot do so without stretching.
  - Raised-arm poses must abduct (arms out to the side) or use the IK high guard.
  - A real fix needs an abduction corrective on the shoulder. Doing it with a Transformation constraint from the child bone would create a dependency cycle, so it needs an extra FK control layer.
- **overhead (high guard) arm p99 2.41** is just above the 2.0 target (cuff fold under two_hand plus armpit compression).
- **NE idle blade** is 54° from vertical, not 30° (see the geometric limit above). E/SE use the "front" arm variant, so the idle arm pose differs per direction; the animation stage must blend the variants.
- **Scarf near arm, N (9 px), plus some pose and walk frames (7–18 px):** the ribbon roots cross the shoulder tops in back views, and in sword_ready, overhead NW and jump NW the posed ribbons pass the arms.
- **Mouth at 64 px** is at most 1 px or hidden by the collar in S.
- **Knee and hip crease compression** in deep bends (leg max up to 9×, hidden by skirt/shorts) is unchanged.
- **Ribbon colour:** pink[0] base deviates from the bible §2 (pink[1] base); it was changed at the GD's request. The AD should confirm and update the bible.

## Round 2 log (response to AD / GD / TA / Gemini round-1 reviews)

**Hair**
- Very dark brunette, using only palette colours.
- The crown disc is replaced by thin angel-ring arcs that follow the skull, plus arcs on the bun.
- The bangs are rebuilt:
  - The back fringe now has a spiky hem just above the brow.
  - Six chunky pointed locks sit on top, swept to her right, with longer locks over the outer eyes.
- The jaw strands are moved back in front of the ears (azimuth 74°) and given volume and pointed tips, so the profile and eye read in E/W.
- The hair cap gets temple and back puff for volume.
- The bun is about 12% bigger.

**Face**
- The eyes are 0.035 H lower and larger (0.23 × 0.28 H). The calm half-lid is the default.
- The other expressions are shape keys (wide / frown / smile / hurt).
- The lower-lash ink mark under the eye was removed (Gemini: no ink around the blush).
- The jaw tapers softly.
- The ears are smaller, flatter and partly tucked under the side locks, so there is no lump in the side view.

**Collar**
- The top edge sits at 1.77 H in front (jaw level) and rises to 1.98 H at the back (0.3 H above the base).
- The V opens to 76° at the top, and the flare goes outward (0.9 H wide).
- The chin and mouth are visible in S/SE/SW.

**Bow**
- Sits at the front-right base of the bun.
- The two loops tilt back 25° and splay ±22°, with violet loop openings front and back and a violet knot as a value break.
- Both loops read in front and back.

**Legs and sandals**
- Legs taper from thigh r 0.152 to knee 0.09, with a calf bulge, a knee dip and an ankle of 0.056. The knees are slightly inward.
- The sandals now have:
  - a closed dark toe vamp and a dark sole,
  - a stiletto heel,
  - a criss-cross instep,
  - two ankle rings with an X between them on the front,
  - a thinner heel counter.
- The skin ankle shows above the rings.

**Scarf**
- 5-bone chains.
- The rest curve splays out to either side of the spine (x up to ±0.55), streams back, and drifts toward her right.
- It has an S-curve, twist and taper, and ends in a swallowtail notch.
- The bare-back strip between the collar and the corset is clear.

**Skirt**
- The bell stops at 0.5 H. Below that, 4 narrow pointed petal tails (116/152/208/244°) hang nearly straight to 0.22 H, with high gaps (hem about 0.6 H) between them.
- The violet under-layer is shorter (0.42–0.50 H), so the shins and heels show in N/NE/NW.
- The front slit on her left is wider (gap 56° at the hem).

**Sleeves and arms**
- The sleeves taper under the band, the bell flare starts sooner, and soft 5-lobe folds start at mid-forearm.
- The deltoid is rounder, and the skin highlight threshold is raised, so the vertical highlight rectangle is gone.
- The arm ornament is about 30% bigger, with thicker lacing and ribbon.

**Pouch and tabs**
- The pouch is a real-volume rounded box with a flap, a stud and a strap loop to the belt. It is placed on the skirt surface by raycast; in round 1 it sat buried inside the skirt.
- The two tassets lie on the skirt surface with steel buckles.

**Sprite katana**
- The blade is an 8-sided prism of about 0.13 × 0.11 H, so it is ≥2 px from every view. It uses **one flat shade** (steel[2]), and the pipeline outline supplies the steel[0] edge, so the blade is no longer dashed.
- The tsuka is chunky (0.12 H) with alternating red[2]/ink bands.
- The kagi is a 0.23 H crescent in flat steel[1].

**Idle sword aim**
- A render-based search was run over 64 directions × 8 yaws (blade pixels outside the body mask + screen angle).
- The rest aim is straight out to her left and 28° down, and the tip stays above the floor. This passes 6 of 8 directions.
- `pose_idle_E` (90°, 22° down: trailing straight back) and `pose_idle_W` (67.5°, 28°) cover the other two.
- checks.json result: blade pixels outside the silhouette are 35–61 in every direction, and 87–94% of blade pixels are in a 2×2 block.

**Pipeline**
- The inverted hull is off for the sprite cells, and the outline is drawn as a 1 px post pass.
- `sheet_readability.png` shows the 8 cells at 1× and 2× on grass, dirt and dungeon, with the 2:1 ground shadow.

**Stress test (`rig_stress_test.py`, results in `renders/model_round_2/stress/stress.json`)**
- The penetration test finds 0 leg-through-skirt samples for every Action and for the TA's FK run stride. FK jump-tuck shows 8 samples, all near the hip crease under the skirt top. The stress renders show no visible poke-through.
- Arm/sleeve **p99** edge ratio is ≤ 2.06 in all Actions and ≤ 1.86 in FK arms-T.
- The max ratio (worst single edge) is 2.5–3.4 at FK arms-T, FK overhead and the overhead Action. Those edges are small ones at the armpit, inside the deltoid cap.
- Round-1 worst cases were sleeve 19×, arm 11.5× and leg/shorts 4–5×.

### Known issues / next round
- **Arm stretch target not fully met:** the worst single edge is still 2.5–3.4× at arms-overhead 150° and arms-T 80° (target < 2). These are tiny armpit edges hidden under the deltoid cap. A real twist chain or corrective shape key would be needed to finish this.
- **Knee and hip creases compress** (max ratio up to 9× on inner-crease edges in deep knee bends). This is expected with linear skinning on a crease, and is hidden by the skirt and shorts.
- **Large sleeve cuffs hide the hands** in the two-handed poses. At 1× the grip reads as "hands together" rather than separate hands on the tsuka.
- **Per-direction idle sword aims (E/W)** must be used by the sprite pipeline (Actions `pose_idle_E` / `pose_idle_W`).
- **Hair base (#42282a) and corset leather (#4a2e20) are close in value.** They do not touch on the sprite, but a per-sprite ramp cap or an AD palette slot may be needed.
- **No keyframed cycles yet** (idle/walk/run/jump/attacks). Only single-frame pose Actions and the IK/FK controls exist for the animation stage.

## Round 1 log (summary)
- Built from scratch: a 40-bone FK rig with JSON poses.
- Gemini critique, round 1: the arm ornament was enlarged, the thigh strap moved lower, the corset straps deepened, the kagi enlarged and the bun made messier.
