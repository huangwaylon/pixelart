# r15 mesh request (Gemini 4 Argon) - NOT YET ANSWERED

Attempt 1 (with turnaround_x3.png): no output within 1500 s (alarm). Attempts 2-3 (compact variant, with/without image): auth failure 'No authentication method found'.

## Prompt (compact variant, p2b)

Write a single standalone Python 3 script, gen.py, that procedurally builds a stylised low/mid-poly anime character TRIANGLE MESH of the heroine described below and writes it as OBJ + MTL. The attached image is the approved target turnaround (front, 3/4, side, back) - match it.

HARD RULES (the script will be sandboxed and rejected otherwise):
- Import ONLY numpy, sys, os, math. No network, no subprocess, no other files read.
- Usage: python gen.py <outdir>. Write ONLY <outdir>/gemini_model.obj and <outdir>/gemini_model.mtl.
- Coordinate system: Z up, character faces -Y (toward the viewer at -Y), X is the character's LEFT? No: +X is the viewer's right when looking at her front. Feet on z=0. Units: 1 unit = 1 sprite pixel at a target height of 52 units (crown to sole) - game proportion 3.4 heads tall, so H (crown to chin) ~ 15.3 units. Put her standing in a relaxed idle (arms down slightly away from the coat, legs together, slight gap).
- Output: closed or near-closed shells per part, outward-facing CCW triangles, 20k-80k triangles total. Use OBJ groups and usemtl with EXACTLY these material names: skin, hair_1, hair_2, teal, oat, rust, tights, boots, iris, ink, white (eye white/catchlight), gold (belt/buttons), blush. MTL Kd colours: skin #FCD6B4, hair_1 #6E3C3A, hair_2 #A85A3A, teal #2A8C8E, oat #F2E6CE, rust #A85A3A, tights #45435E, boots #6E3C3A, iris #2A8C8E, ink #20223E, white #FFFFFF, gold #9C5C2E, blush #F06A58. (hair_2 can be used for a lighter hair layer such as the bang panels or the ponytail highlight strands.)
- Build parts from your own helpers: lofted/swept tubes with variable elliptical cross-sections along a spline (for limbs, ponytail, side locks, bow tails, scarf tail), superellipsoids, revolved profiles (coat skirt, boots), and thin shells / extruded curves (bangs, bow loops). Write the helpers yourself.

DESIGN (Koyuki, 19-20, cute not childlike, Pokemon-DS anime style):
- Proportions (H = crown to chin): game 3.4 H tall. Head is large and round: cranium wider than the face, soft oval face with full cheeks, the jaw tapers to a small chin. Shoulders 0.9 H, sloped, narrower than the hair. Waist 0.75 H, belt at about 2.05 H from the crown in the 5.4H illustration (scale proportionally), hips 1.0 H, coat hem 1.6 H wide (A-line flare). Short legs at game scale (1.1 H), slim ankles.
- Face: large rounded-top tare-me (slightly droopy outer corners) eyes set LOW on the face, one eye-width apart, as slightly inset/raised decal geometry: ink upper lash line, teal iris, white catchlight. Small nose bump, tiny mouth, two blush dashes. Ears hidden by hair.
- Hair: hime bangs = blunt cut just above the brows, with 2 notches making 3 panels, centre widest; the bangs are a thick shell that stands slightly off the forehead. Side locks: flat straight panels from temple to collarbone, blunt cut. Back hair: long straight curtain, blunt slight-V cut at the hip. Ponytail gathered at the back of the crown (brow height in side view) under the bow knot, swells to 0.5 H thick, tapers in a gentle S curve to a sharp point at the waist. Hair colour hair_1 base; hair_2 for highlights.
- Bow (BIG, teal): about 2x head width, the wings stick out past the head in the front view; two loops pinched at a central knot (knot at the ponytail root, back-top of head), each loop with one crease; two swallowtail (V-notched) tails hanging down to the shoulder blades.
- Coat (oat): mid-thigh A-line, fitted to the waist, rust hem band and rust cuffs, gold 6 centre buttons (3 above the belt), gold/brown belt band at the waist. Long sleeves.
- Scarf (teal): chunky double wrap around the neck, about 0.3 H thick, hiding the collar; ONE tail hanging on HER LEFT side (= viewer's right in front view, +X) down to the belt, with a fringe.
- Rounded teal mittens with a thumb bump. Dark tights (tights). Mid-calf boots (boots) with cream oat fold-over cuffs, a slight toe box and a sole.

Prioritise silhouette and appeal at 48x64 iso sprite scale: big readable head and bow, clear ponytail arc in side view, clean A-line coat. Keep the script COMPACT: at most ~350 lines, reuse a few generic helpers (loft along a polyline with elliptical sections, superellipsoid, revolve profile, extruded 2D outline). Output ONLY the Python code in a single ```python block, then a 5-line part list.
