# Kickoff brief (draft by producer/lead)

## Ask
Animated pixel-art sprite sheets for a mobile game set in snowy mountains. Camera: top-down isometric (2:1 dimetric).
First asset: chibi female character, JUMP animation, warm winter clothing. Deliverables: sprite sheets + GIFs for
all isometric facing directions. Quality and cross-angle consistency are the top priorities. The pipeline must be
reproducible (same inputs -> same pixels) and iterable (feedback -> change -> rebuild quickly).

## Proposed system (for discussion)
"3D-driven pixel art": the character is a parametric 3D chibi model (ellipsoid primitives on a skeleton), animated with
keyframed poses + deterministic secondary-motion simulation (scarf tails, braids, hat pom-pom). A custom renderer
rasterizes it from the iso camera at native sprite resolution for each of 8 facings, then a pixel-art pass applies:
locked palette + banded toon shading, outer outline, selective internal outlines on depth breaks, hand-designed face
decals (eyes/mouth pixel patterns anchored to 3D head points so faces stay crisp), integer pixel snapping (no jitter),
ground shadow, snow-puff FX. One model + one animation => all 8 directions are consistent by construction.

A browser pixel editor (palette-locked pencil/erase/fill/picker, onion skin, playback, 8-direction view) lets artists
paint per-frame OVERRIDE layers on top of the generated base. Overrides are stored separately and re-applied on every
rebuild, so hand polish survives iteration. Automated QA: palette compliance, baseline/pivot alignment across
directions, bounds clipping, orphan pixels. Every build is versioned with its config snapshot.

## Initial parameters (open for debate)
- 8 directions: S, SE, E, NE, N, NW, W, SW (rendered, not mirrored, to allow asymmetric details)
- Frame 64x80 px, pivot at feet (32,72). Character ~42px tall standing. Jump bakes vertical offset into frames,
  with metadata giving per-frame height so an engine can also use an "in-place" variant.
- ~12 frames, variable per-frame durations (~12 fps feel)
- Palette <= 32 colors, warm character against cool snow environment.
- Outfit idea: cream knit beanie with red pom-pom, mustard long scarf + mittens, cranberry puffy parka with hood,
  navy pants, brown fur-trimmed boots, chestnut hair with two short braids.
