# v2 schemas (exploration phase)

## Palette / colourway file: data/palettes/<name>.json
```json
{
  "name": "frost_v2_cranberry",
  "colors": [{"name": "outline", "hex": "#241628"}, ...],   // master palette, <= 32 entries, shared by ALL colourways
  "ramps": {                                                // semantic material -> colour names, dark -> light, 2 or 3 entries
    "skin": [...], "hair": [...], "hat": [...], "hatcuff": [...], "pom": [...],
    "coat": [...], "coat_trim": [...], "scarf": [...], "mitten": [...],
    "pants": [...], "boots": [...], "boot_cuff": [...], "snow": [...]   // snow = FX puffs (3-4 tones)
  },
  "bands": {"2": [-0.10], "3": [-0.25, 0.72], "4": [-0.3, 0.4, 0.85]},   // N.L thresholds; ~70% of a part should be base tone
  "special": {"outline": "...", "eye": "...", "catchlight": "...", "mouth": "...", "blush": "...", "ground_shadow": "..."},
  "accents": ["..."],          // documentation: which colours are the accent(s)
  "notes": "rationale"
}
```
Rules: one master palette (cohesive), colourways only re-map materials to ramps. 2-3 tones per material
(skin & boots 2 ok). 1-2 saturated accents per colourway, everything else muted. Character <= 16 colours per frame.
Must read against snow #DFEAF6 / #FFFFFF in greyscale.

## Variant spec: data/variants/<name>.json  (consumed by pipeline/chargen.py)
See pipeline/chargen.py docstring for every parameter.
