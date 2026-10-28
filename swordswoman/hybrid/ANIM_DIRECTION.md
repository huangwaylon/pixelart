# ANIM_DIRECTION.md — the motion bible (hybrid pipeline)

Owner: Animation Director. Status: v1, 2026-10-25. Everyone animating her follows this: Gemini prompts,
Claude hand-pixel passes, the TA guide rig and the judges.

Where things are:
- Pose JSONs: `hybrid/anim/poses/*.json` (director format `dirpose/1`).
  - Executable sources: `tools/hybrid/anim/make_poses.py`.
  - TA guide-rig versions for `render_guides.py --pose`: `hybrid/anim/poses/ta/*.json`, absolute pose plus 8-direction `dir_override`.
  - Rig-native captures: `hybrid/anim/poses/rig/*.json`.
- Pose check renders: `hybrid/anim/preview/<pose>_<DIR>.png`.
  - Each comes with a `.json` of blade, hand and bun-tip screen coordinates.
  - These are guide colour renders, never art.
- Review strips: `hybrid/anim/review/`.
- Smear geometry per direction: `hybrid/anim/smears.json`.
- Research captures (saint11 tutorial sheets): `hybrid/anim/research/`.

Ground rules carried over from the project (do not relitigate):
- 3D renders are a hidden GUIDE only. The user rejected the round-9 3D sprites ("look terrible").
- The look target is `concept/chibi_iso_v5.png`, in its pixelized form `docs/palette_v1_vs_v2_terrain.png`.
- The idle pilot was rejected for a stiff "1 px bob" (`pixel/idle_PILOT_REPORT.md`). Nothing in this
  bible moves only 1 px.
- Key poses fall on the **same frame index in all 8 directions** (pilot lesson A2). The pose JSONs are
  direction-neutral, so this is automatic. Painters must not re-time per direction.
- Feet pivot (64,104), 128 cell, locked palette (`docs/palette.json`). There is no semi-alpha in sprites.
  Engine-side alpha on FX is allowed.
- Review **holistically**: every direction and frame together, in motion, at 1x and 4x, on grass and
  dark terrain. Never sign off a single frame.

---------------------------------------------------------------------------------------------------

## 0. What great pixel action games do (research summary, with sources)

