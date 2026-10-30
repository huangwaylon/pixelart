# charlab review r1: panel verdict (art, animation and game direction), 2026-10-30

**Inputs:** 8 characters x 3 tiers x 3 bodies x 4 sizes (288 cells). We looked at every `boards.png` and at the 4x sheets and 1x strips for 11 key cells. We ran `pxeval seq` on 10 SE walks and a connectivity scan over all 6,912 frames. We also got an Opus second opinion.
**Outputs (in `review_r1/`):**
- `top_picks.png` ranks the best cell per character (1x + 4x, S/SE/E).
- `top3_walk_4x.gif` shows the walks of Rio, Hana and Nova (loop, 120 ms).
- `defects.png` has one frame per defect.
- `fragments.json`, `opus_critique.txt`, and `scripts/` (the scripts that rebuild these files).

## Verdict
This pipeline is the first in the repo that we would call *a viable base generator*. Colours are locked and consistent. The outline is clean: zigzags are gone, and mono runs make the line art look hand-placed at 1x. Faces stay to the owner's eyes + brows rule. Silhouettes at medium/compact/64 read at 1x.

It is **not yet "beautiful"**, for three reasons:
1. The bodies are tubes and barrels with A-pose arms, so posture doesn't read as feminine.
2. Thin limbs break apart at 64-96 px.
3. The E (profile) view loses the face on half the cast.

All three are fixable in code or design. None of them needs a new approach.

## Scores: best cell per character (1-5)
| # | character | best cell | sil. 1x | line | colour | face | walk | appeal | feasibility |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Rio** (mechanic) | medium/compact/64 | 5 | 4 | 5 | 4 | 4 | 4 | **4** |
| 2 | **Hana** (schoolgirl) | medium/compact/64 | 5 | 4 | 4 | 4 (E: 2) | 3 | 5 | **4** |
| 3 | **Nova** (astronaut) | medium/chibi/48 | 5 | 5 | 4 | 4 (E: 1) | 3 | 5 | **4** |
| 4 | Zip (courier) | medium/compact/64 | 4 | 4 | 4 | 3 | 4 | 3 | 3 |
| 5 | Mika (shorthair) | medium/chibi/48 | 4 | 5 | 4 | 4 | 3 | 3 | 3 |
| 6 | Kai (runner) | medium/compact/64 | 3 | 4 | 4 | 4 | 3 | 3 | 3 |
| 7 | Fern (ranger) | medium/compact/64 | 3 | 3 | 3 | 3 | 3 | 3 | 2 |
| 8 | Marin (diver) | medium/compact/64 | 3 | 3 | 3 | 3 | 3 | 2 | 2 |

**Notes per character:**
- **Rio:** the red bandana and yellow gloves mark the head and hands in every frame, and her ponytail swing is the liveliest secondary motion in the set. Her torso is a barrel, though, and the white tee shows as blotchy "drips" under the bib.
- **Hana:** the most iconic design. The navy/white stack and the rigid skirt are clean. But in E the bob covers the face and the red tie floats off the chest. Her palette has grown to 14 colours, over the cap of 12.
- **Nova:** the cutest, and she has the cleanest outline at 48. But the E view is a faceless white blob, and her walk is the stiffest (articulation .13, pose range .17).
- **Zip:** has the best colour pop, but from S the cap reads as a beanie, and pink against green muddles in E.
- **Mika:** the compact build reads as boyish because the hoodie hides the waist. As a chibi she is charming but generic.
- **Kai:** from S her ponytail reads as a spike on top of her head (`defects.png` D4). Her slim build breaks apart.
- **Fern:** the chibi hat is a mushroom over the face. Khaki on skin has low contrast.
- **Marin:** a dark suit plus fragmented teal stripes. The bun reads as a cone, and the fins turn to specks.

**The Opus second opinion** agrees with this top group: Hana, then Rio, then Mika and Nova. Its 5 defects, ranked, match ours: limb breakup, non-feminine bodies, a weightless walk, blotchy shading, and unreliable faces. It calls the approach "about 70% of the way, viable as a base generator" and budgets 1-2 hours of hand polish per character for faces, hands and feet. It puts Fern last and Marin 7th, where we have them the other way round.

## Matrix: sweet spots and breakpoints
Share of frames whose sprite splits into more than one piece (detached shin, boot, tie or arm). The current gap gate does not catch these.

| body \ px | 32 | 48 | 64 | 96 |
|---|---|---|---|---|
| chibi | 0 % | 1.7 % | 3.1 % | 4.5 % |
| compact | 0 % | 2.4 % | 8.0 % | 2.3 % |
| slim | 0 % | 1.0 % | **18.4 %** | **22.6 %** |

- **Overall sweet spot: medium tier / compact body / 64 px.** All 8 characters read there, faces get eyes + brows, and pxeval boil is low (.010-.016).
  - The second product direction is **medium / chibi / 48** (Nova, Mika). It has zero fragments, boil .006, and the strongest appeal per pixel. Don't mix the two in one cast.
