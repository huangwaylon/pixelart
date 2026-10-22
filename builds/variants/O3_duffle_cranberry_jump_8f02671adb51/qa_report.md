# QA report — FAIL

## Errors (8)
- S f3: margin < 2px, bbox (19, 12, 44, 62)
- SE f3: margin < 2px, bbox (20, 12, 42, 62)
- E f3: margin < 2px, bbox (19, 12, 41, 62)
- NE f3: margin < 2px, bbox (20, 13, 42, 62)
- W f3: margin < 2px, bbox (22, 12, 44, 62)
- SW f3: margin < 2px, bbox (21, 12, 43, 62)
- silhouette height differs by 3px across directions at frame 3
- 3 orphan pixels (limit 0); worst [('S_7', 1), ('S_11', 1), ('SW_7', 1)]

## Warnings (0)
- none

## Metrics
- **foot_slide_px**: 0.0
- **max_height_delta_px**: 3
- **standing_height_px**: {'S': 45, 'SE': 46, 'E': 46, 'NE': 45, 'N': 45, 'NW': 45, 'W': 46, 'SW': 46}
- **orphan_pixels_total**: 3
- **orphan_pixels_worst**: [('S_7', 1), ('S_11', 1), ('SW_7', 1)]
- **colours_used**: 17
- **overrides**: 0
- **total_ms**: 770
- **airborne_at_ms**: 110
