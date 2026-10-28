# r5 Panel: Art Director

## 1. Proportions
**Pick: B.** Head plus beanie is about 55% of the height, and the hat/bob mass is wider than the shoulders, so it reads as one Gen 3/4 shape from every direction. **Runner-up: A**, which has more leg but a weaker head read. C and D spend pixels the brief doesn't need, and E works as a costume.

## 2. Outfit and colourway
**Pick: O1 charcoal/red on B (BO1).** It has the widest value spread. Red is the only hue (hat, scarf, mittens), the cream pom and cuff mark the head, and espresso hair stays separate from the red. **Runner-up: O2 navy/red on A.** On B the navy hat merges with the coat, and from the back auburn hair is a large orange mass. Use `hair_color: "espresso"` if O2 is chosen.

## 3. Resolution
**Vote: R2 (~32 px, 48x48).** Every design element survives at 2 px or wider: pom, cuff, 1x2 eyes with a catchlight, bob flaps, mittens and boot cuffs. It uses 13 colours, almost no filler. R3 adds flat coat areas of about 80 px but no new information. R1 breaks the eyes and mittens and drops the scarf to 1 px. The cost is about 2 hand-fixed face pixels per SE/E key. **Fallback: R3.** Next step: build BO1 at `ppu 0.75`, frame `[48,48]`.

## 4. Top 6 pixel issues (BO1, 64x64 coordinates)
1. **Hat highlight covered about a third of the dome** (x22-28, y19-26). **Applied:** `material_bands.hat [-0.45,0.94]`, which leaves a 2-3 px band.
2. **Hair shine split the head in half from N.** **Applied:** `material_bands.hair [-0.35,0.55]`.
3. **Legs disappear.** Only 1-2 px of pants show above the boots. **Fix:** `proportions.leg 4.6→5.4`, then re-check the pivot.
4. **Red side stripes in SE/E** at x21-24 and x38-40, y42-50, from the scarf tail and mitten. **Fix:** `scarf_tails: 1`, `scarf_len: 2.0`.
5. **Hem trim makes a lilac band** (42 px of mauve at y47-50 in SE f6) plus cream specks at (28-33,48) in S f12. **Fix:** `hem_trim: false`, keep `sleeve_cuffs`.
6. **Cuff specks and a nape gap.** Mauve specks at (25-26,28) and (37-38,28) in S f12, and a skin strip at (27-35,38) in N f6. **Fix:** a pixel override that sets the specks to `oat_1` (idx 12) and the strip to `hair_1` (idx 2), or lower the scarf collar at the back.

## 5. Palette changes (applied)
- `red_2` changed from #F7845E to **#F06A58**. The old salmon had nearly the same value as `skin_1` and the copper hair.
- `material_bands`: `hat [-0.45,0.94]`, `hatcuff [-0.5]`, `hair [-0.35,0.55]`.
- I regenerated the `cw_*` files with `make_r3_palettes.py` and rebuilt all 21 variants. The only QA errors are the existing height-delta ones. `archive/snowpeak/boards_r04_r10/*` is stale and needs regenerating.
