# QA report — FAIL

## Errors (4)
- S f2: margin < 2px, bbox (18, 21, 45, 62)
- SW f2: margin < 2px, bbox (16, 21, 46, 63)
- silhouette height differs by 4px across directions at frame 2
- 5 orphan pixels (limit 0); worst [('SW_9', 2), ('S_7', 1), ('S_11', 1)]

## Warnings (0)
- none

## Metrics
- **foot_slide_px**: 0.0
- **max_height_delta_px**: 4
- **standing_height_px**: {'S': 43, 'SE': 44, 'E': 45, 'NE': 44, 'N': 44, 'NW': 44, 'W': 45, 'SW': 44}
- **orphan_pixels_total**: 5
- **orphan_pixels_worst**: [('SW_9', 2), ('S_7', 1), ('S_11', 1), ('SW_11', 1)]
- **colours_used**: 17
- **overrides**: 0
- **total_ms**: 770
- **airborne_at_ms**: 110
