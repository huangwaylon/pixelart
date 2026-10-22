# QA report — FAIL

## Errors (8)
- S f3: margin < 2px, bbox (20, 14, 43, 62)
- SE f3: margin < 2px, bbox (20, 14, 42, 62)
- E f3: margin < 2px, bbox (20, 14, 41, 62)
- NE f3: margin < 2px, bbox (20, 13, 43, 62)
- W f3: margin < 2px, bbox (22, 14, 43, 62)
- SW f3: margin < 2px, bbox (20, 14, 43, 62)
- silhouette height differs by 3px across directions at frame 4
- 102 orphan pixels (limit 0); worst [('S_3', 4), ('S_12', 4), ('NE_11', 4)]

## Warnings (0)
- none

## Metrics
- **foot_slide_px**: 0.0
- **max_height_delta_px**: 3
- **standing_height_px**: {'S': 46, 'SE': 47, 'E': 47, 'NE': 46, 'N': 45, 'NW': 46, 'W': 46, 'SW': 47}
- **orphan_pixels_total**: 102
- **orphan_pixels_worst**: [('S_3', 4), ('S_12', 4), ('NE_11', 4), ('N_10', 4), ('NW_7', 4)]
- **colours_used**: 25
- **overrides**: 0
- **total_ms**: 770
- **airborne_at_ms**: 110
