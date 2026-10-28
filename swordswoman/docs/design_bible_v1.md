# DESIGN BIBLE — "Crimson Ronin" (working name: **Akane**)

Owner: Art Director. Status: v1 (canonical for 3D modeling + sprite pipeline).
Sources: `refs/1.png` (MAIN, canonical costume), `refs/2.png` (action/attitude), `refs/3.png` (jump/flow).
Supporting files: `docs/palette.json`, `docs/palette_swatch.png`, `docs/gemini_breakdown.txt` (Gemini second opinion), `docs/gemini_concept_critique.txt`.

---

## 0. Canonical files

| Purpose | File | Notes |
|---|---|---|
| Costume truth (all details, colors, sword) | `refs/1.png` | Wins on any conflict. |
| **Chibi proportions + front/side/back** | **`concept/chibi_turnaround_v6.png`** | CANONICAL chibi sheet. Front / side / back. |
| **Chibi isometric 3/4 (SE-facing, 30° down)** | **`concept/chibi_iso_v5.png`** | CANONICAL iso read + 3/4 view (stands in for the missing 3/4 panel). |
| Sword-guard detail at chibi scale | `concept/chibi_turnaround_v5.png` | Use only for the katana's hook guard; body there is too kimono-like. |
| Same design as v6, alt sword | `concept/chibi_turnaround_v3.png` | Backup; its "kama" hook weapon is WRONG. |
| Rejected | `chibi_turnaround_v1/v4`, `chibi_iso_v1/v2/v4` | v1/v4 not chibi enough; v4 iso returned the original art unchanged. |

**Known concept deviations to correct in 3D (do NOT copy from concepts):**
1. **Katana guard**: the concepts make it plain or a giant sickle. Build it as in ref 1: a straight silver cross-bar guard (tsuba bar) with **a crescent hook (kagi) prong on one side curving back toward the blade**. Blade is a normal silver katana.
2. **Corset/harness**: the concepts reduce it to a 3-buckle cincher. Build the ref-1 version: an underbust leather harness with 3 stacked straps + buckles, a central vertical plate, a round **hip pouch on the front of her right hip**, and two hanging strap tabs (tassets) over the skirt front. (The sprite will simplify it again; the model must not.)
3. **Choker**: appears in ref 2 only. Keep it as a thin dark band *inside* the collar on the model; it is not required to read on sprites.
4. **Collar** in `chibi_iso_v5` reads like a wrapped scarf. It must be a **stiff, tall, flared funnel collar, open at the front** (ref 1 / turnaround v6).
5. **Handedness / asymmetry** (concepts are mirrored; follow ref 1):
   - Katana carried in her **LEFT hand** at idle (blade down and back). Attacks use a two-handed grip (ref 2), left hand at the pommel end is fine.
   - Red flower ornament + purple lacing + dangling purple ribbon on her **RIGHT upper arm**.
   - Thigh strap + small pouch on her **LEFT thigh**; skirt front slit is on her **LEFT** side (where the black shorts show).
   - Asymmetric: **render all 8 directions from 3D — never mirror W-side sprites from E-side.**

---

## 1. Character summary & personality (acting notes)

A young swordswoman — cool, composed, a little aloof, with hidden warmth. Elegant rather than brutish; every motion should feel like a dance with fabric following through.

- **Default expression**: calm, half-lidded eyes, small closed mouth, faint blush (ref 1). Focused frown/brow-down in combat (ref 2). Small smile allowed in victory/jump (ref 3).
- **Idle**: weight on one hip, sword hanging loosely in left hand, tip near the ground; scarf ribbons drift; slight breathing bob (1px).
- **Walk**: light, poised, small steps (heels!) — hips sway, sleeves swing behind.
- **Run**: low and forward-leaning, sword held back and trailing (ref 3 diagonal), scarf and skirt tails streaming straight back.
- **Attack**: two-handed, low wide stance (ref 2), sharp snap then a held follow-through; sleeves and skirt overshoot and settle 2–3 frames later.
- **Jump**: arched back, chin up, legs together and bent back, skirt and sleeves flare up like petals (ref 3). Optional petal VFX in palette red.
- **Hurt/Death**: keep it graceful — a recoil with ribbons whipping forward.
- Secondary motion is her signature: **scarf tails, sleeve cuffs, skirt tails, bow loops** always lag 1–3 frames behind the body.

---

## 2. Costume breakdown (part by part)

Legend: **[KEEP]** must read at sprite scale · **[SIMPLIFY]** reduce to 1–3 px shape/color · **[DROP]** model only, not on sprites.

