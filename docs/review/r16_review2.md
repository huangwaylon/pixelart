# r16 review 2: S fringe (AD + animation)

**Verdict: APPROVED** for r16. The Gemini check is still owed; see below.

## Pixel check (S frames of idle, walk, run, throw, jump_sc, carry_walk)
- **Idle S f0:** matches the spec.
  - Clumps are at x17-20, x22-25 and x27-30.
  - Dark `#4A2448` notches are at x21 and x26 on y29, with `#D07C74` below them on y30. There is no dark on the hem row.
  - Highlights are at x18-19, x23-24 and x28-29.
  - The y31 shadow is in runs of 2 and 4 px.
  - Shadow at x28-29 under the right clump was not in my spec, but it makes the row symmetric. Accepted.
- **Lock:** notches sit at eyeL+2 and eyeL+7, 3 rows above the eyes, in every S frame of every clip. The exceptions are squint frames (throw f4-5, jump_sc f2-6/f10), where the 1-px eyes shift the measurement but the notches don't move, and the idle f5 blink.
- **Flicker:** S frame-to-frame deltas in the fringe area are equal to or lower than `releases/S4_hd_actions_v1` (run 6-22 vs 6-23; carry_walk 9-16 vs 17-29). SE/SW are unchanged from round 1, the notches hold, and the eyes don't jitter.

## Non-blocking (r17)
1. **throw f0:** 2 px of skin `#EBA586` show at x18-19 on the hem row. Fold them into the clump.
2. **S cheeks:** still 10 px wide. The cheek narrowing was rightly rejected, so the fix belongs in the r17 model (5-head jaw).
3. **E/W:** the fringe still doesn't overhang off the forehead (deferred from r16).

## Gemini
`gemini_critique.sh r16_face_bangs_r2` failed twice on auth ("No authentication method found"; AppleConnect sign-in did not take). No critique exists yet. Rerun it once auth works. Approval stands unless it finds a 1x readability blocker in S.
