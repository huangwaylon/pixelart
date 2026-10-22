# r12 HD round 2 - Game Director re-review

**Verdict: APPROVED** (one doc correction to make while cutting the release)

## Verified
- **Soles (GD3):** walk and carry_walk soles are now at y<=58 in every frame.
- **Run height (GD4):** standing height is 33-34 (spread 1). Before it was 33-35.
- **Hem (GD5):** a rust row over a dark row separates coat from legs at 1x. Checked E/W/S on snow #ECF2F8 and rock #423E4A. 1x/2x readability is equal to v1 or better.
- **Contract vs `releases/S4_actions_v1`:** all 13 clips match on these:
  - frameSize 48x64, pivot (24,57), sheet sizes, frame counts, durations, events, cancel windows, root_px and z_px;
  - hand_R, hand_L and carry anchors (identical);
  - shadow and fx strips (byte-identical);
  - no pixels touching the frame edge, no semi-alpha, at most 16 colours.
- **QA:** 13/13 PASS, 0 warnings. max_height_delta is the same as v1 or lower, except climb and pick_up (1 -> 2).
- **Bow springs:** these are acceptable for gameplay.
  - The top-of-sprite envelope matches v1 in every clip except run N (y=21 vs 22, so +1 px). The +1 px clearance budget already covers this.
  - The horizontal extent stays within x 9-38, the same as v1.
  - Condition: collision and clearance must use a fixed capsule from the pivot, never per-frame pixel bounds.

## Fixes
1. **The README prop-layer detail is stale.** throw json now differs from v1 only at frame 0 W (back -> split). The "f0 E/W, f1 E" wording is out of date. The ship-as-a-set rule is still correct. Fix this in the release README.

## Must go into `releases/S4_hd_actions_v1` (leave v1 untouched)
- All 13 clips, each with `_sheet.png`, `_sheet.json`, `_shadow`, `_fx_front`, `_fx_back`, the `prop_front`/`prop_back` strips where present, and `qa_report.md`.
- Also: `props/*.json` copied from v1, `overrides/variants/S4_hd/` (jump_sc, land), and the buildHash.
- **README** stating:
  - the HD body, json and prop strips are one set, never mixed with v1;
  - +1 px head-clearance and occlusion-sort budget;
  - capsule collision only (the bow loops bounce);
  - the new y=59 frames: climb 2 -> 6, climb_top NW0, throw/land (lunges, not locomotion);
  - the biome shadow tint is a separate ticket.
