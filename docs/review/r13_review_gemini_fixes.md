# r13 review: Gemini triage fixes (AD)

Checked per pixel against HEAD~4. All changes stay inside the fix areas. Bust overlays carry over unchanged except angry and embarrassed, as specified.

## Bust (L): APPROVED
- Items 1-8 are all in: K x76 is `hair_1`, the seams end at y44/y48, one crown split, the curtain tapers x84 to x80, shoulders are in 6/3 px, the placket moved 2 px left, and the `oat_1` shadow is in.
- Nose `u` at (45,46) is the spec's relative pixel. Accepted.

## Turnaround + A poses (T): APPROVED
- 4 views plus idle, wave, point and hips: continuous trim, 1 px centre sag, rounded corners.
- Back: a blunt slight-V at x34-61 (y66, centre y68). The ponytail has a `plum_0` tip at y62 and a `hair_1` cast shadow.

## B poses (H): FIXES
- Recoil lock: approved (one sweep, tucked at y36).
1. **Shy and shiver hem is broken.** The trim covers only x36-56 at y85. Below it come an `oat_2` row (y86) and a second `hair_1` row (y87), so a light stripe shows. The outer sides (x27-35, x57-64) have no trim. Copy the idle hem rows 82-86 and keep the pose's lift.
2. **Recoil regression.** Lifting the hem detached the standing leg. Rows y87-88 at x46-53 are now transparent. Extend the leg top (`I`/`n` with a K edge) up to the hem K.

## Gemini r2 (`docs/review/gemini/r13_illustrations_r2.md`)
It confirms most fixes. Rulings:
- Detached recoil leg: **ACCEPT** (it named the wrong leg; it is the standing leg). Missing shy/shiver trim: **ACCEPT**.
- "Flat hem" on wave, point and hips: **REJECT** (they have the sag).
- Shiver strays: **REJECT** (that is the `snow_1` shiver FX).
- 3/4 and side ponytail notch: **REJECT** (approved silhouette, locked design).
- Scarf-roll sag: **REJECT** (rejected in r13 triage).
