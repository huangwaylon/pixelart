# v2 BRIEF: simplified chibi swordswoman, pixel sprites + lively animation

Date started: 2026-10-25. Root: `/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/`. Everything new goes here; old work (`hybrid/`, `model/`, `renders/`, `pixel/`) is reference only.

## User verdict on everything so far
All earlier pixel art, models and animations are "terrible, inaccurate, inconsistent, not good pixel art".

The user wants:
1. **A model that is a good, solid reference for the pixel art.** It should give consistent proportions across directions and poses.
2. **Much better animation:** lively, bouncy and energetic, with timing chosen for impact, and **smears on fast actions**.
3. **Simplification.** Remove small and tiny details. The silhouette and design must be simple and readable at pixel size. Keep simplifying until the pixel art is good.
   - A **no-katana version** is allowed if that helps.
4. **Actions:** idle, walk, run, jump, dash, slash (attack). More are welcome later: hurt, overhead slash.
5. **Deliverables are GIFs.**

## Character: simplified design target (v2 spec; the design strand may refine it)
Keep her identity and drop the clutter.

**Keep:**
- Chibi, about 2.5 heads tall, with a big round head.
- A **dark brown/black bob with bangs** and a **small bun at the back**.
- A **big red bow** on top. It is the silhouette ID.
- Big blue eyes, set low.
- A **red short kimono-dress** with a flared hem.
- **One dark belt (obi) band.**
- Pale legs and **simple dark shoes/boots**.
- Optionally a katana: a straight thin blade with a simple dark hilt. The hook guard is dropped.

**Remove:**
- corset buckles, pouches and thigh straps
- choker, collar points and the high collar
- pink scarf ribbons
- arm ornaments, chest flower and cords
- strappy sandals
- detached-sleeve complexity: use simple wide sleeves, or short sleeves
- skirt tails and asymmetric wrap

**Palette:** keep to about 16–20 colours total, 2–3 ramps per material, based on `docs/palette.json`. Use dark outlines, selective where it helps.

## Sprite spec (provisional; the design strand tests sizes)
- Character height about **48 px** (also test 40 and 56), in a 64×64 cell. Feet pivot at the bottom-centre.
- Views:
  - Isometric 3/4 top-down: camera elevation about 30°.
  - Priority directions: **SE** (front 3/4) and **E** (side).
  - Then all 8: S, SE, E, NE, N, plus SW, W and NW, mirrored where the design allows. The katana hand flips when mirrored, which is acceptable.
- Frame timing comes from `docs/ANIM_DIRECTION.md` §1. Its principles are good; the execution was not. In short:
  - idle: 4–6 f, slow bob
  - walk: 8 f at about 100 ms
  - run: 6–8 f at about 70 ms
  - jump: anticipation crouch, launch stretch, apex hang, fall, land squash, recover
  - dash: anticipation, 1–2 smear frames, skid or recover
  - slash: anticipation, 1 smear frame (arc), hit-stop hold, follow-through, recover

## Tools
- Gemini (Floodgate):
  - Critique or vision with **Gemini 4 Argon** (default critic): `.venv/bin/python tools/gemini.py ask "prompt" img1.png ...`. This is the same model as Apple Pi CLI; the `pi` CLI itself has no auth in this shell, so use this script.
  - Image generation or editing: `.venv/bin/python tools/gemini.py image "prompt" out.png [ref.png ...]`. The model is gemini-3-pro-image; Argon cannot output images.
  - Run from the project root `/Users/waylonhuang/Documents/other/pixelart/swordswoman`.
- Claude Opus 5.5 as art critic or pixel fixer, with extra quota on other accounts:
  - `claude-as be_system --dangerously-skip-permissions --model claude-opus-5-5 -p "..."`
  - Other accounts: `bni_requests`, `nsystem4`.
  - These are zsh functions. Run them with `zsh -ic 'claude-as ...'`.
  - Give absolute image paths; the critic can Read PNGs.
- Blender: `/Applications/Blender.app/Contents/MacOS/Blender -b ...`
- Python with PIL and numpy: `/Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python`
- 3D from images, available locally:
  - Hunyuan3D-2mini: `.scratch/hunyuan`, about 25 s per image.
  - Pixal3D 4-view: `.scratch/pixal3d`. Earlier test: best with 4 consistent views.
  - TRELLIS: `.scratch/trellis`.
  - Hunyuan3D-Omni pose control: `.scratch/hy_omni`, still downloading.

## Quality gates
- Every iteration produces GIFs at **4× or 6× nearest-neighbour upscale** on a mid-grey background, plus a contact sheet.
- Every iteration is critiqued by **both** Argon and an Opus critic. Use a director-style panel and score honestly; Gemini tends to overrate pixel art. Each critique must name concrete pixel problems, not praise.
- Pixel-art rules:
  - No orphan or noise pixels, no jaggies on outlines, no pillow shading, no banding.
  - Clusters are deliberate.
  - The palette is locked per material, and colours are consistent frame to frame.
  - Silhouette readability is checked at 1× size.

## Log
Each strand writes `v2/<strand>/NOTES.md`: what was tried, results, image paths, and the critique summaries.
