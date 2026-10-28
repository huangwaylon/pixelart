# STYLE TARGET: hybrid sprite pipeline (art director)

Date: 2026-10-25. Owner: art director. This file is the look contract for every strategy, polisher and judge in `hybrid/`.
- Look target: `concept/chibi_iso_v5.png` and its pixelization `docs/palette_v1_vs_v2_terrain.png`.
- Locks: `hybrid/lock/` (manifest `hybrid/lock/LOCK.json`) and `hybrid/lock/pixel/` (manifest `stamps.json`).
- Where this file conflicts with `docs/design_bible.md` on APPEARANCE (head scale, bow placement, shading), this file wins for the hybrid sprites. The bible still wins on costume content, palette, pivot, cell size and timing.

---

## 1. Why iso_v5 and its pixelization look good

### 1.1 Measurements (iso_v5, 928x1120; `hybrid/analysis/iso_v5_measure.png`)
Unit H = skull height, from the hair-dome top (y 225) to the chin (y 522) = 297 px.

| Landmark | y | In H | At a 60 px sprite |
|---|---|---|---|
| bow top | 130 | +0.32 H above the skull | row 0 |
| skull top | 225 | 0 | ~7 px |
| brow (bang tips) | 440 | 0.72 H down the head | |
| eye centre | 468 | **0.18 H above the chin** | eyes 4-5 px tall |
| chin | 522 | 1.0 H | ~29 px |
| collar bottom | 600 | 0.26 H below the chin | |
| corset band | 655-745 | 0.30 H tall | 5-6 px dark band |
| front hem | 835 | | |
| sole | 950 | 1.44 H below the chin | 60 px |

- Sole to skull top = **2.44 H** (the "2.5 heads"). Sole to bow top = 2.76 H.
- **Head + bun + bow = 48 % of the silhouette height.** The skull alone is 36 %.
- Head width is 337 px = 1.13 H. That is the widest thing on her except the skirt flare and the sword.
- The body under the collar is narrower than the head. Only the bell cuffs and the skirt tails reach head width.
- The face is a small window at the bottom of a huge hair dome. Hair covers the top **72 %** of the head. The eyes sit at 0.18 H above the chin, so the lower face is tiny.
- Sprite scale (60 px tall):
  - skull H ≈ 22 px, head ≈ 25-26 px wide
  - bow + bun ≈ 7-10 px above the skull
  - body below the chin ≈ 31 px
  - legs below the front hem ≈ 7-8 px

  This is **bigger than bible §3** (H 17 px at 56 px). We follow iso_v5, and the stamps in `hybrid/lock/pixel/` are built at this scale.

### 1.2 Shape language
1. **Three overlapping circles on top:** skull dome, bun, and two bow loops. They form a clear size hierarchy: big dome, medium bun, two upright ears. That cluster is her silhouette ID from every direction.
2. **Soft bell masses below:** collar funnel, bell cuffs and petal skirt. The overall mass is a stable teardrop/pyramid with a big round top.
3. **Few sharp accents:**
   - collar points
   - skirt-tail points
   - the bow loop tips
   - one long **straight katana diagonal** that counters all the round forms and extends the silhouette. The sword is what makes the pose read as "swordswoman", not just "doll".
4. **Value stacking:**
   - dark hair mass on top
   - saturated red in the middle, split by one dark corset band
   - pale skin legs at the bottom
   - red bow on dark hair: the highest-contrast spot after the eyes
5. **Big, flat clusters.** Almost no interior lines: thin dark-brown line art, 2-tone cel shading per material, one soft sheen arc on the hair. Detail goes only to the face (eyes, lash, blush), the bow and the buckles.
6. **Face:** big blue eyes, wider than tall and half-lidded, set low and wide. A heavy dark upper lash with an outer flick. 1 glint. Blush directly under the outer eye corners. A tiny mouth, no nose.
7. **Thin pink ribbons in soft S-curves.** They are delicate lines, never planks, and they add motion even at rest.

### 1.3 Why the pixelization (`docs/palette_v1_vs_v2_terrain.png`) still works
The big masses survive the downsample:
- a hair block with a dark outline
- a red bow on top
- a pale face window with two blue eyes
- red body + dark corset band
- pale legs
- a long thin blade

The read comes from **silhouette and value blocks**, not from detail. Its weaknesses are exactly what the hand pass must add: a 1 px blade, mushy eyes, and shapeless ribbons.

---

## 2. What to AVOID: the rejected round-9 sprites (`renders/model_round_9`, `hybrid/analysis/round9_iso_8dir_crop6x.png`)

