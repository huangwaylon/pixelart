# r8 Designer A

Both: jump_v2, ppu 0.75, 48 px frame, `regularize` on. QA PASS. Max colours per frame: C1 16, C2 15. Jaggies: C1 40, C2 11. Builds: C1 9, C2 8.

## C1_twintails: strongest kawaii read
**Intent:** Lyra-style twin tails, cream earmuffs, red scarf, red bows on the tail ties.
**Final:**
- Hair ramp `plum_0,hair_1,hair_1,hair_2` (dark brown).
- Earmuff band on oat; muffs 2.4x3.2.
- Coat `char_1,lav_1,mauve` (mid lavender).
- Tails: `tail_len` 1.75, `rest_dir` (±0.5,-1,-0.45), stiffness 450, gravity 900.
- Two bow loops per tie via `add_prims`.

**Strengths:** best silhouette. Tails read at 1x from S, N and profile, and flare like wings on landing. Squint: four clean masses.
**Weaknesses:** bows are about 2x2 px and look like specks in E/W. Scarf covers the chin.

## C2_hime_beret: elegant-cute
**Intent:** black hime cut, small tilted red beret, side bow, cream duffle.
**Final:**
- Hair ramp `ink,char_1,lav_1` (violet-black), angel ring off.
- Duffle `mauve,oat_1,oat_2`, toggles removed.
- Beret 9.2x2.0x8.4 at x -5, tilted 24°, overhanging about 2 px.
- Hair-cap top clip removed.
- Shorter `hair_back`. Three flared locks, stiffness 70.

**Strengths:** most feminine and grown-up. Black, cream and red read clearly on snow. Side locks frame the face.
**Weaknesses:** egg silhouette with only the beret notch. The beret is a big red dome from E/W. The hair edge gets lost on dark tiles.

## Generator limitations hit
1. `material_bands` can't be overridden per variant. Workaround: a 4-entry hair ramp, where ramp[-1] only feeds the angel ring.
2. The angel ring sits 2 rows below the top hair pixel. Under a beret it lands on the brow.
3. Default `tie_*` and `ribbon_side` prims sit inside `hair_cap`, so they are invisible until moved.
4. The beret's top clip leaves a bald hole if the beret is shrunk.
5. Keyframed fall acceleration (about 1850 u/s²) is greater than chain gravity. At default stiffness the tails point straight up at touchdown.
6. Accents under 3 px render as 1-2 px specks.
7. Eye decals are a fixed size, so ppu 1.0 would shrink the eyes relative to the head. Not tried.
