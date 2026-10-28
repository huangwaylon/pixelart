# Akane chibi 3D model: running log

## How to build, render and test
```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/build_character.py       # -> model/character.blend (~3 s)
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/render_turnaround.py [-- --round N] [-- --quick]
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/rig_stress_test.py [-- --out DIR]
.venv/bin/python model/sprite_post.py renders/model_round_N     # called by render_turnaround (outline pass + checks.json)
.venv/bin/python model/make_sheet.py renders/model_round_N N    # called by render_turnaround (sheet.png, sheet_readability.png)
```
- The build is fully procedural and deterministic. It uses no randomness and no external assets, and reads only `docs/palette.json`.
- Round-1 scripts are archived in `model/archive/`.

## Conventions
- **Units:** 1 Blender unit = 1 H (head height).
  - Crown at 2.75 H, bun top about 3.15 H.
  - Bow is 0.8 H wide (cap 0.85).
  - Katana is 2.0 H.
- **Orientation:** she faces **-Y** (S iso direction), origin at her feet.
  - **+X = her LEFT:** katana hand, thigh strap, skirt slit.
  - **-X = her RIGHT:** arm ornament, hip pouch, chest flower, bow side.
- **Iso camera:** orthographic, rot X = 60° (30° elevation), ortho_scale 6.5 H.
  - That gives about 19.7 px/H in the 128 cell. The world origin lands on the pivot (64,104).
  - **The character rotates and the camera stays:** yaw = index × 45° for S, SE, E, NE, N, NW, W, SW.
- **`iso_<D>_64.png`** is a 128×128 sprite cell rendered directly at sprite scale.
  - Render settings: no AA, sprite katana, inverted hull **off**.
  - The raw render goes to `_masks/raw_*`. `sprite_post.py` then adds the pipeline outline: a closed 1 px exterior line in #1a1220 on the shadow side, and the darkest tone of the neighbouring ramp on the lit (top-left) side.
  - `checks.json` holds the automated per-direction checks: palette-exact, semi-alpha, colour count, blade pixels outside the body silhouette, and the fraction of blade pixels inside a 2×2 block (the ≥2 px test).
- **Pose:** ortho and iso renders use the relaxed **idle** pose (Action `pose_idle`). E and W use `pose_idle_E` / `pose_idle_W`, which differ only in the sword aim (see below). The ortho side view uses the W variant because it is seen from her left.

## Materials (all colours from docs/palette.json v2, exact hex output)
Each material is Diffuse → Shader-to-RGB → constant ColorRamp → Emission, with the Standard view transform. A camera-locked key light comes from the top-left. Every material writes a `matid` AOV and carries the custom props `palette_ramp` and `mat_id`.

| material | colours | use |
|---|---|---|
| M_skin | skin 3 (highlight threshold raised to 0.95 in round 2) | body, face, legs |
| M_hair | **outline #1a1220 shadow / hair[0] #42282a base** + pink[0] rim (round 2, AD) | cap, bangs, locks, strands, bun |
| M_hair_sheen | hair[1] #74483a band, hair[2] glint above 0.93 | angel-ring arcs on the skull + bun |
| M_red / M_red_rim | red[1..3] (rim on bow and sleeves) | dress, collar, bow loops, sleeves |
| M_red_under | red[0..1] violet/crimson | skirt + sleeve inner shell, under-skirt, bow knot + loop openings |
| M_red_inner | red[1..2] | collar inner face |
| M_leather | leather 3 | corset, straps, belt, pouch, tabs, thigh strap |
| M_dark | dark 2 | gloves, shorts, sandals, choker, hero tsuka |
| M_steel | steel 3 | hero blade, guard + kagi, buckles |
| M_steel1_flat | steel[1] flat | sprite katana guard bar, kagi, kashira |
| M_glint | steel[2] flat | eye sclera/glints, **sprite blade (one flat shade)** |
| M_pink | scarf roles pink[0] / **pink[1] base** / skin[2] (above 0.965 only) | ribbons |
| M_purple | purple | arm lacing, ribbon, gem |
| flat decals | eye[0], eye[1], ink, pink[0] blush, skin[0] mouth, red[2] tsuka bands/diamonds | face / tsuka |
| M_outline | #1a1220 | inverted hull for the 512/1024 renders only (off for sprite cells) |

**Cast shadows:**
- Off for all cloth, the sword and **all head parts** (head, hair, bangs, bun, ears). There is no diagonal shadow over the face (Gemini round 1).
- Body and limbs still cast shadows.

## Rig ("rig", 68 bones)

**Deform bones (53):**
- **Torso and head:** hips, spine, chest, neck, head, bun, bow.
- **Arms (each side):** shoulder.L/R, upper_arm.L/R, **upper_arm_help.L/R**, forearm.L/R, hand.L/R, sleeve.L/R (cuff tips).
- **Legs (each side):** thigh.L/R, **thigh_help.L/R**, shin.L/R, foot.L/R, **toe.L/R**.
- **Scarf:** **scarf.L.001-005**, **scarf.R.001-005** (5-bone chains).
- **Skirt:**
  - skirt.F, **skirt.F.001**
  - skirt.L, **skirt.L.001-002**
  - skirt.R, **skirt.R.001-002**
  - skirt.B, skirt.tail.001-003
