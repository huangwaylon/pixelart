# r16 - slimmer, pointed face + layered bangs (S4_hd)

## Mockups (00_REVIEW/r16_face_slim_bangs/options_x10.png)
These are pixel edits on real r15 idle S/SE/E frames.

**Face options**
- FA: trim at the same length (10-6-2).
- FB: V-taper with the chin 1 row longer (10-8-6-2, steps 1-1-2).
- FC: curve with a forward chin (10-8-4-2).

**Bang options**
- B1: two tones with a cast-shadow row.
- B2: B1 plus flicked, crossing tips.
- B3: dark shell underside.

## AD
- **Face: FB.**
  - FA only shortens the face, so it reads pinched and babyish.
  - FC's 1-2-1 step makes a lumpy jaw, and its profile chin juts.
  - FB keeps the eye rows and adds length below them, so the face reads older without shrinking the eyes. That is the "realistic, pointy" ask.
- **Bangs: B1.**
  - B3's dark band reads as a headband.
  - B2's 1-px flicks become speckle at 1x.
  - B1 shows the lift through the shadow row, and the layering through dark back tips between mid-tone front clumps that carry the highlight.
  - The tip curl and flick live in the model, where they read in hi-res without adding sprite noise.

## Implementation
- **Model:** narrower, lower jaw; chin 1.55 longer and sharper. The two-layer fringe shell stands 0.7 off the forehead. The back clumps use the dark `hair_dk` material and only their tips show.
- **Rules:**
  - The gap row under the hem is a cast skin shadow.
  - Back-layer pixels are drawn in the dark tone and protected from despeckle.
  - The hem fill keeps each clump's tone.
  - The r15 hem pin, lash rule and pocket rules are unchanged.

## Checks
- Rows under the eyes: S 10-8-5-2, 3/4 8-8-6-1, profile chin 1 px.
- The bang-to-lash gap is a constant 1 row in S/SE/SW run, walk and carry_walk, r14 copies included.
- 0 lone face-hair pixels.
- 27/27 builds pass QA.
- S4_halfup_bow is byte-identical.
