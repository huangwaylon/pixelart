# QA report — FAIL

## Errors (1)
- SW f3: sprite touches cell edge (21, 14, 43, 63)

## Warnings (2)
- silhouette height differs by 6px across directions at frame 5
- 1010 orphan pixels total (target ~0, see worst list)

## Metrics
- **foot_slide_px**: 0.417
- **max_height_delta_px**: 6
- **standing_height_px**: {'S': 45, 'SE': 44, 'E': 43, 'NE': 42, 'N': 41, 'NW': 42, 'W': 43, 'SW': 44}
- **orphan_pixels_total**: 1010
- **orphan_pixels_worst**: [('SW_7', 22), ('NW_7', 21), ('N_9', 19), ('NW_4', 17), ('S_4', 16)]
- **colours_used**: 24
- **overrides**: 0
- **total_ms**: 850
- **airborne_at_ms**: 130
