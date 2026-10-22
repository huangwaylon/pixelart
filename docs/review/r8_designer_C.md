# r8 Designer C: C5 buns + ribbons, C6 bob without a hat

Built on jump_v2 with `regularize`; both pass QA.

## C5_buns_ribbon (7 builds)
**Intent:** a sweet, round odango girl with rose bows and a short scarf.

**Final choices:**
- `cw_lavender`, espresso hair. `hair_espresso: [plum_0, hair_1, hair_1, hair_2]` gives a flat dark mass, with hair_2 only in the angel ring.
- Lav_1/mauve coat. Rose scarf, ribbon and mittens (crn_1/crn_2/red_2), scarf length 1.5.
- Buns r4.0 at y18.6 with z=0 (S/N heights match).
- `hair_cap` clip set to -0.45 for an updo.
- Two-loop bows on the front of each bun, plus back bows that read from N.

**Strengths:** the "mouse-ear" silhouette reads at 1x from S and N. The squint row shows 4 masses. 9 jaggies.

**Weaknesses:** the hair has little form and the face is a narrow band. In E/W the buns merge into one topknot.

## C6_bob_nohat (7 builds)
**Intent:** the face and hair carry the charm. Blue-black bob, side-swept bangs, an ahoge and a gold clip, a rose duffle coat, a navy skirt and tights.

**Final choices:**
- `cw_charcoal`, `hair_blueblack: [ink, navy_1, navy_1, navy_2]`.
- crn coat, oat scarf, mittens and boot cuffs, gold clip.
- Enlarged ink/navy skirt, hair volume 1.12, fringe rotated -20 degrees, ahoge moved off-centre.

**Strengths:** the clearest hue read (navy, skin, rose, cream); feminine.

**Weaknesses:** the bob reads as a helmet with no visible flip. The cream scarf partly merges with the face when you squint. 54 jaggies.

## Generator limitations hit
1. `bangs` is ignored for `bob`; faked via `fringe` override.
2. With no hat, skin pokes out at the temples like elf ears. `temple_cover` only runs when a hat cuff exists.
3. `buns`: the ties are hidden inside `hair_cap`, and the -0.72 cap clip hangs hair below the updo.
4. Hair bands are fixed per palette, so I used a 4-entry ramp hack.
5. The `group: hat` clip picked up red_1 from the `hat` ramp.
6. `regularize` eats 1-2 px protrusions; bows/ahoge oversized.
7. jump_v2's head turn hides the face in E f5-8 when there is no hat.
