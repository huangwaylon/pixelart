# DESIGN LOCK: swordswoman sprite (owner-approved 2026-10-30)

This is the frozen reference. Nothing here changes without an explicit owner decision, and every build and every review is judged against it.
Source: `docs/team_review/2026-10-30/00_SUMMARY.md` (+ 01/02/03). Pipeline assets are reused from `../2026-10-28_sw_skinned/`
(rig r13, motion, renderer, pixel chain). Only new code goes in this folder.

## 1. Face: eyes + eyebrows only
- **No nose, no mouth, no blush.** Face skin is flat `s`.
- Colours: `K` lash/pupil/closed line · `g` lower iris · `W` one catchlight, always on the left side of the iris on screen · `h` brow
  (drawn in `K` where it falls on hair, so brows show through the bangs).
- 7 expressions, made only from eye shape + brow angle: open, half, closed, happy ^^, determined, surprised, hurt ><.
- Size: 5 px wide eyes facing the camera, 4 px for the far SE eye and the E profile eye. SW/W are mirrors, NE shows a 2 px lash tip, N shows nothing.
- **Attachment:** exact pixel templates (`docs/team_review/2026-10-30/face_palette/scripts/facesys.py`) are placed at a **point tracked on
  the 3D head surface** (option b′, ≤ 0.5 px off) and hidden by hair/hands from the 3D depth. An eye less than 60 % visible is dropped whole. The SE far eye gets
  2-frame hysteresis. Position and hiding come from the 3D model; only the eye/brow shapes are fixed (owner-approved exception).

## 2. Locked palette: 14 colours
`K` outline · hair/boots/socks `h H g L` · skin `s S` · red `e E R` · obi `Q O o` · `W`.
- Dropped: `D d` (sock darks), `m` (mouth), `k` (blush).
- **Socks and boots are lighter than the outline** (use `H`/`g`, never `K` fills), so the legs separate from each other and from the line.
- Tone is chosen by **normal-vs-light band**, not by texture: 2-tone flat shading (base + shadow, plus one highlight only on hair `L`).
- Colours stay consistent across all 8 directions: the same material and band always give the same colour. Gate: colours per frame ≤ 14, no off-palette pixels,
  no material using another material's colours.

## 3. Line art
- **Outer outline:** closed, 1 px, near-black `K`. Optional sel-out (one shade darker on lit edges) on red, skin and obi only, never on hair,
  socks or boots.
- **Slopes:** curves are drawn with clean, uniform runs (1:1, 1:2, 1:3, 2:1 …). No 1-3-1 zigzags, no redundant L-corners (pixel-perfect), no 2×2 `K` clumps.
  The method is the vector-line prototype (`docs/team_review/2026-10-30/line_art/proto_vecline.py`): trace the 8x silhouette, smooth it, redraw at 1x.
- **Interior lines only at listed overlaps:** leg/leg, arm over body, hand/sleeve, bangs/face, bow/hair, chin/neck. Each is at least 4 px long, and they come from the
  3D part/depth edges. No other interior `K`.
- **Temporal:** the outline is stable frame to frame; no line pixel appears for a single frame and then disappears.
- **Gates (per clip):** zigzags ≤ 1/frame, L-corners ≤ 2/frame, outline gaps 0, 2×2 clumps 0, interior `K` only at listed overlaps.

## 4. Silhouette simplifications
- **Sleeves:** narrower, simpler sleeves, so arms and hands read outside them. No bell-sleeve wings.
- **Waist:** a clear waist break at the obi (lavender band visible across the front, slight inward step), so the dress is never a poncho blob.
- **Legs:** lighter sock/boot ramp (see palette) and at least 2 px of gap or a separating line between the legs.

## 5. Motion (keep what works)
- Natural, upright, feminine stance (posture gates), head forward over the neck, asymmetric bent arms, root motion for planted feet.
- **Secondary motion simplified to about 10 spring bones:** bun 1, bow 2, back hair 2, side locks 2 (1 each), skirt front/back 2, sleeve tips
  (1 shared). Everything else is driven or static.

## 6. Process
- **Milestone 1 is walk SE only.** Two **gold frames** (contact, passing), hand-polished to this lock and approved by the owner, define "done".
  The pipeline is tuned to match them, and the last fixes go through the snowpeak-style override layer (sparse, with a reason, stale-checked).
- One change set per round, judged against the gold frames, not against "the previous build".
- Only gates that map to the owner's words block a build: line gates, palette gates, limb connectivity, posture, loop/timing. Boil and shade_swap
  are reported only.
- Lean: at most 2 agents at a time, and one critique per round.

## Amendment 1 (owner, 2026-10-30)
- **Gold frames:** the clean style is approved. Revise the poses: a stronger SE 3/4 turn of head + body, a more dynamic contact stride and arm swing,
  and a passing pose clearly different from contact (lively, natural, feminine, per the earlier motion notes). The revised frames become the gold standard.
- **Hair:** use the **master's longer, wavier side locks** framing the face (EC0_SE_96), not the jaw-length bob. Full bangs, eyes clear.
- **Shared SE standard (lead):** the gold frames and the pipeline use the **same view angle and proportions as the master EC0_SE_96**. That covers the
  3/4 turn amount, head width, visible neck, collar V, a wide obi band across the front, leg length and boot size. The pipeline reaches the angle with a per-view body
  yaw cheat, and both are measured against the master's silhouette (IoU).

## Amendment 2 (owner, 2026-10-30)
> Gold v2: "nope, not good at all." Garment volume: "needs to be more based on the 3D models."
- The hand-authored gold frames (v1, v2) are **rejected**. Targets are no longer hand-drawn from the 2D master.
- **Shapes, proportions, garments and poses come from the 3D model** (rig + motion). The 2D master is a colour/style reference only.
  The pixel art is the 3D render made clean: lines, palette, eyes+brows.
- Section 4 "silhouette simplifications" (narrow sleeves etc.) is superseded where it conflicts with the 3D model's garments. Silhouette changes are
  made **in the 3D model**, not in 2D.
