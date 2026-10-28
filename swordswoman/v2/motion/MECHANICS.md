# MECHANICS: whole-body motion spec (96 px girl, 30 deg ortho, views S SE E NE N)

Sources: Williams, *The Animator's Survival Kit* (walk: contact / down / passing / up; "the down is the lowest, the up is the highest";
"breaking joints", overlapping action, "the body is a sack of flour pulled by the hips"); the 12 principles (Thomas & Johnston; Wikipedia summary);
PMD SpriteCollab AnimData timings (refs/pmd, 1/60 s ticks); Pokemon BW / Octopath / Sea of Stars / SF3 practice (key holds, snappy
in-betweens, hair/cloth lag 1-2 frames); real mocap measured on our clips (L = leg length, ~33 px at 96 px; 1 px ~ 0.03 L).

Measured from the mocap (one cycle):
| clip | pelvis bob | side sway | pelvis yaw p-p | shoulder yaw p-p | pelvis obliquity p-p | head bob |
|---|---|---|---|---|---|---|
| Bandai walk_active | 0.093 L (~3 px) | 0.075 L (~2.5 px) | 22 deg | 11 deg (counter, r=-0.64) | 9 deg | = pelvis, same phase |
| CMU 02_03 jog | 0.18 L (~6 px) | 0.03 L | 13 deg | 12 deg (counter) | 10 deg | 0.22 L |
| CMU 09_01 run | 0.15 L | 0.05 L | 11 deg | 23 deg | 12 deg | 0.18 L |
Lowest pelvis = 1-2 mocap frames after contact (the "down"), highest = just after passing ("up"). Head follows the pelvis with ~1 frame lag.

Secondary-motion rules (all actions): the hair side locks, back hair, ribbon tails, bow and skirt hem are driven by damped springs on
their anchor's motion (inertia + gravity): they LAG 1-2 game frames behind direction changes, overshoot by 20-40% and settle in 2-3
oscillations. Order of lag (stiff to loose): bow (stiff, ~1 frame), side locks, skirt hem, back hair, ribbon tails (loosest, ~2 frames).
Vertical bob drives them too: on the down the hair lifts, on the up/landing it drops past rest. Sleeves follow the forearm with a small
drag. Never stretch limbs; never let secondary parts cross the face.

## idle (loop ~2.4 s, 10 frames; holds + quick transitions, PMD-style 20/4/2/4/4/2/6 ticks)
- Key poses: weight on R (hold) -> transfer (down, knees soften) -> weight on L (hold) -> transfer back. Contrapposto: stance hip UP and
  out by ~2 px, shoulders tilt the opposite way (counter-tilt ~3 deg), free knee bent and forward.
- Breathing: chest/shoulders rise ~1 px on the inhale, period ~1.2 s (two breaths per loop), the head rides on it.
- Head: tilts toward the free hip (~4-6 deg), small look-around (turn ~10 deg toward the camera side and back) once per loop,
  leads the body shift by a frame. Blink cue on one held frame (expression blink_closed, 1 frame ~100 ms).
- Arms: relaxed, elbows soft (15-25 deg), pendulum sway that LAGS the weight shift by one frame; wrists trail the forearm.
- Secondary: hair/skirt settle after each transfer (small overshoot), ribbon tails sway with the hip shift.

## walk (loop 8 frames, ~105 ms each = 0.84 s cycle; Williams 12-frame on twos at 24 fps ~ 1 s)
- Keys per step: CONTACT (heel strike, legs widest, arms widest, body mid) -> DOWN (weight lands, knee bends, body LOWEST,
  head lowest) -> PASSING (support leg straight, free foot passes, body mid-high) -> UP (push-off on the toe, body HIGHEST) -> contact.
- Hips: rise/fall 2-3 px (lowest on down, highest on up); side sway ~2 px toward the stance leg; pelvis yaw +-10 deg (forward hip on the
  leading leg) and pelvis obliquity +-4 deg (free side drops at passing). Feminine walk: feet near the centre line (narrow track),
  a bit more hip yaw/sway, shoulders level and calm.
