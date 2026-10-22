# r9 Designer B: S3 and S4

Both pass QA on `jump_v2` and `jump_sc` with `chain_penetrations` at 0.

## S3_high_pony (8 builds)
**Intent:** sporty-cute. A long high ponytail is the motion element.
- **Pony:** 8 segments x 3.5, widths 4.2 to 5.0 to 1.0, anchored at the crown. `rest_dir` [0.3,-1,-0.3] keeps it on her left in every view, and stiffness 120 makes it swing hard.
- **Accessories:** teal scrunchie, teal earmuffs, and a teal side clip (enlarged).
- **Belt:** enlarged a little.

**Strengths:** the best E/W/NE/SW silhouettes and a clear lagging arc.
**Weaknesses:** the front silhouette is only a topknot. The earmuff band is a teal stripe in N, and the tail merges with the hair in NE.

## S4_halfup_bow (5 builds)
**Intent:** a sweet princess with a big back bow, hime bangs and waist-length hair.
- **Bow:** loops [3.9,2.7,1.6] at ±24° with two added tails. The knot and tails use `hatcuff`, remapped to teal_0, so a dark centre splits the loops.
- **Hair and fringe:** `straight` fringe, longer sidelocks, and wider locks (4.6 to 2.6).

**Strengths:** the bow reads in all 8 directions and at distance, and the hair silhouette is large.
**Weaknesses:** N/NE are one brown mass that hides the curves, and coat shows between the locks mid-jump. In S the bow loops peek over the crown and can look like ears.

## Generator limits hit
1. Despeckle (`max_island=3`) silently deletes small accessories. The default `clip` never rendered until enlarged.
2. The default clip sits inside the fringe.
3. Ribbon parts can't be coloured individually. Workaround: the unused `hatcuff` material.
4. The `pony` default is short with a high anchor, so `hair_len` doesn't really apply to it.
5. The earmuff band is a full ring, so it shows on the back of the head.
