# r4 Character Designer: Proportion study (cw_charcoal)

Board: `archive/snowpeak/boards_r04_r10/proportions_keys.png` (built with `--cell-h 312`, so every variant shows at x3). Shared outfit: bob, beanie with `pom_size` 1.5, parka, long scarf, pants, snow boots. Heads = standing height / skull height. QA margin and orphan checks pass on all five. Only height-delta errors are left.

**A · Chibi (~2.6 heads, 46 px).** Balanced baseline. Head 9.4 and leg 8.6 set it apart from B. Strengths: 2x3 eyes, pants read above the boots, feet planted in all directions. Weaknesses: hat and hair are the same value in greyscale, so only the cuff separates them. Pivot moved to y55 because the launch toes clipped.

**B · Pokémon overworld (~2.2 heads, 44 px).** Gen 3/4 massing, head plus hat about 55%. Strengths: the boldest silhouette and wide-set eyes. Weaknesses: the scarf tails don't scale, so in SE/E a red line hangs down to the floor. Pivot y54.

**C · Semi-chibi (~3.4 heads, 64x72).** Strengths: clean legs, readable arms, and neck 2.3 keeps the scarf off the face. Weaknesses: the coat and arms make a boxy rectangle, and in N/NE the back scarf tail is an isolated red blob.

**D · Trainer (~4.1 heads, 64x80).** At head_r 6.5 with small eyes the face was dots. At 7.5 with large eyes it reads, but the figure only reaches about 4 heads. Strengths: elegant legs. Weaknesses: the tiny hat dome turns into candy stripes, the face is the weakest of the set, and there is dead cell space.

**E · Puffball (~2.6 heads, 45 px).** A bell body wider than the head, puffer coat, chunky scarf, 2x pom and 3.2 legs. Strengths: the most distinctive and cosiest read. Weaknesses: the back views stack into bands, and the red takes about 35% of the pixels.

## Recommendation
Hero: **B**. Fallback **A** if poses need more leg. Keep **E** as an alternate costume. Drop **D** at this scale.

## Feature requests
1. Scale scarf tail length with the torso, or add a `scarf_len` option.
2. Option to hide or tuck the back scarf tail.
3. Fewer hat shading bands when head_r < 8.
4. A `hair_volume` option. The bob flaps read small under the beanie.
5. board.py: uniform scale by default, and fix the missing `·`/`é` glyphs.