1. **Render-noise shading.** Coral and crimson blotches all over the dress. They are random light-bake clusters, not designed folds. Every shade cluster must be a deliberate shape: fold wedge, cuff shadow, underside.
2. **Milk-chocolate / orange helmet hair.**
   - Hair base too light and uniform.
   - Bangs cut straight across like a bowl.
   - The dome reads as a cap.

   Hair must read DARK with a lit upper-left: hair_0 ≥ 45 %, hair_1 ≤ 50 %, hair_2 only as one sheen crescent (≤ 12 px per head).
3. **Dead face.**
   - 2 px square eyes placed high, no lash line, no blush.
   - Face window too big and too high.

   Use the locked eye: 4 px wide, lash row + 3 iris rows, glint, blush below the outer corner, set low.
4. **Snowman bun / "brown ball over a red bell" back views.** Stacked spheres, the bow as a red scribble with dark specks. The bun overlaps the skull on a curve, and the bow loops rise above the bun as clean upright ears (`head_N`).
5. **Body as wide as the head.** In round 9 the red bell (31 px) is wider than the head (23 px), so she reads as a dress with a head. In iso_v5 the head dominates.
6. **Continuous pink rim**, read as a second outline. The rim is ≤ 60 % of the contour, broken, and never baked into stamps.
7. **Plank / stick ribbons, sawtooth / icicle hems, box feet.** Ribbons are 1-2 px S-curves that taper. Hems are petals with varied step sizes. Feet are strappy heels with a heel point and a skin ankle.
8. **Sword failures:**
   - a hilt reading as a pole through the thigh
   - the hook as a closed ring or a knuckle-bow
   - a floating sword in NE/NW
   - a 1 px blade

   Use the locked katana stamps: 2 px blade, a small crescent kagi with a transparent notch, a visible fist.
9. **Stiff idle.** A 1 px bob, phase unsynced across directions (`pixel/idle_PILOT_REPORT.md`). See §5.
10. **3D-render look in general.** Soft AA edges, per-pixel light noise, and shapes that change shape frame to frame (boiling). Static cels (head, bow, katana hilt) are pasted stamps, byte-identical across the frames of a direction.

---

## 3. Lock decisions (also in `hybrid/lock/LOCK.json`)

- **Sword hand: LEFT.**
  - refs/1 and bible §0.5. refs/2's two-handed grip sits on her left side; refs/3 is ambiguous; iso_v5 and turnaround v6 are mirrored, per the bible. So the refs do not clearly disagree.
  - Attacks may use a two-handed grip.
  - Gemini fights this (its prior is the right hand). Generate in **mirror space** and flip back. See LOCK.json `handedness_trick`.
- **Bow: centred on the front base of the bun**, both loops rising above it, as the lock sheet draws it in all 8 views.
  - The bible's "offset to her right" is dropped, so the head is symmetric.
  - Head stamps for W/NW/SW = mirror of E/NE/SE + hand re-light.
  - **Bodies are never mirrored** (sword, slit, ornament and thigh strap are asymmetric).
- **Lighting is camera-locked in every direction:** key light top-left (hair_2 sheen on the upper-left), pink_0 rim back-right (added last on the whole silhouette).
- **Collar:** always prompt "tall stiff flared collar open at the front". At sprite scale it is a 2-3 px red band round the jaw with a pointed flare tip each side.
- **Camera:** the lock sheet is flatter than the 30° game camera. The lock gives identity; the 3D guide gives camera and pose.

---

## 4. The lock assets

### Illustration lock (Gemini, in the iso_v5 style): `hybrid/lock/`

| File | Content | How it was made |
|---|---|---|
| `turn8_iso.png` (+ `turn/turn_<DIR>.png` cells) | 8-direction turnaround, one image, same scale, LEFT-hand katana | Pixal3D mesh rendered from the iso camera in 8 directions (`hybrid/guide/p3d_iso/`, `tools/hybrid/render_p3d_iso.py`), then a Gemini trace (`wip/turn8_v2_pro`), then a mirror-space style refine (`wip/turn8_m_pro1`), then a flip. Hand paint-over: NE extra sword removed, E far-hand blade added. |
| `head_sheet.png` | head front, 3/4, back (large) + profile, back (small) | Gemini, iso_v5 style (`wip/face_v1`) |
| `expressions.png` | calm, determined/combat, effort shout, hurt (one eye shut, gritted teeth, sweat), happy | Gemini (`wip/expr_v1`) |
| `bow_bun.png` | bun + bow front, side, back, high iso | Gemini (`wip/bow_v1`) |
| `katana.png` | full katana, hilt close-up, iso view; diamond-wrapped handle, straight bar + crescent kagi as in refs/1 | Gemini (`wip/katana_v1`; v2 rejected: giant sickle) |
| `lock_overview.png` | all of the above on one page | |

All prompts are in `hybrid/lock/prompts/`, and every attempt is in `hybrid/lock/wip/`. The Argon critiques are `wip/critique_*.txt`. They are reference only: Argon misread compass directions and handedness several times on the first pass.

