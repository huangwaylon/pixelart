# Art Director Memo: Character & Style Lock

## Character
- **2.5 heads.** At 42px: head + beanie 17px, body 25px.
- **Silhouette hooks at 42px:** red pom-pom on top (4x4px), braids jutting sideways, scarf tails trailing 6-8px (the main motion read), parka wider than the head, chunky fur-cuffed boots.
- **Outfit:** as the brief says. Ribbed cream beanie (ribs only on the 2px rim), hood bunched at the neck, no zipper line.
- **Personality:** plucky and over-committed. Arms go fully up at the apex.

## Palette (29 + 3 reserve = 32), dark to light
- Outline: `#241628`
- Skin: `#B0606A` `#E8A07C` `#F8C8A0` `#FFE6CC`
- Hair: `#4A2430` `#7A3E2E` `#A8603A`
- Parka/pom/blush: `#4E1A3A` `#8A2440` `#C23A44` `#EE7A5E`
- Mustard: `#7A4A2A` `#C08A2A` `#E8B83A` `#FDE27A`
- Cream (beanie, fur): `#9A8AA0` `#D8CBB8` `#F4EAD2`
- Navy: `#1E1E3E` `#2E3462` `#46528A`
- Boots: `#3A2228` `#6A3E2E` `#94603E`
- Snow/FX: `#6A7AA8` `#A8C0E0` `#DFEAF6` `#FFFFFF`
- Environment reserve: `#3E4A6E` `#6E6A8A` `#2A4A4A`

Shadows lean purple and highlights lean warm. Warm saturated character on cool snow. Cream sits next to snow, so the outline and its yellow lean keep it apart. Ground shadow is `#A8C0E0`.

## Lighting
**Screen-fixed key light from the upper left**, computed in camera space, so all 8 facings shade the same. Ground shadow is a flat ellipse straight below her, 14x5px standing and 10x4px at the apex. Never cast it to one side.

## Outlines
- Outer edge: 1px `#241628`, always.
- Inner lines only at depth breaks (arm over torso, scarf over parka, braid over shoulder), drawn in the front material's darkest tone.
- No lines inside the face.

## Face (S/SE/SW/E/W)
- Eyes are 1x2px `#241628`, no whites, 3px apart, 9px below the beanie top. One blush pixel under each eye.
- **Neutral:** no mouth.
- **Determined (crouch):** 1x1 eyes, 2px flat mouth.
- **Joyful (launch to apex):** ^ ^ arcs, 2x2 open mouth in `#8A2440`.
- **Impact squint (land):** `>` `<`, 1px mouth.
- **Recovery:** neutral plus a 1px smile corner.
- Back facings have no face. Braids and the beanie seam carry them.

## Avoid
- No pillow shading. Shade from the light, never from the outline inward.
- No banding. Shadow edges must not follow the outline contour.
- No orphan pixels unless deliberate, like a sparkle.
- No jitter. Face decals and the pivot are integer-locked, and the head must not do unintended 1px wobbles.
- No anti-aliasing against transparency, no dithering on the character, no jaggies. Pixel runs go 1-2-3, never 1-3-1.
- Snow puffs use the snow ramp only.
