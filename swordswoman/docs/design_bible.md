# DESIGN BIBLE — "Crimson Ronin" (working name: **Akane**)

Owner: Art Director. Status: **v2** (canonical for 3D modeling + sprite pipeline). v1 archived as `docs/design_bible_v1.md` / `docs/palette_v1.json`. Changes are listed in §7 Review log.
Sources: `refs/1.png` (MAIN, canonical costume), `refs/2.png` (action/attitude), `refs/3.png` (jump/flow).
Supporting files: `docs/palette.json` (v2), `docs/palette_swatch.png` (regen: `.venv/bin/python tools/make_swatch.py`), `docs/anim_spec.json` (frame counts, timing, cancel windows, jump z-offsets, hurtbox), `docs/gemini_breakdown.txt` (Gemini second opinion), `docs/gemini_concept_critique.txt`.

---

## 0. Canonical files

| Purpose | File | Notes |
|---|---|---|
| Costume truth (all details, colors, sword) | `refs/1.png` | Wins on any conflict. |
| **Chibi proportions + front/side/back** | **`concept/chibi_turnaround_v6_annotated.png`** | CANONICAL for proportions/massing only. **Open the annotated version, not the raw `chibi_turnaround_v6.png`**: handedness is mirrored, and the wrong items are marked on the sheet. |
| **Chibi isometric 3/4 (SE-facing)** | **`concept/chibi_iso_v5_annotated.png`** | CANONICAL for camera angle and massing only. The collar, sword hand, guard, ornament side, corset and legs are wrong and marked on the sheet. |
| Sword-guard detail at chibi scale | `concept/chibi_turnaround_v5.png` | Use only for the katana's hook guard; body there is too kimono-like. |
| Same design as v6, alt sword | `concept/chibi_turnaround_v3.png` | Backup; its "kama" hook weapon is WRONG. |
| Rejected | `chibi_turnaround_v1/v4`, `chibi_iso_v1/v2/v4` | v1/v4 not chibi enough; v4 iso returned the original art unchanged. |

**Known concept deviations to correct in 3D (do NOT copy from concepts; each is marked in cyan on the `_annotated` sheets):**
1. **Katana guard**: the concepts make it plain or a giant sickle. Build it as in ref 1: a straight silver cross-bar guard (tsuba bar) with **a crescent hook (kagi) prong on one side curving back toward the blade**. Blade is a normal silver katana.
2. **Corset/harness**: the concepts reduce it to a 3-buckle cincher. Build the ref-1 version: an underbust leather harness with 3 stacked straps + buckles, a central vertical plate, a round **hip pouch on the front of her right hip**, and two hanging strap tabs (tassets) over the skirt front. (The sprite will simplify it again; the model must not.)
3. **Choker**: appears in ref 2 only. Keep it as a thin dark band *inside* the collar on the model; it is not required to read on sprites.
4. **Collar** in `chibi_iso_v5` reads like a wrapped scarf. It must be a **stiff, tall, flared funnel collar, open at the front** (ref 1 / turnaround v6).
5. **Handedness / asymmetry** (concepts are mirrored; follow ref 1):
   - Katana carried in her **LEFT hand** at idle (blade down and back). Attacks use a two-handed grip (ref 2), left hand at the pommel end is fine.
   - Red flower ornament + purple lacing + dangling purple ribbon on her **RIGHT upper arm**.
   - Thigh strap + small pouch on her **LEFT thigh**; skirt front slit is on her **LEFT** side (where the black shorts show).
   - Asymmetric: **render all 8 directions from 3D — never mirror W-side sprites from E-side.**
   - Concept check (v2): `chibi_turnaround_v6` front + back and `chibi_iso_v5` all have the katana in her RIGHT hand and the ornament on her LEFT arm, so both are mirrored. The v6 side view shows a **sheathed** sword at the hip, which contradicts its own front view. There is no sheath: the sword is always drawn.
6. **Iso v5 extras**: the guard is plain (needs the kagi), the legs are cylindrical (taper them: thigh 0.30 H to ankle 0.13 H), the face strands are short (they reach the jaw, as in v6), and the round right-hip pouch is missing (v6 has it).
7. **Bow width**: the concepts draw it at about 1 H. **The 3D model caps it at 0.85 H** (§3).

---

## 1. Character summary & personality (acting notes)

A young swordswoman — cool, composed, a little aloof, with hidden warmth. Elegant rather than brutish; every motion should feel like a dance with fabric following through.

