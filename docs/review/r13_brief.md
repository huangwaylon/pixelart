# r13 — Hand-pixelled anime illustrations (restart)

User feedback (verbatim): "the illustrations look terrible, i want you to create them not based on the 3d model but
generate anime pixel art based on the description of the character and then define it with a team"

So: r12 illustrations (vector->pixel, pipeline/illustrate.py) are REJECTED. No 3D renders, no vector rasterising,
no tracing the sprites. Every pixel is placed by an artist in a hand-authored grid (pipeline/pixgrid.py, format in its
docstring). The team first DEFINES the character (design bible + style guide), then pixels it.

## Character description (the only source of truth besides the user's taste notes)
- Hero of a cosy mobile isometric snowy-mountain game. Young woman, cute, feminine, a bit curvy, semi-chibi
  proportions in game; in cut-scene art she is drawn as a normal anime heroine (approx 5-6 heads tall full body).
- Hair: long warm-brown hair (#6E3C3A / #A85A3A / highlight #D08658), straight hime-style bangs, side locks framing
  the face, half-up style: the upper hair gathered into ONE ponytail that tapers to a point at the tip, tied under a
  BIG teal ribbon bow at the back of the head (bow tails hang down). Rest of hair falls long down the back.
- Eyes: large anime eyes, teal irises (#153E4E/#2C9696/#86DCC6), dark lashes, soft brows.
- Outfit: cream/oatmeal winter coat (A-line, flares at the hips, rust #A85A3A trim at hem/cuffs, small buttons,
  belt), chunky teal knit scarf (#1C4C54/#2A8C8E/#6ACBB6), teal mittens, dark tights, brown winter boots.
- Personality: cheerful, warm, plucky, a little clumsy; shy when embarrassed.
- Palette: data/palettes/cw_oatmeal_portrait.json (ramps may be extended by the AD for portraits, keep the family).
- User taste notes: early Pokemon / GBA-DS era pixel charm, Japanese dot-e (ドット絵) line quality, cute and
  feminine, reads well from a distance, clean deliberate pixels (every pixel has a purpose), teal accent scheme.

## Deliverables (to 00_REVIEW/r13_anime_pixel/)
1. Design bible + style guide (docs) — team.
2. Dialogue busts: 10 expressions (neutral, smile, laugh, surprised, sad, angry, embarrassed, determined, worried,
   content), one consistent bust base with expression patches.
3. Full-body cut-scene poses (idle, wave, point, hands on hips, recoil, shy, shiver, cheer) + front/side/back turnaround.
4. Sprite sheets (transparent PNG + JSON) for engine; x4 previews.