### Pixel lock (Claude, hand-typed `.pix`): `hybrid/lock/pixel/`
Palette-locked: 0 off-palette pixels, binary alpha. Rendered PNG + `_x8` previews sit next to each source.

- `head_{S,SE,E,NE,N,NW,W,SW}`:
  - canonical sprite-scale head with face, hair, bun and bow, 26 px wide
  - one canvas origin for all of them (row 0 = bow top, centre col 12.5)
  - S, SE, E, NE and N are authored by hand
  - W, NW and SW are mirrors plus a re-light (sheen moved back to the upper-left)
- `bow_{S,SE,E,N}`: bow + bun-top cels cut from the heads, for 1 px lag offsets in secondary motion.
- `katana_down`, `katana_idle_2to1`:
  - hilt with red diamond wrap and steel kashira
  - guard bar with a pointed end
  - small crescent kagi with a notch (≥ 3 px, never a ring)
  - habaki, 2 px blade (steel_0 spine + steel_2 edge)
  - mirror for the other side
- `fit_8dir_3x.png`: the heads on an auto-pixelized lock body, on slate, dirt and grass. Only a scale and consistency check: the body is not lock quality.
- Generators and history: `tools/hybrid/lock/stamp_history/`. The `.pix` files are the source of truth.

---

## 5. Animation look (the user's direction, which every judge applies)

### 5.1 Motion principles
- **Squash and stretch.**
  - Jump crouch: body −2 to −3 px tall, +2 px wide.
  - Apex / launch stretch: +2 to +3 px tall.
  - Land squash is held 1-2 frames.
  - Walk "down" frame: −1 to −2 px with knees bent. "Up" frame: +1 px with heels up.
  - The head stamp stays rigid. Squash comes from the torso, skirt and legs, plus a 1 px head drop.
- **Anticipation.** Slash k0 is coiled: blade drawn back past the shoulder, torso twisted away, weight on the back foot, sleeves and ribbons pulled the other way.
- **Hit-stop.** The impact frame is held about 2 frames (80-100 ms), with no secondary motion on the held frame. Secondary motion resumes on the next frame with overshoot.
- **Follow-through and overlap.**
  - Bow loops, bun strands, ribbons, skirt tails and sleeve cuffs lag 1-3 frames.
  - They overshoot past rest, then settle over 2-3 frames.
  - They always trail **against velocity**.
- **Arcs.** The blade tip, hands, head and ribbon tips move on arcs, never straight lines. Check them with a tip-path overlay.
- **Timing.** Fast actions are 1-2 frames (40-60 ms); holds are 80-150 ms (`docs/anim_spec.json` ms arrays). Idle is NOT a 1 px bob:
  - breathing goes through the shoulders and collar
  - ribbons drift
  - the sword tip sways 1 px
  - a weight shift every cycle
  - a blink

### 5.2 SMEARS (required for fast movement)
Frames follow `docs/anim_spec.json` `smear_frames`. Palette roles follow `palette.json` `smear_arc`.
- **Blade-arc smear (every slash active frame):**
  - A crescent that follows the blade-TIP path from the previous key to the current one.
  - 3-5 px thick at the leading edge, tapering to 1 px at the tail.
  - Core steel_2, outer edge pink_1 then pink_0. Hard alpha, no dither on the character.
  - It covers the hitbox area. The real blade is drawn at the leading end of the arc, or is replaced by the smear.
- **Stretched / multiple-limb smears (fast swings):**
  - The swinging arm + sleeve stretched 1.5-2x along the motion, or 2-3 offset copies of the cuff and hand along the arc.
  - Copies are drawn in red_3 / pink_0 silhouettes, with no outline on the trailing copies.
- **Run / dash smears:**
  - Speed lines: 1 px pink_0 / steel_1 horizontal streaks behind her, 4-10 px long.
  - Leg smear: a blurred stride arc in skin / dark_1 on the passing frame.
  - Ribbons and skirt tails stretched flat behind her, up to 2 H.
  - Dash after-image (pink_0 at 50 %) is engine-side, per the bible.
- **Motion lines where they fit:**
  - jump take-off: vertical streaks under the feet
  - landing: dust ticks (steel_1 / skin_2, 2-4 px)
  - impact: a 1-frame white (steel_2) spark star on the hit point
- **Smears never cover the face stamp.** The eyes and bow stay readable on every frame.

### 5.3 Standard test set (fixed names)
- `turn_<DIR>.png`
- `walk_SE_k0..k3`: contact, down, passing, up
- `slash_SE_k0..k3`: coil, SMEAR, impact hold, follow-through
- `jump_E_{crouch,apex,land}`