| Lesson | Source | How we use it |
|---|---|---|
| Animate **pose-to-pose**. Key the extremes first; add interpolation frames before/after keys, not evenly between. Attacks are mostly keys + VFX. "Movement is love, movement is life." 3D was only the base; the character is ~50 px in game. | Thomas Vasseur, *Art Design Deep Dive: Using a 3D pipeline for 2D animation in Dead Cells*, Game Developer (gamedeveloper.com/production/art-design-deep-dive-using-a-3d-pipeline-for-2d-animation-in-i-dead-cells-i-) | Our exact situation. Our 3D rig gives keys. Timing lives in holds, and the energy is in smears and FX painted on top. |
| Retime by moving keys. Timing was retuned "dozens of times in minutes" for gameplay balance. | same | All timing is data (§1 json block). Painters never bake timing into frame duplicates. |
| Anticipation: "move weapon in the **opposite** direction of the attack", kept short for player characters ("usually avoided when drawing player characters"). | Pedro Medeiros (saint11, Celeste/TowerFall artist), *Top Down Attack* tutorial (Wayback: web.archive.org/web/20220103163702/https://saint11.org/blog/pixel-art-tutorials/, sheet saved in `hybrid/anim/research/f_TopDownAttack.png`) | Slash coil is 2 frames totalling 140 ms. The blade goes back over her RIGHT shoulder before cutting to her LEFT. |
| "The first [slash] frame should do the **full motion**; slowly stabilize while reducing the motion blur." "Recover in a different motion arc than the attack." "Overshoot the recovery in the last frame." "Keep one foot grounded"; "try rotating the head (just a little)". | saint11, *Top Down Attack* | Smear frame k1 shows the WHOLE arc. Impact keeps a thinning tail, follow-through keeps wisps. Recovery comes back low (different arc), with 1 px overshoot down on the last frame. |
| Motion blur "smears the image, like it's trying to connect it to the previous frame". Lighter colours bleed over darker; darker colours are used for fading. For very fast animation, **flash complementary colours** between frames. | saint11, *Motion Blur* (`research/f_MotionBlur.png`) | Smear core is steel_2 (lightest) bleeding over the body, with pink tones fading outward and at the tail. Two-frame smears alternate core colour (§4.5). |
| **Mass never changes**: when you change the width, change the height too. Preparation squashes **opposite** to the action. Stiff objects deform less. Mix squash with motion blur for extreme effect. | saint11, *Squash and Stretch* (`research/f_Squash.png`) | §2 squash/stretch tables are volume-paired. The katana and the head deform 0 (stiff). Body, skirt and sleeves deform. |
| Impact: "**cut out those frames**" between rest and target for a faster, stronger movement. Add lots of motion blur. Anticipation makes the motion feel stronger. Shake camera and target. **Freeze time**: pause one frame before the impact, not too long, only for very exaggerated impacts. | saint11, *Impact* (`research/f_Impact-export.png`) | There are NO in-betweens between the smear and the coil. Hit-stop is short and scaled by attack weight (§3). Heavy overhead only gets a 1-frame pre-impact hold (the apex coil). |
| Hitstop/hitlag: both fighters freeze on the hit. The attacker freezes on the frame the hit landed; the victim freezes in the first flinch frame **while shaking**. Strong attacks freeze longer: a 15 % hit is 8-15 frames at 60 fps depending on the Smash title, capped at 20-30. Projectiles/FX keep moving. | SmashWiki, *Hitlag* (web.archive.org/web/2024/https://www.ssbwiki.com/Hitlag); Masahiro Sakurai, *Stop for Big Moments! [Design Specifics]* (YouTube OdVkEOzdCPw) | Our hit-stop is lighter than Smash (a fast action-RPG): 3 / 4 / 6 frames at 60 fps (§3). FX continue during the freeze. Victim shake is ±1 px. |
| Screen shake sells hits. It is part of "game feel" alongside hit pause, knockback and impact effects. | Jan Willem Nijman (Vlambeer), *The Art of Screenshake*, INDIGO 2013 (YouTube AJdEqssNZ-U); Jonasson & Purho, *Juice it or lose it*, GDC Europe 2012 (YouTube Fy0aCDmgnxg) | Shake on hit only, never on whiff (§3). Small: 1-3 px at 56 px characters. |
| Anticipation is a trade-off: too little lacks weight, too long hurts control. Sword swings are **fast in, slow out**. Hold strong poses in follow-through so players read the move. Overlapping action: head/torso lead, arm lags, then snaps. **Avoid all parts starting/stopping together.** Stretch on fast travel; squash at apex/landing. Hold a jump apex longer than physics. Hair/cloth drag through the next animation. | *The 12 Principles of Animation in Video Games*, Game Developer (gamedeveloper.com/production/the-12-principles-of-animation-in-video-games) | Slash: active 40 ms, recovery 270 ms. Apex is held 150 ms. The lag tables are in §2. |
| Use a few fixed timing tiers that the player reads as intent: 6 frames is fast/responsive; 12 a quick stop; 18-24 deliberate weight. Keys every 3-6 frames. | *Designing animation for speed*, Game Developer (gamedeveloper.com/art/opinion-designing-animation-for-speed) | Our tiers at 60 fps game frames: smear 40 ms (2-3 f), contact/active 50-70 ms, settle 110-150 ms, breath holds 220 ms. |
| Great idles: "more frames do not always equal better"; Metal Slug 3 idles are 3-6 frames. Secondary motion and physics (Fidget's tail/wings, Ryu's pants in the wind) make characters feel alive. Subtle breathing; personality. | *What makes a great idle animation? Devs share their favorites*, Game Developer (gamedeveloper.com/art/what-makes-a-great-idle-animation-devs-share-their-favorites) | The 6-frame idle stays at 6, but the life comes from overlap: ribbons, bun/bow, sleeves, skirt tail and sword tip all lag the breath (§5.1). |
| Fewer frames + a good smear beats extra breakdowns. Strong, extreme key poses. Check silhouettes. Exaggerate, but not into noise. | *5 tips for making great animations for 2D games*, Game Developer (gamedeveloper.com/art/5-tips-for-making-great-animations-for-2d-games) | Every key must pass a silhouette check: fill the sprite black at 1x and the action must still read. |
| Run: hips rotate down on the landing side; the spine counter-rotates; **head bob lands a few frames after the foot impact**; arms oppose legs. | *Animating the Run Cycle*, Game Developer (gamedeveloper.com/art/animating-the-run-cycle) | Head and bun are +1 frame behind the cog in walk/run (§5.2-5.3). |
| Smear taxonomy: elongated in-between (stretched frame), **multiples** (repeated limbs along the path), duplicated trailing parts, **smear trails** (crescent/teardrop shapes off the moving edge), blob. Sonic's run feet; Crash's spin multiples. | Wikipedia, *Smear frame* (en.wikipedia.org/wiki/Smear_frame); *New School Blues dev diary 16: smearing*, Game Developer ("solid drawing that distorts the form across the range of motion", not a "feathery, formless blur"; only the moving character stretches) | §4 uses all four: arc trail on slashes, multiples on arms/legs in fast swings, a stretched frame in the dash, afterimage multiples in the dash. All are solid, hard-edged and palette-locked. No soft blur. |
| Squash/stretch, anticipation, follow-through/overlap, slow in/out, arcs, timing, exaggeration (definitions). | Wikipedia, *Twelve basic principles of animation* | Vocabulary used throughout. |

Genre references to watch while working: Dead Cells, Hyper Light Drifter, Celeste, Sea of Stars,
Hollow Knight, CrossCode, Children of Morta, Blasphemous and Eastward. Our web fetches for HLD, CoM,
Eastward, Blasphemous and CrossCode returned only press-level text, with no frame data. We took their
lessons from the gameplay patterns those games are known for, listed below, not from cited numbers.
- HLD and CrossCode: top-down slashes read by a crescent arc 2-3x the sprite's own size, a 1-frame
  smear, and a short freeze.
- Dead Cells and Blasphemous: big held anticipation poses on heavy weapons. Light weapons get almost none.
- Celeste: the hair is a lagging chain that changes state with the action.
- Sea of Stars and Eastward: chunky 1-2 px secondary bounce on small, round chibi forms, bigger than
  realism.
- Children of Morta: smear and dust FX carry most of the impact on ~50 px characters.
Our own measurement: the round-9 3D slash moved the body < 3 px between frames, and its smear was a
1 px pink line (`renders/model_round_9/anim_slash_SE_smear_strip64.png`). That is the anti-reference.

---------------------------------------------------------------------------------------------------

## 1. Timing (machine-readable; read by `tools/hybrid/hylib.timing_for`)

Changes against `docs/anim_spec.json` v2, with reasons:
- **idle** 6×150 -> `220,140,140,220,140,140`. The holds at the breath extremes (exhale settled f0,
  inhale top f3) give slow-in/slow-out, and the loop goes from 900 to 1000 ms. An even 150 ms is the
  metronome that made the pilot look mechanical.
- **jump** `70,90,120,90,70,90` -> `80,60,150,80,90,110`.
  - The rise is faster (60 ms): a stretch only reads when it flashes.
  - The apex is held longer (150 ms) for hang time (12-principles "hold the apex").
  - Land is 90 ms, so the squash reads as weight.
  - Recover is 110 ms, so the cloth settle is visible.
  - Total 570 ms vs 530 ms.
- **attack1 (slash)** `70,70,50,80,80,80` -> `50,90,40,60,90,120`.
  - Same 140 ms anticipation, but split as a gather plus a held coil.
  - The smear is 40 ms: one flash, about 2.4 game frames at 60 fps.
  - The impact is 60 ms, plus engine hit-stop on hit (§3).
  - Follow-through 90 ms and settle 120 ms: fast in, slow out.
  - chain_window stays [3,4] and dash_cancel_from stays 4.
- **attack3 (overhead)** `80,80,90,50,60,90,90,90,100` -> `70,70,110,40,60,90,90,90,110`. Same 250 ms
  anticipation, but the apex coil gets the hold. Smear 1 is a 40 ms flash, then smear 2/impact.
- **walk** 8×100, **run** 8×70, **dash** `50,60,60,80` and **hurt** `60,100,120` are unchanged.
- Key-only test GIFs (STANDARD TEST SET, 3-4 keys) use the key timings below. Those values are
  review timings, not game timings.

```json
{"timing": {
  "idle": [220, 140, 140, 220, 140, 140],
  "turn": [250, 250, 250, 250, 250, 250, 250, 250],
  "walk": [100, 100, 100, 100, 100, 100, 100, 100],
  "walk_SE": [130, 110, 100, 110],
  "run": [70, 70, 70, 70, 70, 70, 70, 70],
  "jump": [80, 60, 150, 80, 90, 110],
  "jump_E": [160, 220, 200],
  "slash": [50, 90, 40, 60, 90, 120],
  "slash_SE": [200, 50, 160, 240],
  "attack1": [50, 90, 40, 60, 90, 120],
  "overhead_slash": [70, 70, 110, 40, 60, 90, 90, 90, 110],
  "attack3": [70, 70, 110, 40, 60, 90, 90, 90, 110],
  "dash": [50, 60, 60, 80],
  "hurt": [60, 100, 120]
}}
```

Frame budget at the 60 fps engine tick: 40 ms ≈ 2-3 ticks, 50 ≈ 3, 60 ≈ 4, 70 ≈ 4, 90 ≈ 5-6,
110 ≈ 7, 150 ≈ 9, 220 ≈ 13.

---------------------------------------------------------------------------------------------------

## 2. Global motion rules

### 2.1 Scale facts (56-60 px character, 128 cell)
- 1 sprite px ≈ 0.059 rig units of vertical cog travel, and ≈ 0.051 across.
- Head ≈ 17-20 px. Body below the chin ≈ 30 px. Katana ≈ 34 px on screen.
- The minimum readable motion of a part is **2 px**. A 1 px move reads as jitter unless it is part of
  a travelling wave (ribbons) or a hold.

### 2.2 Squash and stretch (silhouette-box %, body only)
The box is measured on the sprite minus the sword, ribbons and smear. Volume pairs: if height
changes by -h %, width changes by about +h/2 to +h·0.7 %.
- **Rigid:** the katana deforms 0 %. The head deforms ≤ 1 px; it may sink 1-2 px into the collar on
  squash and rise 1 px out of it on stretch. The bun follows the head.
- **Flexible, in order:** skirt hem > sleeves > legs/torso.

| Action / key | Height | Width | Notes |
|---|---|---|---|
| idle f0 / f3 | 0 % (crown −0 / +2 px) | 0 | breath, not squash |
| walk down / up | −4 % / +2 % | +2 % / −1 % | |
| run down / flight | −6 % / +5 % | +3 % / −3 % | flight: legs split, toe points |
| jump crouch | **−12 %** | +8 % | head sinks 2 px into collar |
| jump rise | **+8 %** | −5 % | toes pointed, arms up |
| jump apex | 0 % | 0 | hang, cloth floats |
| jump land | **−14 %** | +10 % | skirt bell flares out 2-3 px each side |
| jump recover | +2 % | 0 | overshoot up 1 px, then idle |
| slash coil (k0) | −6 % | +4 % | crouch on back leg |
| slash impact (k2) | −8 % | **+14 %** | lunge width |
| overhead apex | +6 % | −3 % | up on toes |
| overhead impact | **−12 %** | +10 % | deepest pose in the set |
| dash wind-up / travel / brake | −7 % / +12 % along travel / −8 % | +4 % / −5 % across / +5 % | travel is a stretched frame |
| hurt f0 / f1 | +3 % / −6 % | 0 / +3 % | snap, then buckle |

The guide JSONs approximate these with `["scale","cog",[sx,sy,sz]]`. That is **guide only**: painters
reproduce them as shape, not as a scale.

### 2.3 Secondary motion / overlap: lag in frames behind the body driver

The driver is the cog for bounce, the chest for twist, and the arm for sleeves.

| Part | idle | walk | run | slash / overhead | jump | dash | hurt |
|---|---|---|---|---|---|---|---|
| head (vs cog bounce) | 1 | 1 | 1 | 0 (head leads the twist, eyes on target) | 0 | 0 | 0 (snaps first) |
| bun | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| bow loops | 2 | 2 | 1-2 | 2 | 2 | 1 | 2 |
| scarf ribbons root → tip | 1 → 3 (travelling wave) | 1 → 3 | 1 → 2 | 1 → 3 | 1 → 3 | 1 → 2 | 1 → 3 |
| skirt tails (back) | 1 | 1 | 1 | 1-2 | 1-2 | 1 | 1-2 |
| skirt front panel / side petals | 1 | 0-1 | 1 | 1 | 1 | 1 | 1 |
| sleeve cuffs (vs forearm) | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| sword tip (when not swinging) | 2 | 2 | 2 | — | 1 | 1 | 1 |

Rules:
- **Against velocity, always.** Ribbons, tails, cuffs and bow trail opposite to the motion (bible §2).
  In W/NW that means toward screen-right/up. Never use a fixed world direction.
- **Overshoot, then settle.** After every stop (impact, land, brake, settle), each secondary part
  goes **past** rest by 2-4 px on the next frame. It comes back by half on the following frame and
  rests one frame later. Ribbons show an S-curve during the overshoot: the root is already reversed
  while the tip still trails.
- **Never all at once.** If the body and every secondary part change direction on the same frame,
  the frame is rejected.
- **Amplitudes at sprite scale.** Ribbon tip: idle 2-3 px, walk 3-4, run 4-6, attacks 6-10.
  Bun 1 px (0 in idle except on the top/bottom holds). Bow loops 1-2 px. Skirt tail 2-4 px. Cuffs 2-3 px.

### 2.4 Arcs
- Hands, blade tip and head move on arcs. Check the path of the tip-of-sword and the crown across
  frames (`metrics.py` reports the sword-tip circle-fit RMS). A zig-zag path is a fail.
- Horizontal slash arcs project to an **axis-aligned ellipse with ry = 0.5·rx** (30° camera; the
  circle lies flat). Overhead (vertical) arcs project with ry ≈ 0.87·rx in E/W and collapse to a
  near-vertical streak in S/N. SE/SW/NE/NW are in between (use the tip track, §4.4).

### 2.5 Expressions (rig props → painted face)
- **calm:** idle, walk. Half-lid; small closed mouth; blush.
- **focused (frown):** run 0.5; all attacks 1.0. Brow-down slant; lids 30 %.
- **wide:** jump rise; smear frames at 0.3. Lids up; tiny open mouth.
- **smile:** jump apex 1.0; recover 0.4.
- **hurt:** eyes squeezed (> <-style 2 px lines), mouth open 1 px; f2 blends with frown.
- **blink alt:** idle f3 (every 3rd loop, engine-selected): eye block → 1 px lash line over 2 px, for
  100 ms. Never blink on attack frames.

---------------------------------------------------------------------------------------------------

## 3. Impact, hit-stop and FX (engine + art contract)

Hit-stop is held **on the impact key, not on the smear**. When the hit registers during the smear
frame (the active frame), the engine finishes the smear's 40 ms and then freezes the impact frame.
Holding a smear reads as a blob.

| Event | Hit-stop (60 fps ticks) | Attacker | Victim | Screen shake | FX |
|---|---|---|---|---|---|
| attack1 slash hit | **3** (50 ms) | frozen on impact f3 | frozen in hurt f0 (white flash), ±1 px shake every 2 ticks along the knockback axis | 1 px, 4 ticks, decaying | 3-frame hit spark at the contact point: steel_2 star 5-7 px, then a pink_1 ring, then pink_0 specks. Petal burst (petal_vfx) on kill only. |
| attack2 hit | 4 (67 ms) | impact frame | same | 1-2 px, 5 ticks | spark + 2 petals |
| attack3 overhead hit | **6** (100 ms) | impact f4 | same, shake ±2 px | 3 px vertical, 6 ticks | spark + ground crack line 8-12 px (dark_1) + dust ring (steel_1/steel_0) 3 frames |
| finisher / kill | +2 ticks on top | | | +1 px | petal burst 5-8 petals |
| whiff (no hit) | **0** | plays through | — | 0 | arc only |
| player hurt | 4 ticks on both | — | her hurt f0 flash held + shake ±1 px | 2 px, 5 ticks | white flash is the whole silhouette (steel_2), per spec |
| jump land | 0 (no freeze) | — | — | 0 (1 px only from heights > 2 jumps) | 2 small dust puffs at the feet, 3 frames, steel_1 → steel_0 |
| dash brake | 0 | — | — | 0 | skid dust 2 frames |

- During hit-stop, FX layers and the ribbons' **tips** may keep moving: the engine plays the smear
  tail and spark. The body never moves.
- Danger language (bible): her FX are pink/coral/white, never orange/yellow, never red_2-only.

---------------------------------------------------------------------------------------------------

## 4. Smears — exact specs

Palette roles: `smear_arc = [#eef0f5 steel_2, #f8b5c8 pink_1, #f49ab0 pink_0]`.
- Smears are hard-edged and solid, with **no dark outline**: they read as light.
- There is no dithering and no semi-alpha.
- They are painted **behind** the body unless the arc passes in front of it in that direction (§4.4).
  `tools/hybrid/draw.py smear` / `streak` / `echo` / `speed` implement these.

### 4.1 Blade-arc smear (slash k1 = slash f2; attack2 f2-3; air attack)
- **Span: the full motion, coil → impact.** In saint11's words, "the first frame should do the full
  motion". For attack1 the tip travels about 150° of the swing: tip(f1) → tip(f2) → tip(f3). Draw
  the band from the tip track of f1 (tail) to just short of f3 (lead). The blade itself is drawn at
  the f2 position, sitting in the leading third.
- **Radius:** the outer edge is the blade-tip path, about 30-34 px from the hands at 56 px. The band
  grows inward toward the hands. It never reaches the hands; it stops at 45 % of the blade length.
- **Thickness (taper=lead):** 1 px at the tail, 2 px at 30 % of the span, 4 px at 65 %, 5 px at 90 %,
  then it meets the blade. That is the bible's 3-5 px rule, measured in the leading half.
- **Tones across the band** (outer → inner):
  - a 1 px steel_2 leading rim on the outer edge over the leading 70 %;
  - a pink_1 body;
  - pink_0 on the inner edge and over the whole trailing 30 %.
- **Shape:** a crescent / teardrop. The lead end is blunt and rounded where it meets the blade. The
  tail is a 1 px point. Run lengths along the arc are monotone (R17, no kinks).
- **Impact frame (k2):** keep only the leading 35 % of the arc, as a thin 1-2 px pink_1/pink_0 sliver
  behind the blade. This is the "slowly stabilize". The blade is crisp at the end of the arc.
- **Follow-through (k3):** 0-3 px of pink_0 wisps at the arc tail, or nothing. **No arc on settle.**

### 4.2 Multiple-limb and stretched-limb smears (fast swings)
- **Slash f2:** the arms/sleeves are drawn as **one elongated red shape**. The sleeve cuffs smear
  into a 3-4 px red_1/red_0 streak along the swing toward the coil side; it is an elongated
  in-between, not a copy.
  - One **echo** of the near hand (2×2 skin_1) sits 4 px back along the arc. Hands may stretch 1-2 px.
- **Overhead f3 (smear 1):** the blade, both arms and the sleeves form one stretched shape over the
  top of the arc.
  - The arc band is a **vertical crescent** (§4.4 track) up to **6 px** thick (heavy weapon move).
  - **Complementary flash:** f3's core is steel_2 and f4's core is pink_1 (saint11).
- **Overhead f4 (smear 2 / impact):** keep the lower 40 % of the arc as a 2-3 px sliver ending at the
  tip near the ground.
  - Add a **ground impact line** of 1-2 px dark_1 under the tip, 8-12 px wide, plus a dust ring FX.

### 4.3 Locomotion smears
- **Run (flight frames f3, f7):** the swinging (forward-reaching) leg is a **stretched-limb smear**:
  shin + foot elongated 2-3 px along the swing path, with the shoe drawn once at the lead end.
  - **Motion lines:** 2 lines of pink_0 1 px, 4-7 px long, 3 px apart, behind the back hem and
    behind the shoulder, trailing against velocity. They appear on f3/f7 **only**, once per step.
  - Contact frames (f0/f4) get a tiny dust puff (FX layer, 3 frames): steel_1 → steel_0, 3×2 px.
- **Walk:** no smears. The ribbons and skirt carry the motion.
- **Dash travel (f1, f2):**
  - f1 is a **stretched frame**: the whole body is elongated +12 % along the travel and narrowed
    −5 % across. The sword trails flat behind.
  - f1 **afterimages**: 2 solid flat silhouettes of the f0 pose, offset 6 px and 12 px back along
    the travel (screen space). The near one is pink_1, the far one pink_0. No interior detail;
    behind the body.
  - f2: 1 afterimage at 8 px in pink_0.
  - **Speed lines:** 3-4 lines of 1 px, 8-14 px long, in steel_2 and pink_0 alternating. They start
    at the trailing silhouette edge on f1 and f2.
  - f3 brake: nothing. Skid dust only.
- **Jump:** no smear on rise. Optionally 2 pink_0 1 px motion lines under the feet on rise (f1), 3-5 px
  long, vertical.

### 4.4 Smear geometry per direction (from the guide)
`hybrid/anim/smears.json` is generated by `tools/hybrid/anim/smear_spec.py`. It covers all 8
directions, for `slash_f2`, `slash_f3`, `overhead_f3` and `overhead_f4`.

- **Flat slash (`kind: cut_plane_arc`):** the arc is drawn on the **cut plane**, a horizontal circle
  around the impact hands. It is not drawn on the guide's raised coil track: the coil lifts the blade
  so the anticipation reads, but the arc shows the hitbox sweep.
  - Projection: ry = 0.5·rx. Blade azimuth 123° (coil) → 330° (impact); draw.py angle = −(az + 45°·dir_index).
  - The k1 span is about 186°. The k2 sliver is the last 35 % (≈ 72°).
  - Fields:
    - `draw` is the behind pass.
    - `draw_over` and `front_ranges` cover the part of the arc nearer the camera. That part must
      be painted **over** the body, 1 px clear of the face.
    - `rig_tip_track` is the guide blade tip, for reference.
- **Overhead (`kind: arc`):** an ellipse fitted through the swing tip track
  (`poses/samples/ohS_*`: in-betweens interpolated on the swing pitch, never frames).
  - Where the vertical swing is nearly edge-on (SE, NW), the kind is `polyline`: follow `tip_track`
    as a band with `streak`/`poly`.
- **Demo** (guide frame + draw command, 4x): `hybrid/anim/review/smear_demo_sheet.png`. Use the
  command as a starting point, then hand-correct the crescent's run lengths and thickness on the
  real sprite.

### 4.5 Never
- No smear on idle, walk, settle or hurt.
- No soft gradient or alpha "blur".
- No smear wider than 6 px.
- No outline around smears.
- No red smear: red is the enemy-telegraph neighbourhood, and her FX are pink/white.

---------------------------------------------------------------------------------------------------

## 5. Per-action direction

Notation:
- Frame `fN (ms)`.
- **cog px**: body vertical offset vs standing idle, with negative = lower on screen.
- **lag**: frames behind the driver.
- Directions: pose JSONs are authored facing S in character space and yawed per direction, so the
  same key index holds in all 8.
- The thumbnails are side views (facing →) unless noted.

### 5.1 IDLE (6 f, loop, 1000 ms) — `idle_f0..f5`

```
 f0 exhale(hold)   f1 inhale     f2 inhale     f3 TOP(hold)   f4 exhale     f5 exhale
      @               @             @   ^          @  ^           @             @
     /|\_            /|\_          /|\_  ^        /|\_ ^         /|\_          /|\_
     / \  \sword     / \  \        / \   \        / \   \        / \  \        / \  \
 crown 0          +1            +2            +2             +1            0       (px, up)
```
- **Beat:** a calm breath with weight on one hip.
  - The chest leads. The shoulders rise 1 px on f2-f3.
  - The head nods 1 frame late. The hips rock ±1° into the weight hip.
- **Bounce:** the crown travels 2 px (0, +1, +2, +2, +1, 0) and the hem/knees 1 px. The extremes are
  held 220 ms.
- **Overlap:**
  - bun 1 f behind the head; bow loops 2 f;
  - ribbons a travelling wave, root 1 f → tip 3 f, tip sway ±2-3 px;
  - skirt tail 1 f (±1-2 px); sleeve cuffs 1 f (±1-2 px), left and right offset by 1 f so they never
    mirror;
  - sword tip drifts ±1 px, 2 f behind (a relaxed hand).
- **Expression:** calm. Blink alt on f3 every 3rd loop.
- **Accept:** in a 4x GIF you see breath plus four independent secondary motions. If you can count
  the loop by one moving part, it is too mechanical.
- **turn_<DIR>** = the idle f1 key (neutral mid-breath) in all 8 directions: `turn.json`.

### 5.2 WALK (8 f × 100 ms, loop) — `walk_f0..f7`; test keys `walk_SE_k0..k3` = f0..f3

```
 f0 CONTACT(L)   f1 DOWN          f2 PASSING       f3 UP            (f4-f7 mirror, R leads)
     @              @                 @               @
    /|\            /|\               /|\             /|\
   / |  \         /  \              / |              / |
  /   \_         /    \_ (knee bend)  |\             |  \_ (toe-off)
 cog -1         -3 (weight)      -1               +1
```
- **Feet:**
  - Contact: heel strike with the toe up 14°. The rear foot rolls onto its toe (heel 30°).
  - Down: the stance knee bends; this is the lowest frame.
  - Passing: the swing foot lifts 2-3 px, knee forward.
  - Up: the stance leg is straight on the ball of the foot. Highest frame.
  - Stride ±0.32 (6-7 px heel spread on screen in E).
- **Bounce:** contact −1, down −3, passing −1, up +1 (4 px range). On her short legs this is what sells
  the bounce of the illustration.
- **Body:**
  - hips yaw ±8° with the leading leg; the chest counter-rotates ±10°;
  - the swing-side hip drops 3° on down;
  - slight forward spine 4°;
  - cog sways ±1 px over the stance foot.
- **Arms:** the free right arm swings ±22° opposite to the legs, 1 f behind. The sword arm swings ±12°.
  The blade angles down-out (de 38°) and swings ±8°, 2 f behind the arm.
- **Overlap:**
  - head 1 f behind the bounce (the bob lands after the contact);
  - bun 1, bow 2;
  - ribbons trail back with a per-step flutter, tip 3-4 px;
  - skirt tail lifts 2-3 px the frame after down, then drops on up;
  - the front panel flicks with the leading knee;
  - cuffs 1 f behind the arm swing.
- **Smear:** none. **Expression:** calm, with a slight smile allowed in town.

### 5.3 RUN (8 f × 70 ms, loop) — `run_f0..f7`

```
 f0 CONTACT    f1 DOWN(squash)   f2 PUSH-OFF     f3 FLIGHT(stretch)  (f4-f7 mirror)
     @  ~~        @  ~~              @  ~~            @ ~~~
    /|\~         /|\~              _/|\~             /|\~~
   /  \_        /  \               /  \__          _/   \___   <- stretched swing leg smear
 cog -1         -4                 -1                +2
```
- **Lean:** spine 20° forward, chest 5°. The head counters −12° so the face stays readable. The cog
  is 1-2 px forward.
- **Bounce:** contact −1, down −4, push −1, flight +2 (6 px range). Squash −6 % on down, stretch +5 %
  in flight.
- **Arms:** the free arm pumps ±40° with the forearm bent 70°. The katana is held low and trails
  back almost level (az 72° back, de 12°), swinging ±6° 2 f behind. It breaks the silhouette behind
  her in every direction.
- **Overlap:**
  - ribbons stream back near shoulder height, 1.5-2 H long, two flutter waves per loop;
  - skirt tails stream back 18° and kick up 1 f after the down;
  - cuffs trail 28° ± 8°;
  - bun 1 f and bow 1-2 f behind the bounce.
- **Smear:** f3/f7 stretched swing leg plus 2 motion lines (§4.3). Contact dust puff on f0/f4.
- **Expression:** focused (frown 0.5).

### 5.4 JUMP (6 f, root-locked) — `jump_f0..f5`; test keys `jump_E_crouch|apex|land` = f0, f2, f4

```
 f0 CROUCH       f1 RISE          f2 APEX (refs/3)    f3 FALL           f4 LAND           f5 RECOVER
                    \@/  ^          _@_ ~~ petals         @              
   ~~@~~            |    |        </|\>  cloth up       \/|\/ cloth up                       @
   _/|\_            |               / \_                 / \             __@__             /|\
   /   \           / \  (toes)                          /   \            _/|\_  (flare)    /  \
 body -5 px       +2               0  (engine z 16)     +1               -6                -1
 squash -12%      stretch +8%      hang 150 ms          cloth lifts      squash -14%        overshoot
```
- **f0 crouch (80):**
  - cog −5 px; spine 13° forward, chin up (eyes on the jump);
  - arms swing back (R 40°, L 30°), sword trailing back-low;
  - the skirt bell widens 2 px. The ribbons are still falling from the previous state (1 f lag).
- **f1 rise (60):**
  - legs fully extended, toes pointed (heel lift 55-60°);
  - arms thrown up and forward, blade up-forward;
  - **cloth drags DOWN**: ribbons hang, the skirt hem points down, cuffs hang below the hands;
  - the bun tips back 1 px. Expression wide.
- **f2 apex (150):** the refs/3 leap.
  - Arched back, chin up, the lead leg straight, the trailing leg bent back;
  - the cloth **floats up**: petals flare, ribbons lift, cuffs flare up. Expression smile.
- **f3 fall (80):**
  - legs reach down, arms out for balance;
  - **cloth lifts UP above her**: side petals flare up 30°, tails up, ribbons rise behind the head 3-5 px;
  - the bow loops flip up. Expression wide 0.5.
- **f4 land (90):**
  - cog −6 px, squash −14 %; feet wider, knees out; spine 14°;
  - arms down and forward for balance;
  - **cloth keeps falling** (lag 1): the skirt bell flares outward 2-3 px each side and the ribbons
    drop on the shoulders;
  - bun +1 px down, bow loops flop forward. Dust puffs. Expression frown 0.8 (effort).
- **f5 recover (110):** cog −1, then back to idle.
  - Cloth **overshoots up** 2 px (ribbons swing back), then the idle takes over.
  - Expression smile 0.4.
- Engine: z offsets `[0,10,16,8,0,0]`. The shadow scales `[1,.9,.8,.9,1,1]` and stays on the ground.
- **Accept:** the crouch → rise height range is ≥ 18 % of the body height (metrics flags < 8 % as weak).

### 5.5 SLASH (attack1, 6 f) — `slash_f0..f5`; test keys `slash_SE_k0..k3` = f1, f2, f3, f4

Horizontal two-handed cut from her RIGHT (−X) across the front to her LEFT (+X), the katana side. The
arc is flat (ry = 0.5 rx on screen).

```
 f0 GATHER (50)   f1 COIL k0 (90)        f2 SMEAR k1 (40)            f3 IMPACT k2 (60+hitstop)  f4 FOLLOW k3 (90)   f5 SETTLE (120)
                  blade up behind R       ((((((======>  blade      blade at far end          blade past, low     low guard
    @/             \@  sh.                 @ /  full arc            @-------<                 @                   @
   /|\             /|\ (twist R)          /|\=  coil -> impact     /|\ (unwound L)           /|\  (overshoot)    /|\
   / \            _/  \ (weight back)     /  \_ (lunge starts)    _/    \___ (full lunge)    /    \__            / \_
 cog -1           -3                      -2                       -3                         -2                   -1 (overshoot)
```
- **f0 gather:**
  - torso turns 18° to her right, hips 8°;
  - hands rise toward the right shoulder, blade tip up/back;
  - head counter-turned so the eyes stay on target. Frown.
- **f1 COIL (k0), held:**
  - the deepest twist: chest −34°, hips −18°;
  - the weight sinks onto the back (right) leg, cog −3 px; front toe light;
  - the blade is raised behind her right shoulder (tip up-back);
  - the head turns hard to the target and the chin dips: a **glare**;
  - **secondaries trail to her left** (Z +12): ribbons, cuffs, tail;
  - squash −6 %.
- **f2 SMEAR (k1), 40 ms:**
  - the body is half unwound (chest +2°). The lunge starts: front foot slides 2 px, back heel lifts;
  - **blade straight ahead, at mid-arc**;
  - **full arc smear** from the coil tip to near the impact tip (§4.1), plus the arm/sleeve elongated
    in-between and the hand echo (§4.2);
  - the secondaries still point where the body WAS (to her right/back, Z −15, tips the most) because
    they lag 1 f;
  - expression frown + wide 0.3 (the eyes snap open).
- **f3 IMPACT (k2), 60 ms + hit-stop:**
  - **full lunge** (width +14 %, cog −3 px), chest +24°, hips +14°, back heel up 22°;
  - the blade is at the far end of the arc, edge leading, crisp;
  - a thin smear sliver behind it (§4.1);
  - the ribbons whip around: root reversing, tips still trailing (S-curve);
  - **this is the readable pose: silhouette check required.**
- **f4 FOLLOW-THROUGH (k3), 90 ms:**
  - the blade carries past to her left-back and drops (the wrist rolls);
  - **the chest overshoots** to +36° while the hips stay at +18° (overlap of body sections);
  - cog rises 1 px;
  - **secondaries overshoot past** (Z +10): the ribbons swing out to the front-left 6-10 px, cuffs flare,
    skirt tail swings, bow loops flip;
  - frown 0.6.
- **f5 SETTLE, 120 ms:**
  - recover on a **different, lower arc** into the low guard (blade forward-down);
  - cog 1 px overshoot down; the secondaries settle halfway;
  - frown 0.4.
- Hit-stop 3 ticks on f3 (§3). Chain window f3-f4. Dash cancel from f4.

### 5.6 OVERHEAD SLASH (attack3, 9 f) — `overhead_f0..f8`

```
 f0 DIP   f1 RISE   f2 APEX COIL (hold)   f3 SMEAR1 (40)       f4 SMEAR2/IMPACT (60+6 ticks)   f5 HOLD    f6 REBOUND   f7 RECOVER   f8 SETTLE
            |  /         |/                 ___                    @                          cloth      blade +8°    rise         guard
   @_      @/           @  (on toes)       /   \  vertical        /|\  blade down to ground    falls
  /|\=    /|\          /|\ arched back    @  arc  crescent       / \___  crack + dust ring
 -2        0            +1                 -1                     -5                          -5          -4           -2           -1
```
- **f0 dip (70):** cog −2 px, squash −5 % (anticipation goes opposite: down before up). Blade forward-up.
- **f1 rise (70):** up onto the toes; the blade comes vertical; the cloth drags down (lag 1).
- **f2 APEX COIL (110, the "pause before impact"):**
  - hasso-style high guard: blade up and back past the left side of the head (the rig `overhead` pose);
  - arched back, stretch +6 %, heels up;
  - ribbons and tails lifting late (still rising, 1-2 f lag). Frown + wide 0.3.
- **f3 SMEAR 1 (40):**
  - the blade passes the top-front of the arc;
  - **vertical crescent** up to 6 px with a steel_2 core;
  - arms and sleeves form one stretched shape;
  - the body pitches forward 12°; the cloth still up.
- **f4 SMEAR 2 / IMPACT (60 + 6 ticks):**
  - the blade is down in front, tip near the ground;
  - **deepest squash** −12 %, cog −5 px, spine 22°;
  - the lower 40 % of the arc remains as a sliver with a pink_1 core (complementary flash);
  - ground crack + dust ring FX; screen shake 3 px.
- **f5 impact hold (90):** the same body. **The cloth keeps falling**: ribbons drop forward over the
  shoulders, tails flop, bow loops flop forward 1-2 px. This is the overlap frame that sells weight.
- **f6 rebound (90):** the blade bounces up 8°, cog −4; the secondaries overshoot forward/down.
- **f7 recover (90) and f8 settle (110):** back to the guard on a lower arc. The cloth settles with a
  1 px overshoot.

### 5.7 DASH (4 f) — `dash_f0..f3`

```
 f0 WIND-UP (50)     f1 TRAVEL A (60)                         f2 TRAVEL B (60)          f3 BRAKE (80)
    @                ==  ==  ~~~@~~~                            =  ~~@~~                  @\  ribbons/skirt
   /|\ (lean back)   pink afterimages x2  ___/|\___ stretched   1 afterimage              /|\  flop FORWARD
   / \_  -3 px        speed lines                 \_  -2 px                    -2       _/  \  skid dust  -4
```
- **f0:** a 1-frame anticipation the other way: lean back 6° and crouch −3 px. Sword pulled back.
- **f1 / f2:**
  - spine 30° forward, head up; lead leg reaching, trail leg kicked high;
  - the blade trails level behind (iaido dash);
  - ribbons and tails stream fully back; cuffs 45°;
  - **stretched frame, afterimages and speed lines** (§4.3).
- **f3 brake:**
  - lean back 14°, squash −8 %; front foot planted skidding with the toe up;
  - **all cloth overshoots forward**: ribbons fall over the shoulders, the skirt front swings out,
    cuffs forward, the bow loops flop forward;
  - frown 0.7.
- The engine owns the travel and the i-frames. The sprite never translates.

### 5.8 HURT (3 f) — `hurt_f0..f2`

```
 f0 FLASH (60)                   f1 RECOIL (100)                f2 RECOVER (120)
  \@  head snaps back             @   buckle, shake +-1 px        @   hunch, guard returning
  /|\_ arms flung  (white)       /|\                             /|\
  / \                            / \_                            _/ \_
```
- **f0:**
  - a **solid steel_2 silhouette flash** (spec), drawn as a whole-sprite recolour of this pose;
  - the head snaps back first (lag 0); spine arched back 18°; arms flung out; blade thrown wide;
  - the cloth lags **forward**, toward the attacker.
- **f1:**
  - normal colours; the body buckles (−6 % height, cog −2 px) and is pushed 1 px back;
  - the victim shakes ±1 px during the attacker's hit-stop;
  - the secondaries peak forward: ribbons 6-8 px, bun and bow tip forward.
- **f2:** a hunched recover. The cloth swings back past rest. Expression hurt blending into frown.
- Hurt cancels everything (spec), and nothing cancels hurt.

---------------------------------------------------------------------------------------------------

## 6. Direction notes for the 8 views
- **S, SE, SW (facing camera):**
  - slash and overhead arcs pass **in front** of the body: draw the arc `over`, but never over the face;
    cut it 1 px clear of the eyes;
  - lunge and impact keys grow DOWN the cell (24 px of room below the pivot);
  - the ribbons fan to the far side (rig rule).
- **E, W (profile):**
  - every lean and bounce is fully visible, so these are the hardest directions to cheat. Review E
    first for the timing, and SE first for the look;
  - horizontal arcs are flat ellipses (ry = 0.5 rx); the overhead is a near-circle (ry ≈ 0.87 rx).
- **N, NE, NW (back):**
  - the face is hidden, so the acting is the **bun, bow and ribbons**. Their lag amplitudes are +1 px
    over the front views;
  - the arcs pass behind or over the head: the arc draws behind the body and above the bun.
- **The same frame index for every key in every direction.** The bob, the down frames and the impact
  share the same index (pilot A2). `metrics.py` lag/overlap checks are run per direction and must
  agree within 1 f.

## 7. Production recipe (who does what)
1. **TA:** render guides from `hybrid/anim/poses/ta/<pose>.json` (all 8 directions via `dir_override`),
   or full sequences via `--anim-json` (§9). Passes: clay, id, mask, joints.
2. **Gemini:** paints the keys from the guide plus `concept/chibi_iso_v5.png` as the first ref. The
   prompt states the beat, the expression and the overlap directions from §5. Ask for the pose
   energy of refs/2 and refs/3.
3. **Claude (hand pixel):**
   - locks the static cels (face, bow, bun) at whole-pixel offsets;
   - paints the smears, streaks, echoes and motion lines with `tools/hybrid/draw.py` from
     `smears.json`;
   - does the ribbon S-curves and the overshoot frames;
   - fixes the arcs.
4. **Review (holistic):**
   - `gifs.py all` (all directions, 1x/4x, grass/grey, slow 4x with key stamps) and `sheets.py set`;
   - `metrics.py` flags: stiff, no_smear, weak squash, lag;
   - director-style judges score the **set in motion**. Gemini is triage only (it overrates).

## 8. Acceptance checklist (Animation Director gate)
- [ ] Timing matches §1. The holds are visible in the slow GIF.
- [ ] Bounce amplitudes per §5, ± 1 px. Idle crown ≥ 2 px, walk ≥ 4 px range, run ≥ 6 px.
- [ ] Squash/stretch per §2.2, ± 3 %. Volume-paired; head and katana not deformed.
- [ ] Every secondary part lags per §2.3. Overshoot after every stop. No frame where everything
      reverses together.
- [ ] The slash k1 smear spans the full arc. It is 3-5 px (6 px for the overhead), crescent-shaped,
      monotone runs, palette-only, no outline. Impact sliver ≤ 35 %. No arc on settle.
- [ ] The impact pose reads as a black silhouette at 1x. Hit-stop is on the impact frame, not the smear.
- [ ] The key indices are identical across all 8 directions.
- [ ] Expressions per key (§2.5).

## 9. Pose JSON format (`dirpose/1`) and converters
- `hybrid/anim/poses/<name>.json` holds `{"format":"dirpose/1","name","dirs","ops":[...],"intent":{...}}`.
  - The ops are applied in order in **character space** (she faces −Y, +X = her left, +Z up), with
    the rig's own helper functions.
  - Op list and sign conventions: docstring of `tools/hybrid/anim/pose_preview.py`.
  - Examples: `["move","cog",[0,0,-0.17]]`, `["rot","spine","X",20]` (lean forward),
    `["feet","L",[x,y,z],yaw,heel,toe]`, `["two_hand",center,blade_dir,edge,elbow_out]`,
    `["sword",az,de]`, `["chain","scarf.L","Z",[...]]`, `["scarf_run",phase]`, `["props",{...}]`.
  - `intent` carries the beat, ms, cog px, squash and smear/hit-stop flags.
- **Sources:** `tools/hybrid/anim/make_poses.py`. Edit there, never by hand.
- **Convert + check:**
  `Blender -b --factory-startup -P tools/hybrid/anim/pose_preview.py -- [--only 'slash_*'] [--dirs SE,E] [--no-render]`.
  It writes three outputs:
  - `hybrid/anim/poses/ta/<name>.json`: the TA guide-rig format. Absolute (`"base": null`), all
    bones as `{"quat","loc"[,"scale"]}`, and `dir_override` for the 7 other directions (presentation
    turn + camera-flat blade roll);
  - `hybrid/anim/poses/rig/<name>.json`: rig-native `[qw,qx,qy,qz,lx,ly,lz]`;
  - `hybrid/anim/preview/<name>_<DIR>.png` + `.json`: blade guard/45 %/70 %/tip, hands and bun tip
    in cell px.
- **Verified:** `render_guides.py --pose hybrid/anim/poses/ta/slash_SE_k1.json --dirs SE,E` on the
  TA's `hybrid/guide/guide.blend` reproduces the same stance and blade as the preview.
- **Sequences for `render_guides.py --anim-json`:** `hybrid/anim/poses/ta/anim_<idle|walk|run|jump|slash|overhead|dash|hurt>.json`.
- **Standard test set poses:** `turn` (8 dirs), `walk_SE_k0..k3`, `slash_SE_k0..k3`,
  `jump_E_crouch|apex|land`.
- **Known guide limits (fix in paint, not in the rig):**
  - the guide's squash is a uniform cog scale;
  - the rig's ribbon solvers do not check arm collisions in non-idle poses (the rig's `scarf_clear`
    does);
  - slash coil blades can tuck behind the head in N/NE: paint the blade at least 3 px clear.
