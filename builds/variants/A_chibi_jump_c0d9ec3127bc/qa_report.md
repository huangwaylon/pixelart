# QA report — FAIL

## Errors (8)
- S f3: margin < 2px, bbox (19, 13, 44, 62)
- SE f3: margin < 2px, bbox (20, 13, 42, 62)
- E f3: margin < 2px, bbox (20, 13, 41, 62)
- NE f3: margin < 2px, bbox (20, 13, 42, 62)
- W f3: margin < 2px, bbox (22, 13, 43, 62)
- SW f3: margin < 2px, bbox (21, 13, 43, 62)
- silhouette height differs by 3px across directions at frame 9
- 72 orphan pixels (limit 0); worst [('S_7', 5), ('NW_10', 4), ('NW_3', 3)]

## Warnings (0)
- none

## Metrics
- **foot_slide_px**: 0.0
- **max_height_delta_px**: 3
- **standing_height_px**: {'S': 44, 'SE': 45, 'E': 44, 'NE': 42, 'N': 42, 'NW': 42, 'W': 44, 'SW': 45}
- **orphan_pixels_total**: 72
- **orphan_pixels_worst**: [('S_7', 5), ('NW_10', 4), ('NW_3', 3), ('SE_9', 2), ('SE_10', 2)]
- **colours_used**: 17
- **overrides**: 0
- **total_ms**: 770
- **airborne_at_ms**: 110
