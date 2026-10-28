Restored session: Mon 26 Oct 2026 11:51:45 JST
(eval):1: can't change option: zle
(eval):1: can't change option: zle
I zoomed into the iso, exploded and pose columns for rows A, B and hybrid; the front, side and back columns I judged at sheet resolution.

| Row | On-model | Parts/seams | Rig | 48 px | Defects |
|---|---|---|---|---|---|
| **2mv single** | 6 | 2 | 2 | 5 | One fused mesh, so no exploded view or pose test is possible. The bow is a smeared blob that reads as a crumpled red cap at 48 px. Eye colour bleeds in the iso SE view. |
| **A split** | 6 | 5 | 6 | 5 | The bow is still the noisy 2mv blob. The arm cut shows fringed sleeve ends in the pose test. The torso's obi is jagged in iso SE, and the boots are separate tiny pieces (more joints, nothing gained). |
| **B per-part** | 4 | 7 | 7 | 3 | The head has holes: skin shows through the hair and bangs in front and iso SE. The torso is a thin vase shape with no shoulders. The skirt is a hard cone with an off-model straight hem. At 48 px the face is pixel noise. |
| **C PartCrafter** | 4 | 3 | 2 | 4 | The bow is a thin halo with no lobes. The sleeves are wisps, and in front and back the arms almost disappear. The parts follow materials, not joints, so the pose columns barely differ from the base. |
| **A+B hybrid v2** | 7 | 7 | 8 | 6 | The bow is a flat two-pill shape with no folds or tails, and in side view one lobe sticks up like an ear. The obi breaks into dark fragments in iso SE even though it should be a straight band. The B sleeves are too narrow next to the design's big kimono sleeves, and the B skirt cone is too stiff. |

**Adopt: A+B hybrid v2.** It's the only row that keeps A's on-model head and silhouette while getting clean, joint-aligned parts. Fix these next:

1. **Obi:** replace the vertex-colour band with a real cylinder shell slightly larger than the torso, so it reads as one solid dark band from every angle.
2. **Bow:** model each lobe as a cupped, pinched shape and add a centre knot plus two short tails. Then check the side and back views against the design's iso_N and iso_NE angles.
3. **Sleeves:** widen and lengthen the cuffs into a bell or trapezoid shape that hangs past the wrist, as in the design front view.
4. **Skirt:** lower and flare the hem a little, and check it doesn't cut into the legs during the stride.
5. **Eyes and face:** paint flat eye and skin IDs directly on the A head, and nudge the bangs up a few mm so the eyes read in iso SE at 48 px.
6. **48 px test:** re-run it after each fix; it's the real pass/fail check.

Saving session...completed.
