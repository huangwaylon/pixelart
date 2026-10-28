idle: NEW nat/prop/read/energy = 6/8/7/4 ; OLD = 6 ; fixes: f0–f5 are almost the same pose, so add a 1 px chest/head rise on f3 (300 ms) and lower the shoulders on f0. The blade points forward-up like a guard instead of resting, so drop it about 20° toward the ground so idle and walk use the same grip.

walk: NEW nat/prop/read/energy = 7/8/6/5 ; OLD = 5 ; fixes: the blade switches from pointing forward in idle to trailing down-back here, so pick one carry direction. On f2/f5 (passing) the legs merge into one column, so separate the knees 1–2 px and add a 1 px head bob on the contact frames f0/f3.

run: NEW nat/prop/read/energy = 6/8/6/4 ; OLD = 7 ; fixes: the torso is too upright and the stride is short, so on contact frames f0/f3 lean the body 15–20° forward and push the back leg to full extension. Add one airborne frame (f2/f5, both feet off the ground) so it reads as a run, not a fast walk. The blade is mostly hidden behind the hip, so angle it up-back so it extends past the silhouette.

jump: NEW nat/prop/read/energy = 6/8/5/4 ; OLD = 7 ; fixes: the f1 crouch is too shallow, so drop the hips 3–4 px with knees clearly bent, and raise the apex at f4 (160 ms) by 4+ px with the knees tucked; right now she floats with her legs dangling. The blade points straight down in f0–f2 and merges with the legs, so swing it out to the side.

dash: NEW nat/prop/read/energy = 5/8/5/3 ; OLD = 8 ; fixes: f2 (40 ms) should be the peak, so make it a long low forward extension with the back leg straight and the blade trailing horizontally. f3 is a hunched pose with the blade vertical and reads like a stumble, so replace it with a deceleration skid (lead foot planted, torso upright) before f4.

slash: NEW nat/prop/read/energy = 5/8/5/5 ; OLD = 7 ; fixes: f1 points the blade straight backward, which reads as a back-swing in the wrong direction. Cut it or turn it into a high cocked windup over the shoulder. The smear is on f3, after the blade has already passed in f2, so move the arc to f2 (40 ms) with the arm fully extended forward, and hold f3 as the impact pose.

overhead: NEW nat/prop/read/energy = 7/8/7/6 ; OLD = 7 ; fixes: on f1 the blade is raised but the body barely moves, so lean the torso back and rise up on the toes for more anticipation. On f3 (160 ms smear), drop the hips and step the lead foot forward so the chop has weight; f2's smear can go down to 30 ms.

hurt: NEW nat/prop/read/energy = 5/8/4/5 ; OLD = 6 ; fixes: there's no clear recoil direction, so on f0 snap the head and torso back to the left, away from the hit, 2–3 px. Stop the blade flipping (forward in f0, straight up in f1, dangling in f2) and keep it trailing loosely. Push f2's hunch further with a knee buckle so the hit reads at 1x.
