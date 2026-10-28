# Pixelize bake-off: results (2026-10-27)

**Recommendation: method E2 (k-centroid downscale + programmatic face pass + cleanup, palette-locked), at a 96 px figure (128 px cell).**
Runner-up: the same method at 80 px (112 px cell). Drop 64 and 48.
Re-runnable: `v2/pixelize/make_top.sh top1|top2 [views]` (a single view is `pz.py EC0 <VIEW> 96 --pal v2/pixelize/palette.json [--src new.png]`).

## Ranking (bake-off on SE + front at 64/80/96, board.png)
| # | method | Argon r1 / r2 | Opus r1 / r2 | notes |
|---|---|---|---|---|
| 1 | **E2: k-centroid + face pass** (`EC0`) | 7.0 / 7.0 (#1, #1) | 7.5 / 6.5 (#1, #3) | Cleanest flat clusters, best colours, and the best face SSIM (.85-.86). Both critics put E2@96 in their top 3 both rounds. |
| 2 | C: k-centroid (Astropulse-style, own implementation) | 6.5 / 6.5 | 6.5 / 6.0 | Best global fidelity (ssim_b .96), but the front-view eyes collapse to slits at 80 px. |
| 3 | E1: PixelOE + face pass (`EB`) | 6.0 / 5.5 | 5.5 / 6.5 | Crisp outlines, but hair speckle remains (hair IoU .41-.55). |
| 4 | B: PixelOE (contrast + outline expansion, then the locked palette) | 3.5 / 4.5 | 4.5 / **7.0 (#1 in r2)** | Best line_f (.95-.97) and stark, readable eyes, but the most orphans (54-100) and dark hair speckle. The critics split on it. |
| 5 | A: current palette-locked majority (v2/final ds.py) | 4.5 / 5.0 | 6.0 / 4.5 | Tidy, but eyes become K/W blocks and there's no mouth. Face SSIM is the lowest (.72-.77). |
| 6 | D: Gemini redraw + grid snap | 5.0 / 3.5 | 5.0 / 5.0 | Gemini ignores the requested size: it draws HD pixel art 170-330 px tall (grid 3-6 px). The redraw drifts off-model (legs, bangs, proportions; sil .85-.97, dE 16-19). It's only useful as a face reference. |

Sizes: both critics, both rounds, ranked **96 > 80 >> 64** ("at 64 the face can't hold eyes"). Top-sheet check (crit/top_argon.txt): 96 px sheet S6 SE6 E7 NE7 N7; 80 px sheet S5 SE5 E6 NE6 N7. "80 px loses essential eye definition in S/SE." Colours are consistent across all views in both.

## Scripted metrics (mean of SE + front, locked 16 palette; metrics_final.txt/json)
ssim_b = SSIM on L after a 1 px blur, against the illustration area-downsampled to the sprite grid. dE = CIEDE2000. sil/bloat = silhouette IoU and area ratio. iou_* = per-material IoU. line_f = outline F1 within 1 px. orph = orphan pixels. face_ssim / face_score = face-box SSIM plus eye/mouth/spacing terms. eye_f1 turned out too lenient, so I don't rely on it.

| method | size | ssim_b | dE | sil | bloat | iou_hair | iou_red | iou_skin | line_f | orph | face_ssim | face_score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 64 | 0.93 | 11.6 | 0.99 | 1.01 | 0.72 | 0.75 | 0.54 | 0.86 | 0 | 0.72 | 0.84 |
| A | 80 | 0.94 | 10.1 | 0.98 | 1.01 | 0.74 | 0.80 | 0.64 | 0.85 | 1 | 0.75 | 0.77 |
| A | 96 | 0.94 | 9.6 | 0.99 | 1.01 | 0.78 | 0.82 | 0.69 | 0.86 | 0 | 0.77 | 0.83 |
| B | 64 | 0.94 | 12.8 | 0.97 | 0.99 | 0.44 | 0.68 | 0.67 | 0.95 | 54 | 0.66 | 0.75 |
| B | 80 | 0.95 | 10.9 | 0.97 | 1.00 | 0.53 | 0.74 | 0.72 | 0.95 | 72 | 0.73 | 0.82 |
| B | 96 | 0.95 | 10.2 | 0.98 | 1.00 | 0.57 | 0.78 | 0.73 | 0.97 | 100 | 0.75 | 0.83 |
| C0 | 64 | 0.96 | 10.9 | 0.97 | 0.97 | 0.70 | 0.71 | 0.72 | 0.89 | 36 | 0.81 | 0.76 |
| C0 | 80 | 0.96 | 9.3 | 0.98 | 0.98 | 0.75 | 0.77 | 0.77 | 0.90 | 48 | 0.84 | 0.86 |
| C0 | 96 | 0.96 | 8.9 | 0.97 | 0.97 | 0.76 | 0.79 | 0.80 | 0.90 | 64 | 0.83 | 0.87 |
| D | 64 | 0.88 | 16.1 | 0.94 | 1.01 | 0.64 | 0.69 | 0.47 | 0.91 | 40 | 0.74 | 0.77 |
| D | 80 | 0.85 | 16.7 | 0.92 | 1.02 | 0.65 | 0.71 | 0.44 | 0.95 | 50 | 0.73 | 0.81 |
| D | 96 | 0.79 | 18.5 | 0.91 | 1.03 | 0.58 | 0.65 | 0.42 | 0.93 | 56 | 0.59 | 0.78 |
| EB | 64 | 0.93 | 12.5 | 0.97 | 1.00 | 0.41 | 0.69 | 0.66 | 0.94 | 21 | 0.80 | 0.82 |
| EB | 80 | 0.94 | 10.8 | 0.97 | 1.00 | 0.51 | 0.73 | 0.70 | 0.94 | 26 | 0.82 | 0.83 |
| EB | 96 | 0.93 | 10.1 | 0.98 | 1.00 | 0.55 | 0.77 | 0.71 | 0.95 | 39 | 0.82 | 0.85 |
| EC0 | 64 | 0.95 | 11.0 | 0.97 | 0.97 | 0.68 | 0.70 | 0.67 | 0.88 | 20 | 0.85 | 0.83 |
| EC0 | 80 | 0.95 | 9.5 | 0.98 | 0.98 | 0.73 | 0.75 | 0.72 | 0.88 | 22 | 0.85 | 0.86 |
| EC0 | 96 | 0.96 | 9.0 | 0.97 | 0.98 | 0.75 | 0.78 | 0.74 | 0.89 | 32 | 0.86 | 0.86 |

Summary: k-centroid (C0/EC0) has the best ssim_b and dE at every size. EC0 has the best face_ssim and cuts orphans by about 2x compared with C0. PixelOE gives the best outlines but the noisiest hair. Fidelity rises with size: dE goes 11.0 -> 9.5 -> 9.0 for EC0.

## Findings
- **Why the old sprites didn't look like the art:** palette snapping plus majority voting erased the faces. A plain box-average of the illustration (no palette) still shows irises at 80-96 px, but every palette-locked method turned the eyes into dark slits. The E face pass fixes this per cell inside the face hull: the lash becomes K (only the top dark row), the iris becomes h/g/L (nearest in Lab), sclera becomes W (cells ≥45% white), one catchlight per eye, and the mouth is drawn on the strongest lower-face row. Size was the other half of the problem: 48 px is far too small for this art.
- **Side profile "fat":** no automatic method bloats the figure. In the E view the area ratio is 0.97-1.00 for every method, PixelOE included (1.00), and torso/thigh widths are at or below the illustration. The old 48 px hand-edited master E has 1.18x the area of its old illustration (prev/iso_E; thigh 8 vs 7.1 px), and that old illustration was itself wider. The hair strand's new slim iso_E plus automatic conversion fixes it (top1 E: bloat 0.98).
- **Palette:** a 24-colour version (palette24.json, 8 error-driven extras) gave **no gain**: same or lower SSIM, lower hair IoU, more orphans. The socks (legs a) are a neutral near-black (#2b2927, dE 7-8 from h/H, previously read as outline K), so I added a socks ramp **D #2b2927 / d #373230**, giving **v2/pixelize/palette.json (18 colours = locked 16 + socks)**. With it, dE on front@96 goes 9.05 -> 8.73 and socks separate from the outline.
- **Pokemon reference:** official trainer battle sprites are 62-67 px from crown to sole (Hilda 67, Rosa 64, Lyra/Dawn 62; v2/prop/template.json) on 80x80 (Gen 4) or 96x96 (Gen 5) canvases. 80 px is at the top of that range. 96 px goes beyond it, which this large-eyed anime head needs.

## Trade-off: sprite size vs animation cost
Opaque pixels per frame (SE): 48 px master ~650, 64 px ~880, **80 px ~1400, 96 px ~2000** (S: 1510 / 2160). A 96 px figure has about 1.4x the pixels of 80 px and about 3x the old 48 px, for every frame of every animation, and per-frame hand cleanup scales the same way. 80 px is the budget choice: it reads, but the S/SE faces are weaker. 96 px is the fidelity choice.

## Outputs
- board.png (1307x1252) + board_thumb.png: rows = methods; columns = illustration | 64 | 80 | 96; each cell = SE + front figure + head close-ups.
- top1/ (E2@96, 128 cell) and top2/ (E2@80, 112 cell): EC0_<V>_<H>.{txt,png,json} for S, SE, E, NE, N, plus sheet.png and sheet_thumb.png (illustration | 4x | 1x). Built on the FINAL SET (legs a) with palette.json. metrics_top.txt: ssim_b .953-.968, dE 7.3-9.3.
- tools/: pz.py (methods A, B, C0, C, D, F, E*), pzlib.py, metrics.py, gemsnap.py, board.py, faces.py, sheet.py, mkpal24.py, strip.py. Critiques are in crit/.
- Rejected variants: C with line priority (blobby eyes), palette24, unconstrained snap.

## Remaining defects (top1) / next step
S/SE eyes are still a bit muddy or soft, outlines are jagged on the sleeves and ribbon tails, hands are indistinct, and the thin ribbon tail breaks into dashes. These are automatic outputs, not finished masters. Next step: a small head-only polish (about 24x24 px per view, by hand or an Opus pass) and an outline/jaggy cleanup on top1. Everything else stays re-runnable.