- **Size:**
  - 32 px never fragments, thanks to the 2-px widening, but faces are 1-px eyes and silhouettes are generic.
  - 48 is right for chibi.
  - 64 is right for compact.
  - 96 adds nothing the owner asked for. Silhouette boil is .15-.20 (pxeval flags BOILING on Rio at 96), and it fragments. **Drop 96** until there is a temporal line snap.
- **Body:**
  - Chibi is best at 32-48.
  - Compact is the all-rounder.
  - **Slim breaks everywhere.** At 32-48 its limbs are 2-px stick bundles with the most clumps (2x2 mean 10). At 64-96 they come apart, with 1-px arms and floating boots. pxeval flags BOILING on Kai/slim/64 (.028) and Fern/slim/64 (.021). Slim is not shippable as it stands.
- **Tier:**
  - Medium is the best at every size: it adds the identity marks (Kai's headband, Nova's rings, Rio's bandana).
  - The simple tier loses the identity marks.
  - Detailed decals turn into 1-3 px specks below 64, and even at 64 they add noise but no read (Marin's fins, Kai's bib number, Nova's antenna).
- **Views:**
  - S and SE are good.
  - **E is broken for haired and helmeted characters.** The gates count an eye in E, but on Hana, Fern and Zip it lands on the hair edge. Frames with zero eyes in E: Fern 43 %, Hana 34 %, Zip 13 %.
- **Motion (pxeval seq, SE):**
  - Every cell is flagged FEET_JITTER (feet range 3-4 px) and almost every cell SHADE_SWAP (cel bands flip between frames).
  - Articulation is .19-.28 for compact/chibi and .40 for slim; slim's figure is more pixels in motion, which shows up as boil.
  - The S view barely moves: the legs scissor under a static torso, and the arms hang about 20° out from the body.

## Round 2 recommendation
Iterate **3 characters**:
- **Rio** and **Hana** at **medium / compact / 64**.
- **Nova** at **medium / chibi / 48**, as the chibi-direction control.

Keep Zip as a spare. Park Kai (until a slim rebuild), Fern, Marin, and Mika in her current form. Cells: S/SE/E plus mirrored W/SW. 48 px compact can be a read check only.

### Ranked fix list
| # | owner | fix |
|---|---|---|
| 1 | **lab** | **Limb connectivity.** Floor the limb radius in *output pixels* at every size: at least 3 px of fill at 64, at least 2 px at 48 (today the floor only bites at small f). Add a blocking gate: one 8-connected component per frame. Fuse the tie, scarf and decals into the chest SDF so they cannot float (Hana E). |
| 2 | **design + lab** | **Feminine body preset (`compact_f`).** Waist about 0.8x the chest, hips ≥ shoulders, narrower shoulders, a slightly longer neck, smaller hands. At rest the arms sit 6-8° from the body (not about 20°) with a 10° elbow bend. Rio: replace the belly ellipsoid with a waisted torso under the overalls. Mika: crop the hoodie or add a skirt option. |
| 3 | **lab** | **Walk.** In S, raise hip roll and sway (5-6 %) and keep the 1-px bob on contact/passing. Narrow the step so the feet fall nearly on one line (a feminine cross-step). Reduce arm swing to 12-14° with a 15-25° elbow bend; the hands should pass the hip, not flare out. Add 2-3° of shoulder counter-rotation that is visible in S. Lock the planted foot to whole pixels (FEET_JITTER). Nova needs a bigger pose range: knee lift and helmet bob. |
| 4 | **lab** | **Profile face.** In E, stamp the eye only on skin, and gate eyes-on-skin rather than eyes-placed. If there is no free skin, push the face skin forward or trim the hair. Cut the hair side mass behind the eye line before pixelizing. Nova: render the visor in profile as a light-blue crescent with the eye inside it. |
| 5 | **lab** | **Shading stability.** Add per-part band hysteresis across frames (SHADE_SWAP), raise the minimum band island to about 6 px at 64, and give white and other light materials one flat tone plus the outline (Rio's tee). |
| 6 | **design** | **Silhouette fixes.** Kai: move the ponytail to the nape, or add side volume so S isn't a spike. Zip: put a value gap between cap and hair and tilt the brim down so it shows from S. Fern: shrink the hat brim by 25 % and give the shorts warmer contrast. Hana: keep the palette at 12. |
| 7 | **lab** | **Tier rule.** Decals need at least 64 px *and* a projected area of at least 6 px, or they are skipped. Remove fins from the walk (they are a different gait). |
| 8 | **lab** | **Scope.** Skip slim below 64 and skip 96 entirely until the temporal line snap exists. Add `n_components`, `eyes_on_skin` and pxeval `shade_swap` to `summary.json`. |

### Exit criteria for round 2
- Zero fragmented frames.
- Eyes on skin in every S/SE/E frame.
- pxeval boil ≤ .015 and no SHADE_SWAP flag.
- Owner rates Rio and Hana as "feminine posture" at 1x.
- Opus re-check ranks the top 3 at feasibility 4 or higher.

processes: none left running