- **Default expression**: calm, half-lidded eyes, small closed mouth, faint blush (ref 1). Focused frown/brow-down in combat (ref 2). Small smile allowed in victory/jump (ref 3).
- **Idle**: weight on one hip, sword hanging loosely in left hand, tip near the ground; scarf ribbons drift; slight breathing bob (1px).
- **Walk**: light, poised, small steps (heels!) — hips sway, sleeves swing behind.
- **Run**: low and forward-leaning, sword held back and trailing (ref 3 diagonal), scarf and skirt tails streaming straight back.
- **Attack**: two-handed, low wide stance (ref 2), sharp snap then a held follow-through; sleeves and skirt overshoot and settle 2–3 frames later.
- **Jump**: arched back, chin up, legs together and bent back, skirt and sleeves flare up like petals (ref 3). Optional petal VFX in pink/coral (pink[0], pink[1], red[3]), never pure red, so her effects read apart from enemy danger telegraphs.
- **Hurt/Death**: keep it graceful — a recoil with ribbons whipping forward.
- Secondary motion is her signature: **scarf tails, sleeve cuffs, skirt tails, bow loops** always lag 1–3 frames behind the body.

---

## 2. Costume breakdown (part by part)

Legend: **[KEEP]** must read at sprite scale · **[SIMPLIFY]** reduce to 1–3 px shape/color · **[DROP]** model only, not on sprites.

### Head
- **Hair** — very dark warm brown. Front: heavy straight bangs swept slightly to her right, covering the brows; two thin face-framing strands that **reach the jaw** (not shorter). Side: hair pulled up tight, ear visible. Back: smooth nape, all hair gathered up. **[KEEP]** bangs mass + jaw strands as 1px.
- **Bun** — HIGH, slightly messy loop bun at the top-back of the skull (crown, tilted back). A few flyaway strands. **[KEEP]** — key silhouette, must read from every direction.
- **Bow** — BIG red ribbon bow tied at the base of the bun, sitting on her right side of the bun, two upright stiff loops (bunny-ear like) + two short tails. Front view: loops peek above/beside the head. **[KEEP + EXAGGERATE]** — the #1 silhouette ID. Bow width 0.8–0.85 H, **hard cap 0.85 H** (concepts are ~1 H; don't copy).
- **Face** — big blue eyes, dark upper lash line, small nose (dot or omit), small mouth, pink blush under the eyes. **[KEEP]** eyes (2 blue tones + 1 glint), **[SIMPLIFY]** blush to 1–2 px, **[DROP]** nose on sprites.
- **Earrings** — none.

### Neck & shoulders
- **High collar** — red, very tall (reaches the jaw/ears), stiff, flared outward like a funnel, open at the front in a V; lighter red inner face. Back: wraps fully, hides the nape. **[KEEP]** — frames the face; 2–3 px band of red around the jaw.
- **Choker** — thin dark band inside the collar (ref 2). **[DROP]** on sprites.
- **Chest cord & gem** — braided dark cord running from the collar down across the chest; small purple gem at the collar base. **[DROP] on sprites, no exceptions** (v2). That pixel budget goes to the eyes and the hook guard. Model only.
- **Chest flower** — large red 5-petal flower on the chest/right shoulder area (ref 1). **[SIMPLIFY]** merge with arm flower as one red highlight cluster.
- **Bare shoulders** — skin visible between collar and the detached sleeves. **[KEEP]** — 1–2 px skin at the shoulder gives the costume its read.

### Top & sleeves
- **Top** — fitted red bodice under the collar, sleeveless/off-shoulder.
- **Detached sleeves** — start at the upper arm (with a dark band at the top edge), long, and flare very wide at the wrist like bell/kimono sleeves; hem reaches mid-thigh when the arm hangs. Lighter interior, violet shadowed underside. **[KEEP + EXAGGERATE]** wide cuffs.
- **Arm ornament (her RIGHT upper arm)** — red flower cluster with purple criss-cross lacing and a long dangling purple ribbon. **[SIMPLIFY]** to 1–2 purple pixels + a dangling 1px purple ribbon line where visible.

### Torso gear
- **Corset/harness** — dark brown leather, underbust to hip: three horizontal straps with steel buckles, central vertical plate, rivets, strap tabs hanging over the skirt front. **[KEEP]** as a solid dark-brown band (the waist value break); **[SIMPLIFY]** buckles to 1–2 steel[1] pixels; corset **top edge gets a 1 px leather[2] highlight line** so it separates from the red bodice; **[DROP]** rivets, stitching, cutouts.
- **Hip pouch** — round/box pouch on the front of her right hip. **[SIMPLIFY]** 2–3 px bump on the belt.

