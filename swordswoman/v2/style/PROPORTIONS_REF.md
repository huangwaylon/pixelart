# PROPORTIONS_REF: measured Pokemon trainer proportions vs ours (2026-10-26, STYLE strand)

Overlay with the measured landmark lines (crown, eye centre, chin, shoulder, waist, crotch/hem, sole): `v2/style/prop/proportions_overlay.png` (1360 px; `_thumb.png` is 1000 px). Per-sprite pixel rulers: `prop/r_lyra.png`, `r_dawn.png`, `r_hilda.png`, `r_rosa.png`, `r_ow.png`. Script: `tools/propoverlay.py` (it holds the landmark rows).
How it was measured: the landmark rows are read by eye from 7x/9x ruler overlays and are good to about ±1 px. "Crown" is the top of the skull or hair mass. Hats, ponytail spikes, buns and our bow are left out. Head height runs from the crown to the chin, and head width is the widest point of the hair mass. All refs are official sprites (Showdown 80x80 battle pics; Gen5-style overworld from the Essentials kit, stored at 2x and measured at 1x).

## Table
| sprite | fig px (crown-sole) | heads tall | head % of H | legs % (crotch/hem-sole) | shoulder / head W | waist / head W | eye centre (fraction down head) | eye h / head h | eye w px, gap px | neck |
|---|---|---|---|---|---|---|---|---|---|---|
| Lyra HGSS battle | 62 | 3.6 | 27% | 45% | 0.78 | 0.50 | 0.68 | 0.18 | 2-3, 3 | 2 rows, 3-4 px wide |
| Dawn DPPt battle | 62 | 3.4 | 29% | 40% | 0.65 | 0.45 | 0.61 | 0.22 | 2-3, 3-4 | 1-2 rows |
| Hilda BW battle | 67 | 3.5 | 28% | 43% | 0.78 | 0.61 (vest) | 0.68 | 0.21 | 3, 3-4 | 2-3 rows |
| Rosa B2W2 battle | 64 | 3.2 | 31% | 42% | 0.73 | 0.50 | 0.65 | 0.20 | 3, 4 | 1-2 rows |
| BW-style overworld female (NPC_08) | 29 | 1.6 | 62% | 14% | 0.61 | 0.50 | 0.78 | 0.22 | 2, 4-5 | none |
| Gen3 overworld May / Lass | 20 | 1.7 | ~60% | ~15% | ~0.7 | - | ~0.75 | 1-2 px | 1x2 black | none |
| **OURS C_r4 (48 px)** | 43 | **2.3** | **44%** | **23%** | **0.96** | **0.96** | **0.58** | 0.21 | 3, 4 | **none** |
| **OURS A_r4 (32 px)** | 28 | **2.2** | **46%** | **21%** | **0.94** | **0.94** | **0.58** | 0.23 | 2, 3 | **none** |

## Shape notes (battle trainers, which are the "graceful" ones the user means)
- **Head and face:** the hair mass is wide (18-22 px), but the face inside it is narrow (9-10 px, about half the head width). The jaw runs diagonally in 1:1 steps from below the ear to a small pointed or soft-V chin over the last 3-4 rows. There is no round "mochi" cheek.
- **Eyes:** they sit low, with the centre 0.61-0.68 down the head, so the fringe and skull take the upper 55%. Each eye is 2-3 px wide and 3-4 px tall (about 0.2 of head height). The eyes are 3-4 px apart, about 1-1.5 eye widths. They have a dark lash cap, a dark iris and a 1 px glint. The mouth is 1-2 px, 2-3 rows below the eyes.
- **Neck:** always visible in battle sprites, 1-3 rows tall and 3-4 px wide (about 0.2 of head width). This is a big part of what reads as "graceful".
- **Torso:** shoulders are 0.65-0.78 of the head width. The waist is about 0.5 of the head width, and it pinches visibly between ribcage and hips. Hips and skirt flare back out to about 0.7-0.9 of the head width.
- **Arms:** thin, with the upper arm 2-3 px wide. A relaxed arm reaches crotch or upper-thigh level (shoulder to fingertip is about 0.37-0.4 of height). Hands are distinct, 3-4 px.
- **Legs:** about 40-45% of the figure height, 3-5 px wide, tapering to the ankle, with a knee break and real feet (boots 4-6 px long).
- **Overworld sprites are the opposite recipe:** a super-chibi of 1.6-1.7 heads, where the head is 60% of the height and sits on a tiny narrow body (shoulders 0.6 of head width). They read as cute rather than graceful, but the body is still narrow and never as wide as the head.

## Why ours reads "fat and awkward" (measured)
1. **The body is as wide as the head.** Shoulder and waist are both 0.94-0.96 of head width. Pokemon uses 0.65-0.78 for shoulders and about 0.5 for the waist. The trapezoid dress with no waist is the main cause.
2. **The proportions fall between the two Pokemon recipes.** At 2.2-2.3 heads we are neither the 1.6-head overworld chibi nor the 3.2-3.6-head battle figure.
3. **The legs are short.** They are 21-23% of height, against 40-45% for battle trainers.
4. **There is no neck,** and the face is wide and round, filling the whole width under the hair.
5. **The eyes sit high.** The eye centre is 0.58 down the head, against 0.61-0.68 (0.78 on overworld sprites).

## Recommendation to the design strand (proportion targets)
- **Target "slim trainer chibi": 3.0-3.3 heads.**
  - Shoulders 0.70-0.75 of head width; waist 0.50; skirt hem 0.8 of head width.
  - Legs 35-40% of height; neck 1-2 rows visible.
  - Face width about 0.55 of head width, with a V/soft chin.
  - Eye centre 0.65 down the head; arms reaching mid-thigh.
- **Figure size.** A slim figure needs more pixels than 32 for the face to read.
  - **At 32 px and 3.2 heads, the head is only 10 px.** That allows only 1x2 Gen3-style eyes, with no glint and no chin taper. Reject it for this proportion.
  - **At 40 px (48x48 cell), the head is about 12.5-13 px.** That fits 2x3 eyes plus fringe, mouth and a 2-step chin. It is the minimum, comparable to PMD Gallade.
  - **At 44-48 px (64x64 cell), the head is 14-15 px.** That fits 2-3 x 3-4 eyes, a visible neck, 3-4 px legs and a 2 px katana. **This size is recommended.** It keeps the existing 64 cell and the actions pipeline.
- If the user prefers cute over graceful, the authentic alternative is the overworld recipe: 1.7 heads at 32 px with a narrow body. The measurements suggest that this is not what was asked for.
