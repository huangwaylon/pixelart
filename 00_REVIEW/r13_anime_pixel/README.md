# r13 — Hand-pixelled anime illustrations (restart)

Every pixel is placed by an artist in a text grid (`art/hand/S4/**/*.pix`, tool `pipeline/pixgrid.py`).
No 3D model and no vectors are involved.

## 1. Face direction: 3 candidates. Pick one (team recommends C).
**[face_tests/compare_x4.png](face_tests/compare_x4.png)** · [compare_x1.png](face_tests/compare_x1.png) (actual size)

All three are 80x80 bust tests in 3/4 view. They share the same hair, bow and scarf; only the face idiom changes:

| | Idiom | Notes |
|---|---|---|
| A | GBA dialogue portrait (Fire Emblem / Golden Sun) | Dark outline everywhere, compact 8x8 eyes. Sturdy, but reads older and plainer. |
| B | DS-era moe | Coloured lines, 10x10 eyes with 2 catchlights, rounder face. Softest, but muddy at 1x. |
| **C** | Japanese ドット絵 | Dark outer line with coloured inner lines. Gently drooping lashes, red-pink blush and a tiny ":3" mouth. Reads clearly at 1x. |

## 2. Team definition docs
- Design bible: [docs/review/r13_design_bible.md](../../docs/review/r13_design_bible.md). Covers proportions (5.4 heads), hair shapes, bow, outfit, the 10 expressions and the 8 poses.
- Style guide: [docs/review/r13_style_guide.md](../../docs/review/r13_style_guide.md). Covers canvas sizes, eye construction, line and shading rules, and the palette.
- Full-body blocking: [design/blocking_front_x4.png](design/blocking_front_x4.png). Eye/brow study: [style/](style/).