### Lower body
- **Skirt** — asymmetric red wrap skirt. Front panel: knee-length with a slit on her LEFT exposing shorts and thigh. Sides/back: long layered pointed tails to mid-calf, separating into 3–4 petal-like points; underside crimson→violet. **[KEEP + EXAGGERATE]** back tails and flare; read as "red petal skirt".
- **Shorts** — black, short, visible through the slit. **[SIMPLIFY]** 1–3 px dark.
- **Thigh strap (her LEFT thigh)** — brown leather band with a small pouch on the outer side. **[KEEP]** as one 1px brown line + 1–2 px pouch in directions where the left leg faces camera.
- **Legs** — bare.
- **Footwear** — black high-heeled sandals with criss-cross ankle straps (ref 1 canonical; refs 2/3 show flat strapped shoes — ignore). **[SIMPLIFY]** each foot: **2 px dark** (dark[0] sole/heel + dark[1] upper), with a **1 px skin ankle** above the strap so steps read in walk/run. Heel = 1 px point under the back of the foot.

### Hands
- **Fingerless gloves** — dark, both hands. **[SIMPLIFY]** dark hand blob with 1 skin pixel at the fingers.

### Floating
- **Scarf ribbons** — two long translucent pink ribbons emerging from the back of the collar. Lighter and pinker than the dress (pink[1] base, pink[0] shadow, skin[2] lit edge, never red[3]). **[KEEP]** as 1–3 px wide ribbons; they are the motion indicator.
  - They always **trail against velocity** (and against the swing in attacks), never toward a fixed world direction.
  - In idle they are **≤ 1 H long and hang mostly downward**, with a slight drift. They can reach up to 2 H in run and dash.
  - The same rule applies to the skirt tails and sleeve cuffs.

### Katana (prop)
- **Tsuka (handle)** — black wrap with red diamond windows (4–5 diamonds), silver kashira cap. **[SIMPLIFY]** dark handle with 1–2 red pixels.
- **Guard** — silver straight cross-bar with a **crescent hook (kagi) prong** curving toward the blade on one side. **[KEEP]**: the hook is **≥ 3 px** on every sprite and is checked by hand at clean-up. This is the sword's identity.
- **Blade** — silver, gently curved, single edge. **[KEEP]** at **≥ 2 px wide on every sprite**: steel[0] spine plus steel[2] edge (steel[1] fill when 3 px). In idle the blade angles **outward, away from the silhouette** (about 25–35° off the leg line). It is never hidden behind the legs or skirt, and in N/NE/NW it must still stick out past the silhouette.
- **Sheath** — none shown in refs; the sword is always drawn. No sheath in the model.

### Facing tells (8 directions)
What tells the player which way she faces. Each direction must show its tells at 56 px.

| Dir | Primary tells | Secondary |
|---|---|---|
| **S** | face (eyes + blush), collar V open toward camera | both bell cuffs symmetric, short front skirt with slit on screen-right (her left) |
| **SE / SW** | face 3/4, collar V turned toward the facing side | the near sleeve cuff is bigger. SE: katana is in her left hand, which is on the far (upper-right) side, so check that the blade sticks out past the skirt. SW: katana on the near (lower-right) side |
| **E / W** | profile (nose-less face edge, 1 eye), high-low skirt (short front, long back) | bun clearly behind the crown, collar profile sloping back. Ribbons trail behind against velocity |
| **NE / NW** | bun + bow fill the head (no face), bare back strip (skin between collar and corset) | skirt tails fan toward camera. A 1–2 px cheek/bang edge on the facing side separates NE from N |
| **N** | bun + bow centered over the head, bare back strip, full long skirt tails | both ribbons visible and trailing |

Check: the bun sits **0.25 H back**. In NE/NW the bun must sit left/right of center **toward the camera-far side**, so NE does not read as E. Verify on the first 3D render. If it does read as E, reduce the bun set-back to 0.2 H for sprites.

### Front / side / back silhouette checklist
- **Front**: bow loops + bun above head · collar V framing face · bare shoulders · bell cuffs at hips · dark waist band · short front skirt with slit · tails flaring behind both legs.
- **Side**: bun clearly behind crown, bow loop up · tall collar profile · sleeve cuff hanging · skirt high-low (short front, long back) · heel point.
- **Back**: bun + bow dominate the head · collar wraps nape · bare shoulder blades · corset band · full long skirt tails · ribbons trailing.

---

## 3. CHIBI proportion spec

