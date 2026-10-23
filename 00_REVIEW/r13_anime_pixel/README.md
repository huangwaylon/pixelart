# r13 — Hand-pixelled anime illustrations (restart)

Every pixel is placed by an artist in a text grid (`art/hand/S4/**/*.pix`, tool `pipeline/pixgrid.py`).
No 3D model and no vectors are involved. The face direction is candidate **C**, the Japanese ドット絵 one ([face_tests/compare_x4.png](face_tests/compare_x4.png)).

## Status
| Deliverable | Where to look | Status |
|---|---|---|
| Dialogue busts, 96x96, 10 expressions | **[bust/bust_sheet_x3.png](bust/bust_sheet_x3.png)** · [actual size](bust/bust_sheet_x1.png) · engine [bust_spritesheet.png](bust/bust_spritesheet.png) + `.json` | **APPROVED** by AD (5 review rounds) |
| Full-body turnaround, 96x160, front / 3/4 / side / back | **[turnaround/turnaround_x3.png](turnaround/turnaround_x3.png)** · [silhouettes](turnaround/silhouette_check_x2.png) | **APPROVED** by AD (6 rounds). The 3/4 bow tip is being refined. |
| Full-body head + 20 expressions (front, 3/4) | [head_small/heads_x4.png](head_small/heads_x4.png) · [expressions_x4.png](head_small/expressions_x4.png) | APPROVED. Tilted-head variants are in progress. |
| Cut-scene poses, 96x160, 8 poses | [poses/poses_lineup_x3.png](poses/poses_lineup_x3.png) | In review. hands_on_hips and shiver are approved. Head tilts and the B-set fixes are in progress. |

## Team definition docs
- Design bible: [docs/review/r13_design_bible.md](../../docs/review/r13_design_bible.md)
- Style guide: [docs/review/r13_style_guide.md](../../docs/review/r13_style_guide.md)
- Reviews: `docs/review/r13_review*_{bust,turnaround,poses}.md`