All in a 128 cell, pivot (64,104), character 56-64 px, locked palette. The hi-res source sits next to each sprite.

---

## 6. RUBRIC (0-10 per criterion)

Judges are director-style: art director, game director, and animation director. Gemini is triage only, because it overrates: the idle pilot got Gemini 8.4 vs AD 6.2, and in this lock pass Argon misread compass directions and handedness on the first turnaround pass.

**Every judge reviews HOLISTICALLY:**
- one contact sheet with all 8 directions × all frames, at 1x and 3x, on slate (#24202c), dirt and grass
- the GIFs in motion: per direction, and all 8 at once
- the lock refs (`lock_overview.png`, `pixel_lock_sheet.png`) and the look target next to the sprites

Judging single frames in isolation is not allowed.

| # | Criterion | 4 = reject | 7 = acceptable | 9 = ship |
|---|---|---|---|---|
| 1 | **illustration_appeal** (vs iso_v5) | reads as a 3D render / doll in a dress; head < 40 % of height; noisy shading | iso_v5 massing (head ≈ 45-50 %, dark dome, red bow ID, face window low); clean clusters | you could swap it for a downscaled iso_v5 and prefer the sprite; the face has charm at 1x |
| 2 | **cross_direction_consistency** | head size, hair value, bow shape or eye design change between directions; facing ambiguous (NE reads as E, SW as S) | same stamps in all 8; baseline and pivot locked; facing tells per bible §2 | the turn GIF rotates like one solid character; no pops |
| 3 | **cross_frame_consistency** | the head boils; the hilt or hook changes shape; the palette drifts | static cels byte-identical; only intended parts change | animated parts keep volume; zero flicker or orphans |
| 4 | **pose_fidelity_to_guide** | pose, weight or timing differs from the 3D guide / anim_spec; wrong hand | key poses match the guide silhouette (IoU ≥ 0.8); key frames on the same index in all directions | guide pose pushed further for appeal (stronger line of action) without breaking its timing |
| 5 | **motion_expressiveness** | stiff, 1 px bobs; no anticipation; no smear on slashes | squash/stretch per §5.1, anticipation, hit-stop, secondary lag 1-3 frames, blade-arc smear on every active frame, run smears | lively and weighty; smears sell speed; overlap settles beautifully; refs/2-3 energy |
| 6 | **pixel_cleanliness** | AA halos, semi-alpha, off-palette, orphans, jaggies, double outlines, sawtooth hems | lint hard gates at 0 (`tools/pixel/lint.py`); 1-2-3 step curves; selective outline closed | hand-pixelled feel: every cluster intentional, readable at 1x on all terrains |
| 7 | **design_fidelity** | wrong hand, extra sword or sheath, missing bow / collar / corset band / kagi | all bible §2 KEEP items readable; blade ≥ 2 px, hook ≥ 3 px; asymmetry correct | every KEEP item reads at 1x in every direction and frame |

**Pass bar:** every judge's overall ≥ 8 AND no criterion below 7, for that judge. Gemini scores never count toward the pass.

**Judge output format:** scores per criterion, overall, and the top 5 defects. Each defect names the file, frame and area, plus a concrete pixel-level fix.

---

## 7. Self-assessment of the lock (honest)

- **Illustration lock:** Argon gave the final `turn8_iso.png` 7/7/6/7 (style, consistency, fidelity, readability) with 7/8 handedness correct, in `wip/critique_turn8_final.txt`. Its remaining defects:
  - the E blade looks disconnected from the hidden hand
  - the SW skirt-wrap side
  - the accessories that are dropped at sprite scale
  - the flatter camera
  - **Good:** style is close to iso_v5; proportions and costume are consistent across the 8 cells; the katana is in the left hand in all 8 after the hand fixes.
  - **Weak:**
    - the camera is flatter than iso_v5
    - the collar reads wrapped
    - the NE left blade has no visible hilt
    - E shows only the blade
  - **Usable as an identity/design ref:** yes. As a pose ref: no.
- **Pixel lock:**
  - **Good:**
    - heads consistent across directions at iso_v5 scale
    - eyes and face read at 1x
    - dark hair with an upper-left sheen
    - big bow ID
    - katana stamps meet the 2 px blade / ≥ 3 px hook rules
  - **Weak (polish targets):**
    - back-view hair strands still a little stiff
    - the bow-growth rows make the S/SE/E loops boxy (round off the corners)
    - the diagonal katana hook is small and reads as a cross at 1x
  - Argon's harsh pass (3.5/10, `wip/critique_pixel_lock.txt`) drove these fixes: banding removed, eyes made calmer, the mouth/blush "moustache" split, rim removed, the N bow raised. Its "rapier" and "missing ribbons" claims are wrong: refs/1 has the cross-bar plus crescent, and the ribbons belong to the body, not the head stamp.