Unit **H = head height** (chin to crown, *excluding* bun and bow). Total standing height = **2.75 H** (feet to crown); with bun + bow the silhouette is **≈ 3.3 H** tall.

| Part | Spec | Notes |
|---|---|---|
| Head height | 1.0 H | Large and round. Skull is close to a sphere; chin soft, slightly pointed. |
| Head width | 1.05 H (front) | Slightly wider than tall incl. hair volume. ≈ shoulder width × 1.3. |
| Bun | 0.45 H diameter, top at +0.35 H above crown, set back 0.25 H | Must break the head silhouette from every view. |
| Bow | **≤ 0.85 H wide (hard cap)**, loops 0.4 H tall | Exaggerated vs ref (~1.5×). Concepts are about 1 H; don't go wider in 3D. |
| Eyes | 0.28 H tall, 0.22 H wide each, centers at 0.42 H above chin, spacing ≈ 1 eye-width | Eye line slightly below head midpoint (cute). Iris fills 70% of eye. |
| Mouth | 0.05 H, at 0.18 H above chin | |
| Neck | ~0 (hidden by collar) | Collar height 0.3 H, flares to 0.9 H wide. |
| Torso (collar base → crotch) | 0.85 H | Short; corset band occupies the lower 0.35 H. |
| Shoulder width | 0.8 H | Narrow, rounded. |
| Arms | shoulder → wrist 0.75 H | Hands reach just below crotch. |
| Sleeve cuff flare | 0.55 H wide at wrist, hem length to 0.15 H below the hand | Exaggerated bell. |
| Legs (crotch → sole) | 0.9 H | Short, soft, **tapered**: thigh 0.30 H → knee 0.20 H → ankle 0.13 H wide. Not cylindrical (iso v5 is wrong). |
| Hands | 0.22 H | Small mitten-like; fingers suggested only. |
| Feet | 0.3 H long incl. heel, 0.15 H heel height | Small; heels shortened from ref to keep stability. |
| Skirt | front hem at lower thigh (0.6 H above sole, 0.3 H below crotch), back tails to 0.2 H above sole; flare radius 0.65 H at hem | Petal tails: 4 points. |
| Scarf ribbons | 0.12 H wide, 1.2–2.0 H long | Animated / physics. |
| **Katana** | **total 2.0 H** (blade 1.45 H, handle 0.45 H, guard bar 0.22 H, hook 0.15 H) | ≈ 0.73 × body height — shortened from ref (~1.1× body) but still long and iconic. Hero model blade width 0.06 H. |
| Katana, sprite-render variant | blade width **0.12 H** (= 2 px), hook **0.18 H** (= 3 px), guard bar 0.25 H | A separate shape key / object switched on only for sprite renders, so that downsampling keeps the 2 px blade and 3 px hook. |
| Hurtbox (gameplay) | capsule **0.8 H wide** (~14 px), torso + legs only | Sleeves, skirt flare, bow and ribbons are **not** hurtbox. The visual silhouette is 1.3–1.5× wider than the body; players must not feel hit through the costume. |

**Why this is "well rounded":** 2.75 H gives a head big enough for 3px-tall eyes at sprite size while leaving enough leg for readable walk/run cycles (2.0–2.5 H chibis lose leg action; 3+ H loses cuteness). All forms are built from soft ovals — round head, round bun, soft bell sleeves, petal skirt — with only three sharp accents (collar points, skirt tail points, sword). Mass is pyramid-shaped (big head on top, wide flared skirt/sleeves at the bottom) which reads stable and cute in iso, and the dark corset band cleanly splits the red mass into upper/lower halves.

---

## 4. Pixel palette v2 (22 unique colors) — `docs/palette.json`

All ramps go dark to light. Swatch with luminance values and a dark-terrain test strip: `docs/palette_swatch.png`.
**Value rule:** colors that touch each other on the sprite or touch the silhouette edge must differ by **≥ 1.8× in relative luminance**, or by a strong hue jump (red vs brown vs violet-grey).