### Head
- **Hair** — very dark warm brown. Front: heavy straight bangs swept slightly to her right, covering the brows; two thin face-framing strands to the jaw. Side: hair pulled up tight, ear visible. Back: smooth nape, all hair gathered up. **[KEEP]** bangs mass + jaw strands as 1px.
- **Bun** — HIGH, slightly messy loop bun at the top-back of the skull (crown, tilted back). A few flyaway strands. **[KEEP]** — key silhouette, must read from every direction.
- **Bow** — BIG red ribbon bow tied at the base of the bun, sitting on her right side of the bun, two upright stiff loops (bunny-ear like) + two short tails. Front view: loops peek above/beside the head. **[KEEP + EXAGGERATE]** — the #1 silhouette ID. Bow width ≈ 0.8× head width in chibi.
- **Face** — big blue eyes, dark upper lash line, small nose (dot or omit), small mouth, pink blush under the eyes. **[KEEP]** eyes (2 blue tones + 1 glint), **[SIMPLIFY]** blush to 1–2 px, **[DROP]** nose on sprites.
- **Earrings** — none.

### Neck & shoulders
- **High collar** — red, very tall (reaches the jaw/ears), stiff, flared outward like a funnel, open at the front in a V; lighter red inner face. Back: wraps fully, hides the nape. **[KEEP]** — frames the face; 2–3 px band of red around the jaw.
- **Choker** — thin dark band inside the collar (ref 2). **[DROP]** on sprites.
- **Chest cord & gem** — braided dark cord running from the collar down across the chest; small purple gem at the collar base. **[DROP]** (gem may be 1px purple in front views if space).
- **Chest flower** — large red 5-petal flower on the chest/right shoulder area (ref 1). **[SIMPLIFY]** merge with arm flower as one red highlight cluster.
- **Bare shoulders** — skin visible between collar and the detached sleeves. **[KEEP]** — 1–2 px skin at the shoulder gives the costume its read.

### Top & sleeves
- **Top** — fitted red bodice under the collar, sleeveless/off-shoulder.
- **Detached sleeves** — start at the upper arm (with a dark band at the top edge), long, and flare very wide at the wrist like bell/kimono sleeves; hem reaches mid-thigh when the arm hangs. Lighter interior, violet shadowed underside. **[KEEP + EXAGGERATE]** wide cuffs.
- **Arm ornament (her RIGHT upper arm)** — red flower cluster with purple criss-cross lacing and a long dangling purple ribbon. **[SIMPLIFY]** to 1–2 purple pixels + a dangling 1px purple ribbon line where visible.

### Torso gear
- **Corset/harness** — dark brown leather, underbust to hip: three horizontal straps with steel buckles, central vertical plate, rivets, strap tabs hanging over the skirt front. **[KEEP]** as a solid dark-brown band (the waist value break); **[SIMPLIFY]** buckles to 1–2 light-leather pixels; **[DROP]** rivets, stitching, cutouts.
- **Hip pouch** — round/box pouch on the front of her right hip. **[SIMPLIFY]** 2–3 px bump on the belt.

### Lower body
- **Skirt** — asymmetric red wrap skirt. Front panel: knee-length with a slit on her LEFT exposing shorts and thigh. Sides/back: long layered pointed tails to mid-calf, separating into 3–4 petal-like points; underside crimson→violet. **[KEEP + EXAGGERATE]** back tails and flare; read as "red petal skirt".
- **Shorts** — black, short, visible through the slit. **[SIMPLIFY]** 1–3 px dark.
- **Thigh strap (her LEFT thigh)** — brown leather band with a small pouch on the outer side. **[KEEP]** as one 1px brown line + 1–2 px pouch in directions where the left leg faces camera.
- **Legs** — bare.
- **Footwear** — black high-heeled sandals with criss-cross ankle straps (ref 1 canonical; refs 2/3 show flat strapped shoes — ignore). **[SIMPLIFY]** dark feet + 1px dark ankle band; heels implied by a 1px gap/point.

### Hands
- **Fingerless gloves** — dark, both hands. **[SIMPLIFY]** dark hand blob with 1 skin pixel at the fingers.

### Floating
- **Scarf ribbons** — two long translucent pink-red ribbons emerging from the back of the collar, streaming behind/side. Lighter and pinker than the dress. **[KEEP]** as 1–3 px wide pink ribbons; they are the motion indicator. Max length on sprite ≈ 1 head in idle, up to 2 heads in run.