- **Props:** sword, sheath.

**Control bones (non-deform, 15):**
- **root**, **cog**.
- **Feet:** foot_ctrl.L/R (heel pivot on the floor) › toe_pivot.L/R (ball pivot) › foot_ik.L/R (ankle). Also knee_pole.L/R.
- **Arms:** hand_ik.L/R, elbow_pole.L/R.
- **Sword:** sword_grip.R (child of sword, on the tsuka next to the guard).

**Custom props:** all are keyable, and all drive constraint influences through simple drivers. These drivers need no Python auto-exec.
- `ik_leg.L/R` (default **1** = IK).
  - IK on shin (chain 2) → foot_ik, with a knee pole.
  - foot.X copies the rotation of foot_ik.
  - Pole angles are solved numerically at build time, so IK at rest equals the rest pose (residual 3e-5).
- `ik_arm.L/R` (default **0** = FK). Same setup: IK on forearm → hand_ik, elbow pole, hand copies rotation.
- `two_hand` (0/1): hand_ik.R snaps to `sword_grip.R` with Copy Transforms. With `ik_arm.R=1`, the right hand holds the tsuka at the guard while the left hand stays at the pommel.
- `skirt_follow` (default 1): Transformation constraints are corrective skirt drivers.
  - skirt.F takes 55° per 100° of **forward** flex of either thigh.
  - skirt.B takes 45° per 100° of **backward** swing.
  - skirt.L/R take ±50° per ±100° of their own thigh's flex.
  - Sign probes at build time make the local-axis directions robust.
- `expr_wide`, `expr_frown`, `expr_smile`, `expr_hurt`: shape-key values on `face_decals`. The basis is the bible's **calm, half-lidded** default (upper lid down 20%).
- `idle_sword_dir`: JSON of the per-direction idle sword aim (character-local azimuth from +X toward +Y, and down angle).
- `poses`: JSON copy of every pose (bone basis + `_props`), kept for tools that do not read Actions.

**Helper bones:** upper_arm_help and thigh_help each have Copy Rotation 0.5 from their limb, in local space. They split the shoulder and hip bend into two blend zones, which removes the collapse at large raises or flexes.

**Sword:**
- Child of **hand.L**: the bible puts the katana in her LEFT hand. This differs from the task text, which said hand.R.
- In round 2 the katana mesh is offset 0.15 H along the blade (`KATANA_OFF`), so the left hand holds the **pommel end**. The tsuka no longer runs up through the forearm and sleeve (Gemini round 1).
- Constraint `to_sheath` (influence 0) switches the sword to the `sheath` bone. The saya mesh exists but stays **hidden**, because the bible says there is no sheath. The round-1 `to_hand.R` constraint was removed: it formed a dependency cycle with the new arm IK.

**Actions (pose library):** every Action is 1 frame, has all bones + props keyed with CONSTANT interpolation, and has a fake user.
- `pose_rest`, `pose_idle`, `pose_idle_E`, `pose_idle_W`
- `pose_sword_ready`: refs/2 low wide two-handed stance, feet about 1.4 H apart, knees bent outward, torso forward, blade forward and down, curved scarf, frown.
- `pose_walk_contact`, `pose_run_stride`
- `pose_jump_apex`: smile, sleeves and skirt flared, sword trailing.
- `pose_overhead`: two-handed wind-up, arched back.

Apply one with `rig.animation_data.action = bpy.data.actions["pose_x"]; scene.frame_set(1)`.

**Weights:** analytic per-vertex weights, written at generation time (`MB.wfn`).
- `chain_w` gives rigid segments with smoothstep blends at the joints. Arms use shoulder › upper_arm_help › upper_arm › forearm; legs use hips › thigh_help › thigh › shin › foot.
- Sleeves are weighted by ring parameter: upper_arm, then forearm, then the sleeve tip bone scaled by how far the furi hangs. There is **no chest bleed**.
- The deltoid cap is weighted 0.85 upper_arm / 0.15 shoulder, so it rotates as a unit.
- The shorts centre seam blends L/R.
- The skirt uses angle × depth weights over the F/L/R/B chains, plus thigh follow on the front and side panels.
- The scarf is weighted along the 5-bone chains.
- Rigid parts (head, hair, face, bow, sword, thigh strap) use a single bone.
- Arm, leg, shorts and sleeve meshes use the Armature modifier with **preserve volume (DQS)**.

## Objects (round 2)
- **Body:** arm.L/R, hand.L/R, leg.L/R, foot.L/R, shoe.L/R, body_torso, neck, head, ears.
- **Face:** face_decals (with 4 expression shape keys).
- **Hair:** hair_cap, **hair_sheen**, bangs (back layer + 6 chunky locks), hair_strands (jaw strands + side locks), bun, **bun_sheen**.
- **Upper costume:** bow, collar, choker, bodice, chest_flower, chest_cord.
- **Sleeves:** sleeve.L/R, sleeve_band.L/R, arm_ornament.R.
- **Waist:** corset, corset_buckles, belt_pouch.
- **Lower costume:** skirt_outer, skirt_under, shorts, thigh_strap.L.
- **Scarf:** scarf.L/R.
- **Props:** katana, katana_sprite (hidden; switched on for sprite renders), saya (hidden).

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