| Ramp | Hex (dark → light) | Rel. luminance | Role |
|---|---|---|---|
| **outline** | `#1a1220` | 0.008 | Deep plum-black. Exterior outline (selective), pupils, lash line. Same as dark[0] and leather[0]. |
| **skin** (3) | `#c48089` · `#f0b49c` · `#fde3d2` | 0.290 · 0.536 · 0.805 | Shadow (cooled toward mauve in v2 so it doesn't merge with collar red; also the mouth) · base · highlight (lit cheek, thigh, shoulder; **also the scarf lit edge**). |
| **hair** (3) | `#42282a` · `#74483a` · `#b07a62` | 0.028 · 0.087 · 0.240 | Shadow/inner outline · base (lifted and warmed in v2) · sheen band on top of the head **and on the bun** (v2: required). |
| **red cloth** (4) | `#4a1640` · `#92203f` · `#d8343e` · `#f5705a` | 0.024 · 0.075 · 0.174 · 0.317 | **Violet** deep shadow (occluded undersides only) · crimson shadow · base red (dress, collar, sleeves, bow) · **warm coral** highlight. |
| **leather** (3) | `#1a1220` · `#4a2e20` · `#a8744a` | 0.008 · 0.035 · 0.213 | Corset recess (= outline) · corset base / thigh strap (v2: darker, 2.1× below red[1], 2.5× below hair base) · **corset top-edge line** + pouch flap highlight. |
| **dark** (2) | `#1a1220` · `#504462` | 0.008 · 0.067 | Soles, heels, pupils, glove/shorts shadow · **base** of shorts/gloves/shoe uppers (v2: lifted, violet-grey so they don't merge with leather or the floor). |
| **steel** (3) | `#5f6678` · `#a8b0c0` · `#eef0f5` | 0.133 · 0.432 · 0.871 | Blade spine & guard shadow, buckles · blade body & guard · edge glint (also eye glint, specular, **hurt flash**, smear core). |
| **eye** (2) | `#2c3f9e` · `#5f8ee8` | 0.066 · 0.276 | Iris top/shadow · iris lower/lit. |
| **pink** (2) | `#f49ab0` · `#f8b5c8` | 0.455 · 0.572 | pink[0]: scarf shadow, blush, **camera-locked rim light**, occluded-silhouette pass, petal VFX · pink[1]: **scarf base** (v2: lighter so it pops against red[3]). |
| **purple** (1) | `#9b45c9` | 0.154 | Arm-lace ribbon only, **≤ 3 px per frame**. (Chest gem dropped on sprites.) |

Usage rules:
- No colors outside the palette. No anti-aliasing to white/transparent (hard alpha). The tsuka diamonds use red[2].
- **Scarf:** pink[1] base, pink[0] shadow, skin[2] lit edge. Red[3] is **never** used on the scarf (v2).
- **Corset:** leather[1] mass, leather[2] 1 px top edge, steel[1] buckles, outline recesses. Never touch hair[1] directly; there is always a leather[2] or red pixel between them.
- **Red vs danger language:** she is about 70 % red, so red is **her identity color, not a game signal**.
  - Enemy and boss telegraphs use **orange/yellow** (`#ffb52e` / `#ffe066`). Never red `#d8343e`, and never purple (her accent color).
  - Her own VFX (petals, smears) lean **pink/coral**: pink[0], pink[1], red[3].
  - Damage/hurt feedback is **white** (steel[2]), never red.

---

## 5. Sprite rendering conventions

### Lighting
- Single key light from **top-left** (screen space), fixed to the camera, not the world, so shading reads the same in all 8 directions.
- **Rim light (required, v2):** camera-locked from the **back-right**, color **pink[0] `#f49ab0`**, 1 px.
  - Applies on the hair (including the bun), the bow loops, and the sleeve-cuff edges, on the silhouette side away from the key.
  - In Blender: a second sun lamp parented to the camera, plus a toon/rim pass that is quantized to pink[0] only where that pass is above threshold.
  - This is what keeps the dark hair from merging with dark floors.
- **3-tone cel shading** per material: shadow / base / highlight. Red cloth uses its 4th (violet) tone only on occluded undersides (inside the skirt, under the sleeves, under the bow loops).
- No gradients, no dithering on the character (dither allowed only on VFX).

### Outline
- **Selective, colored outlines.** The exterior silhouette uses `#1a1220` on the shadow side (bottom/right) and the material's darkest ramp color on the lit side (top/left). Examples: red cloth lit edge `#92203f`, skin lit edge `#c48089`, hair lit edge `#42282a`.
- The exterior silhouette is always **closed**: no gaps where she touches the ground plane.
- Interior lines only where two similar values meet (sleeve vs. skirt, arm vs. body). Use the darker ramp color there, never the pure outline.
- 1px lines only, no doubles, no orphan pixels; clean pixel-perfect curves (no jaggies — 1-2-3 step patterns).
- Eyes: outline-colored upper lash 1px, iris 2 blue tones, 1 steel[2] glint.
- **Engine-side silhouette pass (optional, v2):** when she is occluded by props or walls, the engine draws her silhouette (or a 1 px outline of it) in pink[0] `#f49ab0` at 60–80 % alpha over the occluder. The sprite sheet does not bake this in; the engine builds it from sprite alpha. Use the same pass optionally as a 1 px light outline on very dark floors.

### Isometric camera (Blender)
- **Orthographic** camera; elevation **30°** above the ground plane (camera rotation X = 60°), azimuth fixed at 45° to the world grid. 30° gives a better face read on a chibi.
- **Ground contact uses 2:1 math (26.57°), not 30°.** The ground-shadow ellipse and the footprint are drawn at exactly 2:1 (e.g. shadow 20 × 10 px), so the feet sit correctly on 2:1 tiles. The 30° camera applies to the body only.
- Character rotates, camera stays. **8 directions**, named by facing on screen: **S** (toward viewer/bottom), **SE**, **E** (screen-right), **NE**, **N** (away), **NW**, **W**, **SW**. Character yaw steps of 45°, S = facing the camera.
- Render each direction from 3D (asymmetric costume → **no mirroring**).
- Render at 8–10× target resolution, with the **sprite-render katana variant** (§3) switched on.
- **Quantize per material, never by global nearest color.** Render a material-ID pass. Each pixel snaps only to its own ramp (hair → hair ramp, shorts → dark ramp, and so on). In the v2 test, global nearest-color turned the hair into dark[1] violet-grey (see `docs/palette_v1_vs_v2_terrain.png`).
- Then downsample with nearest/area, palette-quantize to `docs/palette.json`, and do a hand clean-up pass: outlines, eyes, the 2 px blade, the 3 px hook, and the 2 px feet + skin ankle.
- **Ground shadow is a separate layer, always on the ground.** It is never moved by jump, knockback or any vertical motion; only its scale changes (see the jump spec). The engine may draw it instead (`#1a1220` at 35 % alpha, 2:1 ellipse). In top-down iso the shadow is the only cue for height and landing position.

### Target sprite size & cells
- **Character height ≈ 56 px** standing (sole to top of bow; crown ≈ 47 px; head H ≈ 17 px; the head reads ≈ 18–20 px wide in iso).
- **Cell 128 × 128 px, feet pivot at (64, 104)** for every animation (v2; was 96 × 96). The cell leaves 48 px above the bow for overhead swings, 64 px each side for katana (34 px) + arm + lunge, and 24 px below the feet for S-facing lunges and tails.
- **Pivot rule:** the same world point (root between the feet) lands on the pivot in every frame and every direction. Lunges, dashes and knockback move the **engine** position, not the sprite.
- **Delivery:** author and review in uniform 128 cells. The export packs a **trimmed atlas with per-frame pivot offsets** (relative to (64, 104)), so the cell size costs no texture memory.
- Justification for 56 px:
  - At H ≈ 17 px the eyes are 4–5 px tall × 3–4 px wide, enough for lash + 2 iris tones + glint.
  - The bow/bun get 8–10 px, the hook 3 px, the blade 2 px, the corset band 5–6 px.
  - ≤ 40 px loses the face and the hook. ≥ 80 px multiplies animation cost and clashes with 32×16 / 64×32 tiles.

### Gameplay animation spec (machine-readable copy: `docs/anim_spec.json`)
Every animation is authored in all 8 directions. "Loop" = cycles. Timing columns are frame counts (ms per frame in the JSON).

| Anim | Frames | Loop | Anticipation | Active | Recovery | Notes / cancel windows |
|---|---|---|---|---|---|---|
| idle | 6 | yes | – | – | – | 1 px breathing bob. Sword low and angled out. Ribbons ≤ 1 H, hanging down. |
| combat-idle | 4 | yes | – | – | – | Two-handed guard (ref 2), knees bent. Blade forward, clear of the silhouette. |
| walk | 8 | yes | – | – | – | Contacts on f0/f4. 2 px dark foot + 1 px skin ankle must read on each step. |
| run | 8 | yes | – | – | – | Forward lean, sword trailing. Ribbons/tails stream against velocity, up to 2 H. |
| dash | 4 | no | 1 (wind-up) | 2 (travel, with after-image) | 1 (brake) | Engine moves the root and owns the i-frames. After-image = pink[0] silhouette at 50 % alpha, spawned by the engine from f1/f2. |
| jump | 6 | no | 1 (crouch) | rise 1 · apex 1 · fall 1 | 2 (land, recover) | **Authored in place, root locked.** Engine z-offset per frame = `[0, 10, 16, 8, 0, 0]` px. Shadow stays on the ground, scale `[1, .9, .8, .9, 1, 1]`. |
| attack 1 | 6 | no | 2 | 1 | 3 | Horizontal cut. Chain to attack 2 on recovery f1–f2. Dash-cancel from recovery f2. |
| attack 2 | 7 | no | 2 | 2 | 3 | Rising diagonal. Chain to attack 3 on recovery f1–f2. Dash-cancel from recovery f2. |
| attack 3 | 9 | no | 3 | 2 | 4 | Two-handed low lunge finisher (ref 2). No chain. Dash-cancel from recovery f3. |
| hurt | 3 | no | – | – | – | f0 = **solid white silhouette (steel[2])**, never red. f1 recoil with ribbons whipping forward, f2 recover. Interrupts anything except death. |
| death | 6 | no | – | – | – | Graceful fold to the ground. Hold the last frame. |
| *air attack (opt.)* | 5 | no | 1 | 2 | 2 | Uses the jump z-offset from the frame of input. |
| *landing slash (opt.)* | 6 | no | 1 | 2 | 3 | Triggered on landing from an air attack. |

- **Smear / slash-arc VFX (required):** every attack shows the arc on its active frame(s): 1 frame for attack 1, 2 frames for attacks 2 and 3. The arc is **3–5 px thick**, with a steel[2] core and a pink[1] → pink[0] outer edge. **The arc is what tells the player the hitbox, not the blade.** It is drawn on the sprite layer, inside the 128 cell.
- Input buffer: the last 2 frames of the active phase. Hurt cancels everything. Nothing cancels hurt or death.
- Secondary motion (ribbons, sleeves, skirt tails, bow) lags 1–3 frames behind the body and **trails against velocity** in every anim. In W/NW they trail toward screen-right/up, never in a fixed world direction.

---

## 6. Judge checklist (pass/fail per sprite sheet)
1. Silhouette alone identifies her: bun + big bow, tall collar, bell sleeves, petal skirt, katana with hook.
2. Palette: only `docs/palette.json` colors, ramps used in order, red hue-shifts to violet in shadows.
3. Lighting from top-left in all 8 directions; 3-tone cel; selective colored outline.
4. Chibi proportions per §3 (≈ 2.75 H body, sword ≈ 2 H, bow ≤ 0.85 H).
5. Asymmetry correct per §0.5 in all directions.
6. Secondary motion (scarf, sleeves, skirt, bow) lags and settles.
7. Feet pivot stable at (64, 104) in a 128 cell; no jitter, no orphan pixels, no AA halos. Jump frames root-locked; shadow on the ground.
8. Blade ≥ 2 px and hook ≥ 3 px in every frame and direction; the blade sticks out past the silhouette in idle (including N/NE/NW); every attack has a smear arc.
9. Readability: composite on dungeon, dirt and grass test tiles at 1×. Hair, corset, shorts and shoes stay separable; the pink rim is visible on the hair/bow; facing is readable per the §2 facing-tell table.
10. Danger language: no red telegraph-like VFX on her; hurt flash is white.

---

## 7. Review log

### v2: response to Game Director review + Gemini critique (gemini-3.1-pro-preview)

**Adopted**
- **GD-1a, darks:** hair lifted and warmed: `#33201c/#57372e/#80574a` → `#42282a/#74483a/#b07a62`. Hair base luminance goes from 0.050 to 0.087. A sheen band on the bun is now required.
- **GD-1c, rim light:** camera-locked back-right rim in pink[0] `#f49ab0` on the hair, bun, bow and sleeve cuffs (§5 Lighting).
- **GD-1d, silhouette pass:** engine-side pink[0] silhouette / 1 px outline when she is occluded, and optionally on very dark floors (§5 Outline).
- **GD-1, other darks:** dark[1] lifted `#3a3046` → `#504462` (0.035 → 0.067). Shorts, gloves and shoe uppers now use dark[1] as base and outline as shadow, so they separate from the leather and the floor.
- **GD-2, sword:** blade ≥ 2 px (steel[0] spine + steel[2] edge) and hook ≥ 3 px, kept by hand. A sprite-render katana variant (blade 0.12 H, hook 0.18 H) makes the downsample produce this automatically. Idle blade angles out of the silhouette in all 8 directions. Smear arcs are mandatory (3–5 px, steel[2] + pink).
- **GD-3, cell:** 128 × 128, pivot (64, 104) for **all** animations (not only attack/dash/jump), so one pivot rule holds everywhere. Exported as a trimmed atlas with per-frame offsets, so we get both of GD's options.
- **GD-4, anim spec:** table in §5 plus `docs/anim_spec.json` with frames, loop, timing phases, chain and dash-cancel windows. Combo is 2/1/3, 2/2/3, 3/2/4. Optional air attack and landing slash added.
- **GD-5, jump:** authored in place with the root locked. The z-offset is exported as data. The shadow stays on the ground and only scales.
- **GD-6, facing tells:** table added in §2. The ribbons/tails rule is now "against velocity" everywhere (the v1 "streaming straight back" wording was ambiguous). Idle ribbons ≤ 1 H, hanging down. NE-vs-E bun check added.
- **GD-7, danger language:** enemy telegraphs are orange/yellow; her VFX are pink/coral; hurt flash is white (steel[2]).
- **GD-8, hurtbox/bow:** hurtbox is a 0.8 H capsule on the torso and legs. Bow is hard-capped at 0.85 H.
- **GD-9, handedness:** marked directly on the sheets: `concept/chibi_turnaround_v6_annotated.png` and `concept/chibi_iso_v5_annotated.png` (cyan = wrong, green = correct target). §0 now points modelers to the annotated files. The sheets are generated by `tools/annotate_concepts.py`.
- **GD-10:** ground shadow and footprint use 2:1 math (shadow 20 × 10). Feet are 2 px dark + 1 px skin ankle. Chest cord and gem are dropped entirely on sprites.
- **Gemini 5, leather:** leather[1] `#5e3a28` → **`#4a2e20`** exactly as proposed.
- **Gemini 6, scarf:** scarf base `#f49ab0` → **`#f8b5c8`** (0.572 vs red[3] 0.317). The old pink stays as scarf shadow and rim color.
- **Gemini, skin shadow:** cooled toward mauve, `#c9776f` → `#c48089`.
- **Gemini fidelity points 1–4 and 6, plus the collar and leg taper:** all listed in §0 and marked on the sheets. The corset must have 3 straps, a plate and tabs; face strands reach the jaw.
- **Verification:** `docs/palette_v1_vs_v2_terrain.png` shows iso v5 at 56 px, quantized with v1 (top) and v2 (bottom), on dungeon, dirt and grass.
  - The v2 hair separates from the dungeon floor and from the corset.
  - The corset now reads as a distinct dark band.
  - The test also shows two things this palette alone cannot fix: hair base vs mid-brown dirt, and the 1 px blade. Both are covered by rules (pink rim + closed outline; blade ≥ 2 px via the sprite katana variant).
- **Producer note:** the scarf's lit edge no longer uses red[3]. It now uses skin[2] `#fde3d2` (shared, so no new color). v6's sheathed side view is flagged as self-inconsistent.

**Rejected / modified (with reasons)**
- **GD-1b, corset `#6e4630`: rejected; the corset was moved darker instead.** Measured luminance of `#6e4630` is **0.079**, which is *the same* as red shadow `#92203f` (0.075), so it would remove the separation GD asked for. It would also collide with the new lifted hair base (0.087). Gemini asked for the opposite direction (`#4a2e20`, 0.035), and that is what we used. Corset vs red[1] is now 2.1× apart and corset vs hair base 2.5×. GD's *intent* (corset clearly reads against the red) is met by the value gap plus GD's own leather[2] top-edge line, which we adopted (leather[2] brightened to `#a8744a`). The corset is interior to the silhouette (red all around it), so being dark does not cause ground merging.
- **GD-7, purple for telegraphs: rejected.** Purple `#9b45c9` is her accent color and red[0] is violet, so purple telegraphs would read as "hers". Telegraphs use orange/yellow only.
- **GD-3, 128 only for attack/dash/jump: modified to all animations.** Mixed cell sizes break the "same pivot every frame" rule across animation transitions. Trimmed-atlas export removes the memory cost.
- **GD-9, "corrected paintover": not done; overlay notes only.** AI regeneration has failed the handedness/kagi fix in 5+ attempts and risks new errors. Ground truth is the text spec + `refs/1.png`, and the 3D model is where this gets fixed. The annotated sheets make the mirrored items impossible to miss.
- **Gemini, "turnaround v6 is missing the right-hip pouch / strands too short": rejected for v6, accepted for iso v5.** v6 has the pouch and roughly jaw-length strands; only iso v5 lacks them.
- **leather[0] is no longer shared with hair[0].** It is now the outline color, so the palette grows from 21 to 22 colors. Corset recesses at 56 px are 1 px, and the outline color reads cleaner there than a near-black brown.