### Katana (prop)
- **Tsuka (handle)** — black wrap with red diamond windows (4–5 diamonds), silver kashira cap. **[SIMPLIFY]** dark handle with 1–2 red pixels.
- **Guard** — silver straight cross-bar with a **crescent hook (kagi) prong** curving toward the blade on one side. **[KEEP]** — one 2–3 px curved steel hook; this is the sword's identity.
- **Blade** — silver, gently curved, single edge; dark spine, bright edge. **[KEEP]**.
- **Sheath** — none shown in refs; the sword is always drawn. No sheath in the model.

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
| Bow | 0.85 H wide, loops 0.4 H tall | Exaggerated vs ref (~1.5×). |
| Eyes | 0.28 H tall, 0.22 H wide each, centers at 0.42 H above chin, spacing ≈ 1 eye-width | Eye line slightly below head midpoint (cute). Iris fills 70% of eye. |
| Mouth | 0.05 H, at 0.18 H above chin | |
| Neck | ~0 (hidden by collar) | Collar height 0.3 H, flares to 0.9 H wide. |
| Torso (collar base → crotch) | 0.85 H | Short; corset band occupies the lower 0.35 H. |
| Shoulder width | 0.8 H | Narrow, rounded. |
| Arms | shoulder → wrist 0.75 H | Hands reach just below crotch. |
| Sleeve cuff flare | 0.55 H wide at wrist, hem length to 0.15 H below the hand | Exaggerated bell. |
| Legs (crotch → sole) | 0.9 H | Short, soft, slightly tapered; knees barely indicated. |
| Hands | 0.22 H | Small mitten-like; fingers suggested only. |
| Feet | 0.3 H long incl. heel, 0.15 H heel height | Small; heels shortened from ref to keep stability. |
| Skirt | front hem at lower thigh (0.6 H above sole, 0.3 H below crotch), back tails to 0.2 H above sole; flare radius 0.65 H at hem | Petal tails: 4 points. |
| Scarf ribbons | 0.12 H wide, 1.2–2.0 H long | Animated / physics. |
| **Katana** | **total 2.0 H** (blade 1.45 H, handle 0.45 H, guard bar 0.22 H, hook 0.15 H) | ≈ 0.73 × body height — shortened from ref (~1.1× body) but still long and iconic. Blade width 0.06 H (wider than real for readability). |

**Why this is "well rounded":** 2.75 H gives a head big enough for 3px-tall eyes at sprite size while leaving enough leg for readable walk/run cycles (2.0–2.5 H chibis lose leg action; 3+ H loses cuteness). All forms are built from soft ovals — round head, round bun, soft bell sleeves, petal skirt — with only three sharp accents (collar points, skirt tail points, sword). Mass is pyramid-shaped (big head on top, wide flared skirt/sleeves at the bottom) which reads stable and cute in iso, and the dark corset band cleanly splits the red mass into upper/lower halves.

---

## 4. Pixel palette (21 unique colors) — `docs/palette.json`

All ramps dark → light. Swatch: `docs/palette_swatch.png`.

| Ramp | Hex (dark → light) | Role |
|---|---|---|
| **outline** | `#1a1220` | Deep plum-black. Exterior outline (selective), pupils, lash line. Same as dark[0]. |
| **skin** (3) | `#c9776f` · `#f0b49c` · `#fde3d2` | shadow (also blush 1px, mouth) · base · highlight (lit cheek, thigh, shoulder). Warm, slightly pink to sit next to red. |
| **hair** (3) | `#33201c` · `#57372e` · `#80574a` | shadow/inner outline · base · sheen band on top of head & bun. |
| **red cloth** (4) | `#4a1640` · `#92203f` · `#d8343e` · `#f5705a` | **violet** deep shadow / skirt & sleeve underside · crimson shadow · base red (dress, collar, sleeves, bow) · **warm coral** highlight. Hue shifts violet in shadow → warm in light. |
| **leather** (3) | `#33201c` · `#5e3a28` · `#8f5e3c` | corset shadow (shared with hair[0]) · corset base / thigh strap · buckle-glint & top edge. |
| **dark** (2) | `#1a1220` · `#3a3046` | shorts / gloves / shoes / tsuka shadow · their lit side. |
| **steel** (3) | `#5f6678` · `#a8b0c0` · `#eef0f5` | blade spine & guard shadow · blade body & guard · edge glint (also eye glint, specular). |
| **eye** (2) | `#2c3f9e` · `#5f8ee8` | iris top/shadow · iris lower/lit. |
| **pink** (1) | `#f49ab0` | scarf ribbons (with red[3] as their lit edge and red[2] as their shadow); blush accent. |
| **purple** (1) | `#9b45c9` | arm-lace ribbon, chest gem. Accent only — ≤ 4 px per frame. |

