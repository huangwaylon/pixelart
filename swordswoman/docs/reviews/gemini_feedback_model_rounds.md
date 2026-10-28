## Round 1 — Gemini overall 6.6 pass=False
Scores: {'design_fidelity': 8, 'chibi_appeal': 5, 'silhouette_readability': 8, 'pixel_art_readiness': 6, 'technical_quality': 6}
MUST FIX:
- Hair bangs & volume (All views): Current bangs are a flat, uniform scalloped fringe plastered to a spherical skull, making her look bald/helmeted compared to the ref. Model chunky, layered anime bangs that frame the face and add outer volume to the hair mass (see Image 2).
- Head shape & eye placement (Front/Iso views): Lower face is too wide/bloated and eyes sit too high on the head. Taper the jaw/cheeks into a softer anime chibi contour and lower the eyes so the forehead/bangs occupy the upper half of the head.
- Hair color (All views): The warm milk-chocolate brown is too light and loses contrast at 56px. Shift to the dark espresso/charcoal brown from Image 1 & 2.
- Face lighting & outlines (Front/Iso views): Disable cast shadows on the face mesh (the harsh diagonal shadow cutting across her nose/cheek ruins the 2D appeal and muddies the 56px sprite) and remove the inner black outlines around the blush/under-eye.
- Katana tsuka/hilt clipping (Front/Iso views): The long sword handle clips straight through her left forearm/ flared sleeve. Adjust wrist rotation or grip point so the hilt clears the sleeve geometry cleanly.
- Pose test right arm deformation (Image 7, iso SE pose_test): In the two-handed stance, her right bare shoulder collapses/clips into the collar and the upper arm appears detached. Fix upper-arm rig weights and shoulder pivot.
- Shoe ankle straps (Front/Side/Iso views): Missing the signature crisscross ankle straps from Image 1 & 2; currently reads as plain pumps/bare ankles. Add thick, sprite-readable dark straps.
- Right hip pouch (Front/Side views): The brown pouch on her right skirt hip looks like a flat coin pasted onto the skirt surface. Give it 3D bulk and tuck it properly at the bottom edge of the corset.
NICE TO HAVE:
- Scarf ribbons (Side/Back/Iso views): The two pink back ribbons look like stiff vertical planks in neutral pose; add a gentle S-curve and flared tips.
- Katana blade thickness (56px sprite views): Slightly thicken the blade geometry or brighten its value so the 1px line doesn't break up as heavily during nearest-neighbor downsampling.
- Hair bun silhouette (Front/Iso views): Enlarge the messy bun slightly so it reads more clearly behind the red bow.

## Round 2 — Gemini overall 6.2 pass=False
Scores: {'design_fidelity': 7, 'chibi_appeal': 5, 'silhouette_readability': 7, 'pixel_art_readiness': 6, 'technical_quality': 6}
MUST FIX:
- Head/Face & Bangs (all views, esp. front/SE/SW): The bangs are cut way too high and short, leaving a massive bare forehead that breaks the cute chibi appeal of ref 2. Lengthen the front bangs down to eyebrow/eye-top level with fuller, softer locks framing the face.
- Eyes & Facial Placement (ortho front, ortho side, iso S/SE/SW): Eyes sit too high and wide on the head sphere, and in side/iso views the eyeballs bulge/protrude past the face contour (see image 6/7 right eye sticking out). Recessed/flatten the eye geometry into the face mesh and lower the eye line slightly.
- Sleeves & Sword Guard Clipping (ortho front/side, pose_sword_ready): The wide sleeve bells are stiff cylinders that severely intersect the katana hilt/guard in idle side view and completely swallow the hand/hilt in sword_ready poses. Flare the sleeves more naturally from the elbow and rig/angle the lower sleeve so the hand and crescent guard clear the fabric.
- Hair Bun & Bow Placement (ortho front/side, iso views): The red bow sits perched on top of the bun like a hat rather than nestled at the front base of a large messy bun (ref 2). Enlarge the bun volume, remove the awkward thin spiky hair twigs sticking out of the top, and seat the bow lower against the crown/bun junction.
- Skirt & Belt Pouches (ortho front, iso S/SE): The two vertical brown leather straps/holsters hanging down the front center look like rigid sausages and obscure the asymmetric wrap slit from ref 2. Simplify the corset/pouch shapes into cleaner, chunkier masses that read at 64px without noisy silver rivets and tiny buckles (which turn into single-pixel noise in the sprite scale row).
NICE TO HAVE:
- Add the flowing pink tassel/ribbon to the katana hilt/guard as seen in ref 1 for extra secondary motion readability.
- Widen the stance slightly in the default idle so the two legs don't merge into a single flesh-colored pillar at 56px height.
- Push the value contrast between the dark brown hair and the black/dark-red outline in the palette so the back views (N, NE, NW) don't read as a flat dark blob at 1x sprite scale.