- Shoulders counter-rotate the pelvis (+-5 deg) -> arm swing opposite the legs; torso lean ~3-4 deg forward.
- Arms: swing from the shoulder ~+-25 deg, elbow drags (forearm extends late on the back swing, bends ~20-35 deg on the forward swing),
  the wrist breaks last. Arm extremes ~1 frame after the leg contact (drag).
- Head: stable gaze forward, bobs with the pelvis, ~1 frame later; tiny counter-tilt to the hip.
- Secondary: side locks and back hair bounce up on the down and swing opposite the shoulder yaw; skirt hem swings with the leading thigh
  then lags on the reversal; ribbon tails trail behind and swing laterally with the sway.

## run (loop 8 frames, ~65 ms each = 0.52 s cycle; jog cycles 0.5-0.75 s)
- Keys per step: CONTACT (foot under the body, knee soft) -> DOWN (deepest squash, lowest, knee ~40 deg) -> PUSH-OFF/PASSING (driving
  leg extends) -> FLIGHT/UP (both feet off, highest, legs split) -> contact.
- Hips: bob 5-6 px (more than walk), low on down, high in flight; pelvis yaw +-6 deg; obliquity +-5 deg.
- Torso lean 10-15 deg forward, shoulders counter-rotate +-8 deg, chest twist visible in SE/E.
- Arms pump: elbows bent ~90 deg, swing +-35 deg, hands near the chest in front / behind the hip at the back; forearm whips at reversal.
- Head: forward, bob ~1 frame behind the pelvis, slight nod on the down.
- Secondary: hair and ribbons stream back (constant drag + bounce on each down); skirt hem flicks back and up in flight.

## jump (one-shot, 10 frames; PMD Hop 2,1,2,3,4,4,3,2,1,2 ticks: fast launch, slow apex, fast fall, held land)
- ANTICIPATION: crouch (knees ~70 deg, hips back, torso forward 20 deg, arms swing back and down) held 2 frames.
- LAUNCH: legs extend, arms swing forward-up, body stretches, head looks up. RISE -> APEX (tuck knees, arms up/out, hang 160+ ms)
  -> FALL (legs reach down, arms out for balance) -> LAND (squash: knees bend deep, torso forward, arms down/forward, head drops LATE)
  -> RECOVER (overshoot up a little, settle).
- Secondary: on launch hair/skirt/ribbons drag DOWN; at apex they float up (catch up and overshoot); on the fall they flow up;
  at landing they keep going down and bounce once (follow-through, 2 frames).

## dash (one-shot, 6 frames)
- ANTIC (lean back/down, arms cocked, 100 ms) -> BURST (hard forward lean ~25 deg, legs split, arms pump, 40 ms) -> DRIVE (40-60 ms)
  -> SKID (brake: torso pitches back, feet forward, arms out) -> RECOVER (settle upright with overshoot).
- Secondary: everything streams back during the burst/drive, then whips FORWARD past rest on the skid (strongest overlap of the set),
  settles on recover.

## hurt (one-shot, 5 frames; PMD Hurt 2,8 ticks = snap + hold)
- HIT (snap: head whips back first, shoulders back, hips forward, arms fly up/out, 80 ms) -> RECOIL (body bends back, step back,
  eyes shut) -> STAGGER (weight catches on a back step, arms out) -> RECOVER (back to neutral, head last).
- Head leads the reaction (it is hit), torso follows a frame later, hips last; secondary lags most here (hair flies forward past the face
  line is NOT allowed -> flies up/sideways).

## throw (one-shot, 9 frames; overhand, CMU throw)
- READY (weight back foot) -> WINDUP (anticipation: arm back and up, torso coils away ~30 deg, front arm points at the target,
  weight back) -> STRIDE (front foot plants, hips open FIRST) -> RELEASE (shoulders whip after the hips: hip-shoulder separation,
  elbow leads, wrist snaps last, 50 ms) -> FOLLOW (arm crosses the body, torso pitches forward, back foot lifts) -> RECOVER -> SETTLE.
- Whole-body chain: legs -> hips -> torso -> shoulder -> elbow -> wrist (successive breaking of joints, each ~1 frame later).
- Secondary: hair and ribbons lag the coil and then whip through on the release, settling over the recover/settle frames.