Rules: no colors outside the palette; no anti-aliasing to white/transparent (hard alpha). The tsuka diamonds use red[2]. Petal VFX use red[2]/red[3]/pink.

---

## 5. Sprite rendering conventions

### Lighting
- Single key light from **top-left** (screen space), consistent for all 8 directions (the light is fixed to the camera, not the world, so shading reads the same in every direction). Optional faint rim from the back-right on hair/sleeve edges using the ramp's highlight.
- **3-tone cel shading** per material: shadow / base / highlight (red cloth uses its 4th violet tone only for occluded undersides: inside the skirt, under sleeves, under the bow loops).
- No gradients, no dithering on the character (dither allowed only on VFX).

### Outline
- **Selective, colored outlines**: exterior silhouette uses `#1a1220` on the shadow side (bottom/right) and the material's darkest ramp color on the lit side (top/left), e.g. red cloth lit edge = `#92203f`, skin lit edge = `#c9776f`, hair = `#33201c`.
- Interior lines only where two similar values meet (sleeve vs. skirt, arm vs. body): use the darker ramp color, never pure outline.
- 1px lines only, no doubles, no orphan pixels; clean pixel-perfect curves (no jaggies — 1-2-3 step patterns).
- Eyes: outline-colored upper lash 1px, iris 2 blue tones, 1 steel[2] glint.

### Isometric camera (Blender)
- **Orthographic** camera; elevation **30°** above the ground plane (camera rotation X = 60°), azimuth fixed at 45° to the world grid. (Pure 2:1 tile math is 26.57°; we use 30° for a better face read on a chibi — tiles are drawn 2:1, the 3.4° difference is invisible on a character.)
- Character rotates, camera stays. **8 directions**, named by facing on screen: **S** (toward viewer/bottom), **SE**, **E** (screen-right), **NE**, **N** (away), **NW**, **W**, **SW**. Character yaw steps of 45°, S = facing the camera.
- Render each direction from 3D (asymmetric costume → **no mirroring**).
- Render at 8–10× target resolution, then downsample with nearest/area + palette-quantize to `docs/palette.json`, then hand clean-up pass (outlines, eyes, sword hook).
- Feet anchor (pivot) at the same pixel in every frame and direction; soft ground shadow is a separate layer (ellipse 20×8 px, `#1a1220` at 35% alpha, or drawn by the engine).

### Target sprite size
- **Character height ≈ 56 px** standing (sole to top of bow; crown ≈ 47 px; head H ≈ 17 px; with the iso foreshortening the head reads ≈ 18–20 px wide).
- **Cell 96 × 96 px**, feet pivot at (48, 84). Idle/walk fit in 64×64, but sword swings (katana ≈ 34 px), jump apex (+16 px) and streaming scarf/skirt tails need the larger cell; a uniform cell keeps the atlas simple.
- Justification: at H ≈ 17 px the eyes are 4–5 px tall × 3–4 px wide — enough for lash + 2 iris tones + glint, the detail that sells the face. The bow/bun get 8–10 px, the sword hook 2–3 px, the corset band 5–6 px — every [KEEP] item from §2 gets at least 2 px. Smaller (≤ 40 px) loses the face and the hook; larger (≥ 80 px) multiplies animation cost and clashes with 2:1 tiles at 32×16 / 64×32.
- Frame budget suggestion: idle 6, walk 8, run 8, jump 6 (anticipation, rise, apex, fall, land, recover), attack 6–8 per swing (3-hit combo), hurt 3, death 6 — × 8 directions.

---

## 6. Judge checklist (pass/fail per sprite sheet)
1. Silhouette alone identifies her: bun + big bow, tall collar, bell sleeves, petal skirt, katana with hook.
2. Palette: only `docs/palette.json` colors, ramps used in order, red hue-shifts to violet in shadows.
3. Lighting from top-left in all 8 directions; 3-tone cel; selective colored outline.
4. Chibi proportions per §3 (≈ 2.75 H body, sword ≈ 2 H).
5. Asymmetry correct per §0.5 in all directions.
6. Secondary motion (scarf, sleeves, skirt, bow) lags and settles.
7. Feet pivot stable; no jitter, no orphan pixels, no AA halos.
