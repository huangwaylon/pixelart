# 3D Artist memo: chibi winter girl and jump

1 u = 1 px; root at feet. Sq scales Y, XZ by 1/sqrt(Sq) (volume preserved).

## 1. Skeleton
root > pelvis (y10) > spine (y15) > chest (y20) > neck (y22) > head (centre y30) > hat > pom*
- chest > shoulder/elbow/hand, L and R
- pelvis > hip/knee/ankle, L and R
- neck > scarfA1-3*, scarfB1-2*
- head > braidL1-2*, braidR1-2*

`*` = deterministic spring sim.

## 2. Primitives (W x H x D, u)
| Part | Shape | Size |
|---|---|---|
| Head | sphere | 20 x 19 x 19 |
| Hair cap | head x1.06, clipped at the ear line | 21 x 14 x 20 |
| Bangs | 3 flat ellipsoids | 6 x 4 x 2 |
| Braids | 2 beads + tie, per side | 3.5 / 3 / 2 diameter |
| Beanie | half-ellipsoid clipped at the brow | 21 x 10 x 20 |
| Cuff | flat ring | 22 x 3.5 x 21 |
| Pom-pom | sphere | 5 diameter |
| Scarf wrap | 2 flat ellipsoids | 13 x 3 x 11 |
| Scarf tails | chain segments, 3 + 2 | 4 x 5 x 1.5 |
| Parka | egg, wider at the bottom | 15 x 12 x 12 |
| Hem | flat ring | 16 x 2.5 x 13 |
| Hood | half-ellipsoid at the back | 13 x 7 x 6 |
| Arms | upper / lower | 5 x 6 x 5 / 4.5 x 5 x 4.5 |
| Mittens | sphere + thumb | 4.5 / 2 diameter |
| Pants | thigh / shin | 5 x 5 x 5 / 4 x 4 x 4 |
| Boots | clipped at the sole, toe forward | 5 x 4 x 7 |
| Fur cuffs | flat ring | 6.5 x 2 x 6.5 |

Height ~42 u to beanie top (+2 pom). Hands and feet oversized for silhouette.

## 3. Jump (12 frames, 1060 ms)
Angles in degrees; tilt + = forward. P = pom, B = braids, S = scarf tails.

| # | Name | ms | Root | Sq | Spine/Head | Arms | Legs | Secondary |
|---|---|---|---|---|---|---|---|---|
| 1 | Ready | 100 | 0 | 1.00 | 0/0 | 10 out | straight | rest |
| 2 | Dip | 80 | -3 | 0.88 | +15/-5 | back 30 | knees 40 | lag, lift |
| 3 | Crouch | 120 | -5 | 0.80 | +30/-15 | back 70 | knees 80 | drape forward |
| 4 | Push | 60 | -1 | 1.12 | +10/0 | swing past 0 | knees 30, heels up | pulled down |
| 5 | Launch | 60 | +6 | 1.25 | -5/+10 | overhead 160 | extended, toes pointed | trail straight down |
| 6 | Rise | 80 | +14 | 1.10 | -10/+10 | 140 | tuck 30 | still dragging |
| 7 | Apex | 140 | +18 | 0.97 | 0/+5 | V shape 120 | asymmetric tuck, knees 70 | float level, P up |
| 8 | Fall | 80 | +15 | 1.02 | +5/0 | 90 | untuck 40 | overshoot up, flick |
| 9 | Drop | 60 | +7 | 1.15 | +5/-5 | 70 for balance | reach down 10 | stream upward |
| 10 | Contact | 60 | 0 | 0.92 | +10/-5 | 60 | knees 30 | still high |
| 11 | Squash | 100 | -4 | 0.75 | +25/-10 | forward and down 30 | knees 85 | slam past rest, snow puff |
| 12 | Settle | 120 | 0 | 1.04 to 1.00 | to 0 | to rest | straighten | 1 to 2 damped wobbles |

## Principles
Anticipation (2-3); squash/stretch 0.75-1.25; slow-in/out holds on 3, 7, 12; parabolic root, circular hand arcs; overlap lags P 1, B 1.5, S 2-3 frames; exaggerated 18 u hang; appeal via asymmetric apex, head up, open mittens. Feet pinned, integer snapping.
