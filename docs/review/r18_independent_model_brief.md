# Character model brief (independent team)

Build a production-ready, stylised 3D character in Blender. This brief and the images in ./refs/ are your ONLY inputs.
The user rejected earlier attempts as "hideous" and wants production-ready meshes, roughly the quality of a
modern stylised / anime game character (see refs).

## Who she is
- The cheerful, plucky heroine of a cosy mobile game set in snowy mountains.
- A young woman of about 19-20: cute and feminine, slim and petite, with soft gentle curves.
- She must read in one glance as a beautiful, adorable anime heroine.

## Style and proportions
- Stylised anime toon, like refs/ref4-ref5 (cel-shaded anime model) with the face appeal of refs/ref2, ref3, ref6, ref7 and ref9.
- About 5 to 5.5 heads tall: a slightly large head, a slim neck, narrow sloped shoulders, a small defined waist, a modest
  bust and soft hips.
- Long slim tapered legs, small hands and small feet.

## Face (most important)
- **Shape:** slim oval-to-heart face, cheek planes turning into a narrow jaw, and a small clearly pointed chin. Clean
  profile with a tiny nose tip and small full lips.
- **Eyes:** large anime eyes, modelled as almond-shaped eye sockets with separate eyeball or eye-plane geometry.
  - Thick upper lash with an outer wing.
  - Teal irises.
- **Brows:** thin and shaped.
- **Ears:** mostly covered by the hair.

## Hair (warm chestnut brown)
Designed as large smooth sculpted SHEETS and clumps, as in ref4-7, never noodles or a helmet.
- **Bangs:**
  - Full blunt-ish bangs with 2-3 notches, layered (a back layer and a front layer) and lifting slightly off the
    forehead.
  - Longer at the sides so they slope into the side locks; no bare temples.
- **Side locks:** two face-framing locks down to the collarbone.
- **Back hair:** long, to mid-back, as broad tapering sheets with a few loose thin strands.
- **Ponytail:** half-up. Upper hair gathered at the back of the crown into ONE voluminous layered ponytail that tapers
  to a point (see ref6 for ponytail volume).

## Accessory
- **Bow:** a BIG teal satin ribbon bow where the ponytail is gathered.
  - Two puffy loops, about 1.5x the head width tip to tip.
  - A pinched knot, and two tails with V-cut ends.

## Outfit (cosy winter)
- **Scarf:** a chunky teal cable-knit scarf, one thick roll around the neck. One tail hangs down the front on HER LEFT
  side, with a fringe.
- **Coat:** cream/oatmeal winter coat.
  - Fitted bodice with a small round collar, a thin brown belt and a small gold buckle.
  - 6 gold buttons.
  - Flares into an A-line skirt with soft folds, ending at mid-thigh with a rust-red hem band.
  - Long sleeves with rust cuffs.
- **Mittens:** teal, with thumbs.
- **Legs and boots:** dark plum-charcoal tights, and brown mid-calf winter boots with cream fur cuffs and rounded toes.

## Colours (flat toon base colours)

| Part | Colours |
|---|---|
| hair | #A85A3A, shadow #6E3C3A, highlight #D08658 |
| skin | #FCD6B4, shadow #EBA586 |
| teal | #2A8C8E, dark #1C4C54, light #6ACBB6 |
| coat | #F2E6CE, shadow #D2BFA4 |
| rust | #A85A3A |
| tights | #45435E |
| boots | #6E3C3A |
| fur | #F2E6CE |
| iris | #2C9696 |
| lash | #20223E |
| gold | #E2A434 |

## Production requirements
- **Tool:** Blender 5.2 headless (`/Applications/Blender.app/Contents/MacOS/Blender -b -P script.py`). Model entirely by Python
  (bpy/bmesh) as a real modeller would:
  - low-poly box-modelled / edge-loop cages with quad topology;
  - Mirror and Subdivision Surface modifiers, and creases or support loops for crisp edges;
  - curves or bevelled ribbons for hair sheets, and Solidify for cloth;
  - shade smooth, with correct outward normals and no non-manifold junk.
- **Pose and scale:** A-pose, 1 unit = 1 m, height about 1.6 m, feet on Z=0, facing -Y.
- **Objects and materials:** separate named objects (Body, Head, Eyes, Hair_*, Bow, Scarf, Coat, Mittens, Tights, Boots).
  One material per colour role, using toon shading (EEVEE with Shader-to-RGB and a colour ramp, or Workbench flat).
- **Polycount:** about 30-80k triangles at export.
- **Export:** `.blend` plus `.glb`, plus `.obj`/`.mtl`.
- **Renders:**
  - front, 3/4, side and back turnaround (orthographic, 1024 px tall);
  - a face close-up (front and 3/4);
  - side-by-sides with ref4 and ref5 at the same framing.
- **Iteration:** at least 5 viewed iterations. Look at your renders with the Read tool and fix what looks wrong each time.

---
**Process note (lead):** the user rejected the Gemini r17 mesh (v2) as "hideous", asked for production-ready meshes, and
suspected the design echoed our existing model. Both Gemini tracks were stopped. Track A's engineer had worked with our
SDF model earlier, so contamination was possible. Two fresh, isolated modelers (A and B) now build competing Blender
models in /tmp/indep/A and /tmp/indep/B. Their only inputs are this brief and the user's reference images. They are
forbidden from reading this repo or any earlier attempt. The results get copied into 00_REVIEW/r18_blender_model/ and
reviewed by an independent AD, with Gemini used only as a critic.
