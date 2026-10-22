# Game Director memo: JUMP

## Timing (12 frames, 720 ms)
- Anticipation: frames 1-2, 40 ms each, 80 ms.
- Takeoff: frame 3, 60 ms.
- Airtime: frames 4-8, 64/72/88/72/64 ms, 360 ms. The apex frame is held longest.
- Landing: frames 9-10, 50 ms each, 100 ms.
- Recovery: frames 11-12, 60 ms each, 120 ms.

Frame 1 shows on the tap and the character is airborne at 80 ms. Input is locked until 600 ms. Recovery can be cancelled into move or jump. Anticipation over 80 ms feels laggy on touch.

## Vertical offset: engine-driven (overrides the brief)
Frames are drawn in place, with the feet on the pivot. Each frame carries `z_px` (apex 22 px), and the engine applies it. The shadow stays on the ground and shrinks with z. Gameplay owns jump height, landing on different iso elevations and collision. Baked offsets fight all three. Baked versions are exported only for preview GIFs.

## Size
- Frame 64x64, pivot (32,56).
- Character 40 px tall, 46 px or less at peak stretch.
- Integer scaling only: 3x on phones, 4x on tablets, nearest-neighbour.

## Directions: 8, rendered, not mirrored
S, SE, E, NE, N, NW, W, SW. Asymmetric details (scarf, braids) stay correct.

## Sheet and metadata
- One PNG per animation: rows are directions in the order above, columns are frames. 12 x 8 cells = 768x512, no padding. The atlas packer adds 2 px extrusion.
- A JSON sidecar holds `frameSize`, `pivot`, `directions[]`, `paletteId` and `buildHash`.
- Per frame it holds `duration_ms`, `z_px`, `phase`, `cancelable` and `events[]`. The events are `takeoff` at frame 3 and `land` at frame 9, and they drive SFX, puff FX and shake.

## Acceptance criteria
1. Total 720 ms, airborne at 80 ms, input lock ends at 600 ms. All timings are read from the JSON.
2. In grounded frames the feet are exactly on (32,56) in all 8 directions, with 0 px drift.
3. Nothing clips the 64x64 cell, and the top margin is at least 2 px.
4. 32 colours or fewer, with 0 off-palette pixels and 0 orphan pixels.
5. The face reads clearly at 3x on a 6.1" phone in all facings. The director signs this off on device.
6. The silhouette reads in greyscale against the snow tile.
7. The same config gives a byte-identical PNG and JSON.
8. A playtest of 5 testers rates responsiveness 4/5 or higher.
