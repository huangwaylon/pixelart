# r17: a new base 3D model, generated from scratch by Gemini 4 Argon

The user asked (verbatim): "get gemini argon to generate a better, more pretty, detailed, base model from scratch without
referencing your existing model. you should describe in detail, the character, the details, anime esque, semi-chibi,
silhouette, feminine, cute"

Gemini gets only this description. It does not see our current SDF model, its renders or its STLs.

## Character description (send this to Gemini)

**Who she is.** The heroine of a cosy mobile isometric game set in snowy mountains. She is a cheerful, plucky young woman
of about 19-20 with a little clumsiness. She is cute and feminine, with soft gentle curves, and she should read as
"adorable anime heroine" in a single glance.

**Style.** Japanese anime, semi-chibi. Think a modern cute JRPG field model (Atelier, Ni no Kuni, Pokémon
Legends-era humans, Genshin-style chibi figurines): clean stylised forms with smooth surfaces, no realism, no
muscles. Every shape should be appealing and designed, with no lumpy blobs.

**Proportions.** About 3.2-3.5 heads tall. The head is large, about 30% of the height.
- Neck: short and slender.
- Shoulders: narrow and sloped, about 1.1 head-widths across.
- Torso: small, with a gently defined waist that is the narrowest point, and a modest bust and soft hips. The hips flare
  slightly wider than the waist and carry the coat's A-line.
- Legs: slim and tapered, about 1.2 heads long. The thighs are slightly full, the knees small and the calves slender,
  with small feet in chunky boots.
- Arms: slim, and the hands are small (mittens).
- Overall silhouette: a pear or teardrop shape. The big head and hair sit on top, a small waist below it, and the
  coat flares into an A-line skirt over slim legs.

**Head and face (most important).**
- **Head shape:** NOT a sphere. Use anime head construction:
  - a rounded cranium;
  - cheeks that narrow below the eye line;
  - a soft but clearly POINTED, small chin (a V-taper);
  - a jaw line that curves from below the ear to the chin, visible in 3/4 and profile.

  The face is slim and heart-shaped. The profile shows a slight forward cheek curve, a tiny nose bump and a small chin.
- **Eyes:** large anime eyes, modelled as shallow almond-shaped recesses or inset discs so that their perspective
  reads in 3/4 view.
  - Shape: slightly tare-me (gently drooping outer corners) with a rounded top lid.
  - Placement: set on the lower half of the head, with about one eye-width between them.
  - Colours: iris teal, lash line dark.
- **Rest of the face:** a tiny nose (a small ridge), a small mouth and slight cheek fullness. Ears are mostly hidden by
  the hair.

**Hair (signature).** Warm chestnut brown, built as designed, layered clumps, never a smooth helmet.
- **Bangs:**
  - Full hime-style bangs that are voluminous and LIFT OFF the forehead.
  - Layered: a back layer and a front layer of pointed clumps with staggered lengths. The tips curve and flick slightly,
    and a few cross over others.
  - The centre bangs reach just above the brows. The side bangs slope gently longer toward the temples and blend into
    the side locks, so no bare forehead shows at the sides.
  - There are small gaps between clumps.
- **Side locks:** one flat, slightly curved lock per side framing the cheeks, down to the collarbone, cut in a soft
  point.
- **Back hair:** long, falling down the back to about mid-back, as 4-6 broad tapering clumps with soft pointed tips, and
  slight volume at the crown.
- **Half-up ponytail:** the upper hair is gathered at the back of the crown into ONE ponytail that tapers to a single
  point at about the shoulder blades, with a gentle S-curve.

**Bow (signature).** A BIG teal satin ribbon bow tied at the back of the head where the ponytail is gathered.
- **Loops:** two puffy, voluminous teardrop loops, about 1.5x the head width tip to tip, drooping slightly at the
  outer ends.
- **Knot and tails:** a pinched centre knot, and two tails hanging down to the shoulders with V-cut ends.
- **Seen from the front:** only the loop tips peek out behind the head on each side, and they must not read as cat ears.

**Outfit (cosy winter).**
- **Scarf:** a chunky teal knit scarf (cable ribs), one thick roll around the neck. One tail hangs down the front on
  HER LEFT side, to the waist, with a fringe.