## Round 3 — Gemini overall 6.5 pass=False
Scores: {'design_fidelity': 8, 'chibi_appeal': 5, 'silhouette_readability': 8, 'pixel_art_readiness': 7, 'technical_quality': 6}
MUST FIX:
- Hair bangs and forehead (all views, especially front, side, and iso SE): Lower the bangs significantly so the tips reach the top of the eyes/eyebrows as in Image 2, eliminating the massive exposed forehead.
- Hair volume and side locks (front, side, iso): Add thicker, fuller side hair locks framing the cheeks and jaw, and smooth out the jagged, step-like cutout notch behind the cheek in the side profile (Image 5).
- Crown highlight band (side, iso SE, pose tests): Remove or reshape the thin, flat, tan/light-brown ring running horizontally across the top of the cranium—it reads like a monk's tonsure or a headband artifact in top-down isometric views rather than natural anime hair highlights.
- Head/face shape and eye placement (front, 3/4, iso): Soften the wide, bulbous lower cheeks into a smoother, cute chibi contour (per Image 2), lower the eyes slightly on the face, and widen the upper eyelash curve so the face has commercial chibi appeal rather than a bug-eyed doll look.
- Hair bun and bow placement (front, back, iso): Center the bun and red ribbon bow more cleanly behind the crown as in Image 2 (symmetric bunny-ear silhouette in front view) instead of the lopsided tilt to her right side.
- Sleeve cuffs and fabric drape (front, side, 3/4): Replace the thick,rolled, donut-like dark red torus at the bottom of the sleeves with thinner, sharper flared kimono-style cuffs that drape down rather than puffing out like inflatable tubes.
- Katana hilt/tsuka and ribbon (all views): Lengthen the tsuka handle so it is visible extending behind her grip (with the red/black diamond wrap), and add the long pink ribbon trailing from the guard/hilt as seen in Image 1.
NICE TO HAVE:
- Shoe ankle straps (front, iso): Thicken the criss-cross ankle straps so they register cleanly at 64px sprite resolution instead of breaking into single-pixel noise.
- Scarf ribbon tails (side, back, iso): Give the back pink scarf ribbons a cleaner S-curve flow and slightly more spread so they read as dynamic fabric rather than a stiff plank.
- Corset silhouette (front): Slightly cinch the waist/corset width so the transition from chest to flared skirt has a more appealing hourglass chibi rhythm.
- Liaison note (not Gemini): Gemini was given refs/1.png, concept/chibi_turnaround_v6_annotated.png, and renders/model_round_3/{sheet,ortho_front,ortho_side,iso_SE,pose_test}.png. Its bangs/forehead complaint contradicts the modeler's round-3 claim that bangs reach the eye-top line, and the bow-centering request conflicts with the bible's off-center bow placement; the AD should verify both against the renders before acting.

