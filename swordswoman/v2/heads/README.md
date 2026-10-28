# v2/heads: shared ROUND CHIBI SKULL head set (48px character)
Built by the anim_redraw strand with Opus (be_system) as pixel artist, 5 rounds, critiqued by Argon + Opus each round
(crit/r1..r5_*.txt; scores r1 5.5/4, r2 6/6, r3 5.5/5, r4 5/6, r5 6/6, r6 5/6 = FINAL: r5 + bangs shelf lowered onto the lash line as in the old master). Backups: r1/..r5/, r5b_pre/ (r5 before the bangs fix).
Design refs: v2/design/turnD/iso_SE.png, iso_E.png, DESIGN_SPEC.md. Palette: v2/pixel/palette.json chars (cm.py compatible).

## Convention (same as anim_cut parts/se/head*.txt)
- Char-maps readable by v2/anim_cut/tools/cm.py: rows of palette chars, '.' transparent, meta '; pivot X Y', '; anchor NAME X Y'.
- `head_<variant>.txt` = hair + face (no bun, no bow). **pivot = neck point under the chin** (attach to torso.neck).
  Anchors: `bow` = where the bow part's pivot goes (crown top), `bun` = where the bun part's pivot goes (top-back; may be negative/outside the part).
- `bun.txt` pivot = bun centre, drawn BEHIND the head (z below head). `bow.txt` pivot = bottom centre of the knot, drawn IN FRONT.
- `*_squash.txt` bow/bun go with head_squash (preview picks `<part>_<variant>.txt` if present, else `<part>.txt`).
- Rig example (anim_cut stand_SE.json style): "head":{"part":"head_neutral","at":"torso.neck"}, "bun":{"part":"bun","at":"head.bun","z":0}, "bow":{"part":"bow","at":"head.bow","z":8}.

## Variants
- SE (front 3/4, facing screen lower-right): neutral, lean (whole head 1px forward/down; use for run/dash/slash impact), lookup (eyes+brows+bangs up 1px; jump launch/apex), squash (wider/shorter; landings), blink.
- E (true profile facing screen right): neutral, lean, lookup, squash. Mirror for W.

## Files
| file | size | meta |
|---|---|---|
| `e/bow.txt` | 13x9 | pivot 6 8 |
| `e/bun.txt` | 8x7 | pivot 4 4 |
| `e/head_lean.txt` | 23x23 | pivot 15 21; anchor bow 11 2; anchor bun 4 0 |
| `e/head_lookup.txt` | 23x21 | pivot 16 21; anchor bow 10 2; anchor bun 3 0 |
| `e/head_neutral.txt` | 23x22 | pivot 16 21; anchor bow 10 2; anchor bun 3 0 |
| `e/head_squash.txt` | 25x20 | pivot 18 19; anchor bow 11 3; anchor bun 4 1 |
| `se/bow.txt` | 17x8 | pivot 8 7 |
| `se/bun.txt` | 7x7 | pivot 3 3 |
| `se/head_blink.txt` | 24x23 | pivot 14 20; anchor bow 11 2; anchor bun 2 2 |
| `se/head_lean.txt` | 24x24 | pivot 13 20; anchor bow 12 2; anchor bun 3 2 |
| `se/head_lookup.txt` | 24x22 | pivot 14 20; anchor bow 11 2; anchor bun 2 2 |
| `se/head_neutral.txt` | 24x23 | pivot 14 20; anchor bow 11 2; anchor bun 2 2 |
| `se/head_squash.txt` | 26x21 | pivot 15 18; anchor bow 12 3; anchor bun 3 3 |

## Previews
- `png/<view>_<variant>_1x.png`, `_6x.png`: composed head+bun+bow; `png/<view>_<variant>_full.txt`: composed char-map (pivot = head pivot, for direct stamping).
- `png/sheet.png`: all variants 6x + 1x strip. Regenerate: `.venv/bin/python v2/heads/tools/preview.py`.

## Known critic notes (r5)
- r6 Argon 5 / Opus 6: dome, temple bulge and soft chin fixed (no more helmet); remaining: SE reads slightly ball-like / face window, E bow shape still debated. Further tweaks should keep the pivots/anchors.
