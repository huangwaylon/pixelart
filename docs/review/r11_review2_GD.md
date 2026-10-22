# r11 Review 2: Game Director

The script `/tmp/gd_r11/check_r11.py` now checks the final prop schema:
- one `ref` declaration that matches `data/props/<id>.json`
- `frame.prop{ids,visible,layer[dir]}`
- `layers.prop` strip on the same grid, with pixels only on visible frames
- front-layer prop pixels over the head

Output: `/tmp/gd_r11/report_r2.txt`. I accepted two plan changes from round 1: pick_up is now 9 frames / 700 ms (wpC) and carry_throw is 540 ms with `throw_release` on f2 (wpD). **Update the plan table to match.**

## Script results

| clip | result | notes |
|---|---|---|
| idle, walk, run, fall, climb, climb_top | PASS | |
| pick_up, carry_idle, carry_walk | PASS | WARN: front-layer crate overlaps the hair top (45-55 px) |
| throw | PASS* | height at exit: NW is 2 px taller than idle |
| jump_sc, land | PASS* | height at exit: W is 2 px taller than idle |
| carry_throw | FAIL | prop is still visible on the release frame; height at exit: NW is 2 px taller |

\* The only failure is the 1 px exit-height tolerance. These three one-shots still pass that check structurally.

## Round-1 items

| item | status |
|---|---|
| land: cancel at f3, lock 120 ms | FIXED |
| land: `derivedFrom` | FIXED |
| props in a separate strip, per-frame layer | FIXED (all 5 prop clips; strip pixels match `visible` exactly) |
| pick_up: duplicate `props[]` | FIXED (single `ref: crate`) |
| pick_up: 18 colours | FIXED (body is 15 or fewer) |
| crate: thin column in E/W | FIXED (box with real depth) |
| carry offset differs from plan | RESOLVED: 19.2 is correct, (0,3,1.5) can't work |
| crate clears the head | PARTIAL: 3D clearance is 2u, but on screen it overlaps the hair (see new issue 2) |
| run: lean, stride, arm pump | **NOT FIXED** (only the trail wind changed) |

## New issues

1. **Exit pop into idle.** The rebuilt idle `rest` frame (f1) is 1 px shorter. As a result, the land, jump_sc, throw and carry_throw `ready` frames are 1-2 px taller than idle, and the head dips 2 px in W/NW on the handoff. Fix: start idle at f2 (`inhale`) after a one-shot, or re-key `rest` to match `ready`.
2. **Crate reads as part of the hair.** The brown crate over the brown hair in NE/NW/E/W fuses into one silhouette at 4x. Add a dark sel-out row along the bottom edge of the crate, or lighten the wood one step.
3. **carry_throw f2.** `throw_release` fires on f2, but `prop.visible` is still true and the strip still draws the crate. That risks drawing the crate and the projectile together for 70 ms. Set `visible:false` on f2 and leave that frame of the strip empty, as throw does.

## Verdicts

- **idle: CHANGES** (minor). Fix the exit-height pop (issue 1).
- **walk: APPROVE.**
- **run: CHANGES.**
  - Widen the stride by 2-3 px.
  - Put the head 1-2 px ahead of the hips in E/W/SE/SW.
  - Pump the elbows clear of the torso.
- **jump_sc, fall, land: APPROVE.** Approved once issue 1 is fixed, which is an idle-side fix.
- **climb, climb_top: APPROVE.**
- **pick_up: APPROVE.** The crate outline (issue 2) is nice to have.
- **carry_idle, carry_walk: CHANGES** (minor). Fix the crate outline (issue 2).
- **throw: APPROVE.**
- **carry_throw: CHANGES.** Hide the prop on the release frame (issue 3).