## Round 4 — Gemini overall 6.8 pass=False
Scores: {'design_fidelity': 8, 'chibi_appeal': 5.5, 'silhouette_readability': 8, 'pixel_art_readiness': 7.5, 'technical_quality': 7}
MUST FIX:
- Head & bangs (all views, especially ortho front/side and iso SE): The front bangs are cut way too short and high up, exposing a massive, bare, bulbous forehead. Lower the fringe/bangs down to just above the eyebrows and add fuller side-framing hair locks over the temples/cheeks to match the cute proportions of Image 2.
- Face & eyes (ortho front, side, iso SE): The eyes sit too low/far apart under the giant forehead, lacks eyebrows, and the spherical head shape makes her look like a creepy plastic doll rather than an appealing anime chibi. Add visible eyebrows, adjust eye placement relative to the lowered bangs, and soften the lower cheek/jaw contour.
- Skirt & legs clipping (pose tests: jump_apex, attack_slash_mid, sword_ready): In wide-stance dynamic poses, the upper thighs clip straight through the front/side of the red skirt mesh. Fix skinning weights or add skirt rig bones so the skirt opens/deforms cleanly over the legs without intersection.
- Scarf ribbon ends (ortho side, back, iso views): The pink neck ribbon has jagged, notched polygon cutouts at the tips that look like broken geometry. Clean up the mesh tips into a smooth, intentional swallowtail or tapered ribbon end.
NICE TO HAVE:
- Katana hilt ribbon (all views): Consider adding the small flowing pink ribbon attached to the katana guard/pommel from Image 1, or keep the neck ribbons slightly longer/more dynamic to enhance secondary motion in animations.
- Corset & belt pouches (sprite scale 56px): The three small silver buckles and multiple front belt pouches get a bit noisy at 1x pixel scale; slightly simplifying or merging the front pouch shapes would help pixel cluster clarity.
- Hands/fingers (ortho front): The cylindrical fingers look slightly stiff; a softer mitten-like chibi hand with a distinct thumb would read more apelike/cute in close-ups.

## Round 5 — Gemini overall 6.8 pass=False
Scores: {'design_fidelity': 8, 'chibi_appeal': 5, 'silhouette_readability': 8, 'pixel_art_readiness': 7, 'technical_quality': 6}
MUST FIX:
- Head/Hair (Front & Side ortho): The forehead is too tall and exposed, and the bangs are thin, flat, and sit too high up. Re-sculpt the hair mass to match the canonical chibi turnaround (Image 2)—thicker, fuller bangs that come down over the eyebrows and thick side locks framing the cheeks to hide the ear connection.
- Face/Head shape (Front & Side ortho): The lower face is too long and lantern-jawed, with the eyes placed too high and the mouth/nose too high above a large blank chin. Shorten the lower jaw, make the cheeks rounder and fuller (classic chibi squash), and lower the eye line to sit around the vertical midpoint of the head.
- Hair Bun & Bow placement (Front & Iso views): The red ribbon bow is lopsided to her right side instead of sitting symmetrically behind/under the bun as in Image 2, where both bow loops frame the bun evenly from the front.
- Skirt Hem Geometry (Front, Side, Back): The jagged, spiky 'banana peel' tails at the bottom of the skirt look stiff and cheap compared to the soft, pleated/ruffled layered fabric in Images 1 and 2. Soften the hem into broader, overlapping curved folds.
- Outline / Freestyle artifacts (Ortho & Iso renders): Broken, jagged, and floating black outline segments appear around the hair bun, neck, skirt tips, and ankles. Clean up geometry normals or switch to a clean inverted-hull / post-process outline so 64px downscales don't get noisy stray dark pixels.
- Katana Hilt & Guard proportions (Front & Side): The straight crossguard bar is overly thick and blocky like a broadsword, and the red/black diamond-wrapped long hilt is barely visible inside the sleeve cuff. Extend the hilt slightly and slim down the guard thickness.
NICE TO HAVE:
- Streaming Scarf / Ribbons: Add secondary bone dynamics or more dramatic S-curve arcs to the back pink scarf tails during run, jump, and slash animations to enhance motion trails at 64px.
- Corset & Pouches simplification: At 64px sprite scale, the three tiny silver buckles and multiple belt pouches merge into muddy brown noise; consider consolidating into 2 larger, high-contrast gold/silver reads.
- Katana Pommel Ribbon: Add the long flowing pink ribbon attached to the sword guard/hilt seen in Concept Image 1 for extra visual flair during slashes.
- [Liaison note, not from Gemini] The centred-bow must_fix and the hilt-ribbon nice_to_have repeat items the AD has already rejected. Gemini was given refs/1.png, concept/chibi_turnaround_v6_annotated.png, sheet.png, ortho_front.png, ortho_side.png, iso_SE.png and pose_test.png from renders/model_round_5, using model gemini-3.1-pro-preview with --json.

