# r6 Acceptance: Game Director (JUMP, build b07b36a846d4)

**ACCEPT WITH NOTES.** Integration can start. Two art items must close before ship.

| Criterion | Result |
|---|---|
| 576x384 sheet (48x48, 12x8), no empty cells | PASS |
| 770 ms total, airborne 110, lock 590 = f10 start | PASS |
| takeoff f3, land f9 | PASS |
| z arc to apex 15 at f6 | PASS |
| Contact row 42 in all dirs | PASS |
| Margin, orphans, foot slide | PASS |
| Shadow/fx strips match frames and pivot | PASS |
| Greyscale on snow | PASS |
| Height gate 3 px | **CONFIRMED** (crouch tilt only; standing 29 px everywhere) |
| Overrides | **26/44 stale** |

Script `/tmp/gd_accept/sanity.py`: 16/16 pass.

## Integration
- `jump_sheet.json` is authoritative. DECISIONS v1 still says 64x64.
- Put pivot (24,41) on the ground point.
- Draw shadow, then fxBack, character, fxFront. Layers share the frame index and pivot across all directions.
- Offset only the character by `-z_px`. It rises 6 px above its cell, so cull and sort on 48x63 bounds.
- Lock input for 590 ms. Input during f10-f12 cancels the jump.
- Fire events on frame entry.

## Before ship
1. Resolve all 26 stale overrides and re-run QA. Make stale overrides a release error.
2. Shadow: widen from 10 px to 14-16 px and shrink to ~65% at apex. It currently goes from 10 to 8 px.
3. Update DECISIONS: 48x48, pivot (24,41), apex 15, gate 3 px.