- **Coat:** a cream/oatmeal winter coat.
  - Cut: fitted bodice, a small rounded (Peter Pan) collar under the scarf, and a gently defined waist with a thin
    brown belt and a small gold buckle.
  - Front: 6 small gold buttons, 3 above the belt and 3 below.
  - Skirt: below the waist it flares into an A-line skirt with soft folds, ending at mid-thigh in a curved hem with a
    rust-red trim band.
  - Sleeves: long, slightly puffy, with rust-red cuffs.
- **Mittens:** teal, with a visible thumb.
- **Legs and boots:** dark plum-charcoal tights on slim legs, and brown winter boots to mid-calf with a cream fur
  cuff, a rounded toe and a small heel.

**Colours (palette roles).**

| Part | Colours |
|---|---|
| hair | #6E3C3A shadow, #A85A3A base, #D08658 highlight |
| skin | #FCD6B4 light, #EBA586 mid, #D07C74 shadow |
| teal (bow/scarf/mittens) | #1C4C54, #2A8C8E, #6ACBB6 |
| coat | #F2E6CE, #D2BFA4 |
| rust trim | #A85A3A |
| tights | #45435E |
| boots | #6E3C3A |
| fur cuff | #F2E6CE |
| iris | #2C9696 |
| lash | #20223E |

**Pose for the model.** A relaxed A-pose standing rest, arms slightly away from the body (about 20-25°) so the arms and
waist read separately. The feet are slightly apart and the toes point forward.

## Technical contract (Gemini output)

- **Script:** one standalone Python 3 script, numpy only. No network access, and no file access outside the output dir.
  Run as `python gen.py <outdir>`.
- **Output files:** `model.obj` plus `model.mtl`. Use one material (`usemtl`) per part, named
  `skin`, `hair_shadow`, `hair`, `hair_hi`, `teal_dark`, `teal`, `teal_light`, `coat`, `coat_shadow`, `rust`, `belt`, `gold`, `tights`,
  `boots`, `fur`, `iris`, `lash`, `eye_white`, `mouth`.
- **Mesh:** triangulated, consistent outward winding, and watertight per part where possible. Aim for 40k-150k triangles:
  smooth but detailed.
- **Axes:** +Y is up, the character faces +Z, units are metres, the height is about 1.0 and the feet are at y=0.
- **Construction:** any technique Gemini wants, such as an SDF plus its own marching cubes, lofted or swept
  cross-sections, subdivided primitives, or deformed spheres and capsules. Hair clumps work well as swept tapered
  ribbons or tubes along curves.
- **Pose:** the rest pose above. No rig is needed.

## Evaluation

1. Render the mesh with `pipeline/meshrender.py`: 8 iso directions plus a hi-res front, 3/4, side and back turnaround.
2. Render a 48x64 pixelised sprite with our palette and outline rules.
3. Compare it against the current S4_hd. The comparison happens on our side only; Gemini never sees our model.
4. Send Gemini only its OWN renders for 3-5 self-critique and refinement rounds.
5. AD verdict per body part.

## Update: user reference images (outside the repo, at /tmp/r17_refs/ref2-5.png; not committed for copyright reasons)
The user said (verbatim): "look at the face shape and model here, take inspiration from it for the gemini model ...
doesn't have to be this detailed, but your model should be something like this".
- **ref2, ref3 (stylised 3D women, front and 3/4 A-pose):** take the FACE from these:
  - a slim oval-to-heart face with high soft cheekbones;
  - a narrow jaw tapering to a small, defined chin, and a slim neck;
  - large almond eyes with a winged upper lash;
  - a small nose ridge and small full lips;
  - soft wispy bangs that part slightly and lift off the forehead.

  Also take the body: slim limbs, a defined waist and long tapered legs.
- **ref4, ref5 (anime cel-shaded toon model, side and front):** take the overall MODEL LANGUAGE from these:
  - clean anime toon forms;
  - long straight hair as a few large smooth layered sheets with blunt-cut bangs and side locks;
  - big anime eyes;
  - a simple flat-shaded outfit with crisp folds;
  - slim straight legs and small feet.

  This is the target look, with less detail allowed.
- **Proportion decision (lead):** about 5.0 heads, to match the APPROVED hand-drawn turnaround. That is taller and slimmer than
  the brief's earlier 3.2-3.5 heads, and keeps the refs' slim limbs and small waist. The game sprite is squashed from it.
- **Outfit and colours:** unchanged; our character keeps her winter outfit, bow and ponytail. The refs are only for face,
  body shape and modelling language.
- Gemini MAY see these reference images. It still must never see our existing model.
