# r10 Outline style — Game Director

Script: `/tmp/gd_ol/measure.py` (8 dirs x 14 frames, S4 jump_sc). dL* = mean L* gap across the silhouette edge; melt = edge px < 1.5:1 WCAG; IoU = silhouette rebuilt from px >= 1.5:1 at 1x; flip = edge px that change colour frame to frame (shimmer).

| mode | snow DFEAF6 dL*/melt/IoU | white | rock 3E4A6E | night 2A2E3A | flip |
|---|---|---|---|---|---|
| none | 47 / 15% / .86 | 55 / 0% / 1.0 | 17 / **50%** / .57 | 26 / 15% / .95 | 12.2% |
| dark | **82 / 0% / 1.0** | 90 / 0% / 1.0 | 22 / 0% / 1.0 | 9 / **100%** / .76 | **0%** |
| selout | 67 / 5% / .92 | 75 / 0% / 1.0 | 19 / 28% / .67 | 15 / 69% / .83 | 10.2% |
| open | 63 / 10% / .89 | 71 / 0% / 1.0 | 20 / 25% / .69 | 19 / 53% / .84 | 9.4% |
| colored | 54 / 7% / .91 | 62 / 0% / 1.0 | 16 / **59%** / .54 | 20 / 44% / .88 | 13.7% |

Engine swap of the outline index (#241628) on dark tiles, dark mode: rock goes to dL* 32 with #8C9AC0 (53 with #C8D4E8), night goes to 45/66, 0% melt, IoU 1.0. On selout and open the swap does nothing on rock (28% / 25% melt stays) because those edges are coloured, not the outline index.

**Recommendation: use a connected dark outer outline.** Our 48x64 sprite sits on a busy snow field on a phone screen, and every outline-free mode melts on snow (5-15%) and badly on rock (25-59%). Dark is the only mode that is perfect on snow and white. Its edge colour also never changes between frames (0% flip), so the outline doesn't shimmer as she moves. The 1x distance tests agree: on the slate band, none, colored and selout lose the hair and boots into the ground.

**Does the swap fix dark ground? Yes, if we change one thing first.** 9% of the outline-index pixels sit inside the silhouette (inner lines and features). So the outer outline needs its own palette index, split from the interior line colour, so the swap only lights up the rim. Then: on night tiles, swap to #8C9AC0 (a soft rim with no halo). On rock it's optional, because the dark outline already passes at 1.9:1, but the swap helps.
