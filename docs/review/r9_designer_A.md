# r9 Designer A

Both extend S0 (cw_oatmeal). QA PASS on jump_v2 and jump_sc, `chain_penetrations` 0.
- S1: jaggies 72 / 85, max 15 colours, 5 builds.
- S2: jaggies 70 / 79, max 15 colours, 7 builds.

## S1_waist_beret: elegant
**Intent:** waist-length hime hair with flared ends, a small tilted teal beret, a red side ribbon, belted A-line coat.
**Key:**
- waist 0.66, hip 1.16, flare 1.30.
- Beret 6.9x1.8x6.5, rot z 24, x -3.2.
- Red ribbon ramp.
- Outer locks anchored ±6.4, `rest_dir` x ±0.5, tips swell. Stiffness 60, gravity 700.
- `scarf_len` 1.8.

**Strengths:** the hair makes a bell shape at the hips (S/N). The beret notch and ribbon are on consistent sides. The hair swings in the jump.
**Weaknesses:** the hair hides the waist in N/E. The beret highlight is large in SE.

## S2_long_twintails: playful
**Intent:** high twin tails below the hem, teal earmuffs, red ties, short flared coat.
**Key:**
- `tail_len` 2.2, anchors (±9.6, 11.8, -3.6), `rest_dir` (±0.12, -1, -0.25).
- Tail stiffness 220, gravity 1000.
- Muffs 2.0x2.7, raised.
- `coat_len` 0.3, flare 1.30, waist 0.66.
- Scarf `rest_dir` (0.3, -1, 0.55).

**Strengths:** the most striking silhouette, an inverted V front and back with streamers in 3/4. Reads at 1x.
**Weaknesses:** the tails flare outward and look stiff. The teal muffs sit near the teal scarf in profile.

## Generator limits hit
1. Short or flared coat: in scrunch the scarf jams between thighs and skirt, and collision stretches it to the floor (margin FAIL). Stiffer scarf or lower `max_swing` made it worse. Fixed with a forward `rest_dir`.
2. `chain_overrides` can't add chains (3 locks max).
3. Body collision pushes the tails outward. No per-chain plumb or collide toggle.
