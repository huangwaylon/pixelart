"""make_stress.py : writes rig/qa/stress.json (contract motion format) -- deformation QA poses, rotations given as WORLD axes at rest
and converted to each bone's local rest frame (q_local axis = R_rest^T @ axis_world).  Contract frame: +X = her right, +Y = front, +Z up."""
import json, math, os
H = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(H, 'rest_skeleton.json')))
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def nrm(a): l = math.sqrt(sum(x * x for x in a)); return [x / l for x in a]
X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
NX, NY, NZ = [-1, 0, 0], [0, -1, 0], [0, 0, -1]
def toward(a, b): return nrm(cross(a, b))  # rotation axis that swings direction a toward b
def q(bone, axis_w, deg):
    M = S[bone]['matrix']  # rows; columns = local axes in world
    al = [sum(M[r][c] * axis_w[r] for r in range(3)) for c in range(3)]; al = nrm(al); h = math.radians(deg) / 2
    return {'rot': [math.cos(h)] + [math.sin(h) * x for x in al]}
FWD = toward(NZ, Y)   # swing a down-pointing bone forward
BACK = toward(NZ, NY)
P = []
def mul(a, b):  # quaternion product a*b (w,x,y,z)
    w1, x1, y1, z1 = a; w2, x2, y2, z2 = b
    return [w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2]
def pose(name, bones, loc=(0, 0, 0)): P.append({'key': name, 'root': {'loc': list(loc)}, 'bones': bones})
pose('rest', {})
pose('deep_knee_bend', {'thigh.L': q('thigh.L', FWD, 80), 'thigh.R': q('thigh.R', FWD, 80), 'shin.L': q('shin.L', FWD, -125), 'shin.R': q('shin.R', FWD, -125),
                        'foot.L': q('foot.L', FWD, 45), 'foot.R': q('foot.R', FWD, 45), 'pelvis': q('pelvis', toward(Z, Y), 12), 'spine': q('spine', toward(Z, Y), 8)},
     (0, -0.06, -0.33))
pose('stride', {'thigh.L': q('thigh.L', FWD, 38), 'shin.L': q('shin.L', FWD, -12), 'thigh.R': q('thigh.R', FWD, -28), 'shin.R': q('shin.R', FWD, -35),
                'foot.R': q('foot.R', FWD, 20), 'foot.L': q('foot.L', FWD, -20)}, (0, 0, -0.035))
pose('arm_raise_120', {'upper_arm.R': q('upper_arm.R', toward(NZ, X), 94), 'upper_arm.L': q('upper_arm.L', FWD, 120), 'shoulder.R': q('shoulder.R', toward(X, Z), 12)})
pose('elbow_120', {'upper_arm.R': q('upper_arm.R', FWD, 30), 'forearm.R': q('forearm.R', FWD, 120), 'upper_arm.L': q('upper_arm.L', FWD, 30), 'forearm.L': q('forearm.L', FWD, 120)})
pose('twist30_head40', {'spine': q('spine', Z, 15), 'chest': q('chest', Z, 15), 'neck': q('neck', Z, 15), 'head': q('head', Z, 25)})
pose('hair_chains_40', {**{f'hair_front.{s}.1': q(f'hair_front.{s}.1', toward(NZ, Y), 40) for s in 'LCR'},
                        'hair_side.L.1': q('hair_side.L.1', toward(NZ, NX), 40), 'hair_side.R.1': q('hair_side.R.1', toward(NZ, X), 40),
                        'hair_back.1': q('hair_back.1', toward(NZ, NY), 40), 'hair_back.2': q('hair_back.2', toward(NZ, NY), 15)})
pose('bun_bow_sleeves_40', {'bun': q('bun', toward(NY, Z), 40), 'bow.L.1': q('bow.L.1', toward(NX, Z), 40), 'bow.R.1': q('bow.R.1', toward(X, Z), 40),
                            'bow_knot': q('bow_knot', X, 20), 'sleeve.L.1': q('sleeve.L.1', toward(NZ, NY), 40), 'sleeve.R.1': q('sleeve.R.1', toward(NZ, NY), 40),
                            'sleeve.R.2': q('sleeve.R.2', toward(NZ, NY), 20)})
pose('skirt_40', {'skirt.F.1': q('skirt.F.1', toward(NZ, Y), 40), 'skirt.B.1': q('skirt.B.1', toward(NZ, NY), 40), 'skirt.L.1': q('skirt.L.1', toward(NZ, NX), 40),
                  'skirt.R.1': q('skirt.R.1', toward(NZ, X), 40), 'skirt.FR.1': q('skirt.FR.1', toward(NZ, nrm([1, 1, 0])), 30), 'skirt.F.2': q('skirt.F.2', toward(NZ, Y), 20)})
pose('stride+skirt', {'thigh.R': q('thigh.R', FWD, 45), 'shin.R': q('shin.R', FWD, -30), 'thigh.L': q('thigh.L', FWD, -25), 'shin.L': q('shin.L', FWD, -20),
                      'skirt.F.1': q('skirt.F.1', toward(NZ, Y), 25), 'skirt.FR.1': q('skirt.FR.1', toward(NZ, Y), 30), 'skirt.B.1': q('skirt.B.1', toward(NZ, NY), 15),
                      'upper_arm.L': q('upper_arm.L', FWD, 30), 'upper_arm.R': q('upper_arm.R', FWD, -25), 'spine': q('spine', Z, -8), 'head': q('head', Z, 10)}, (0, 0, -0.03))
# ---- round 2: head + hair at the round-2 spring limits, posing direction (contrapposto, hip sway, pointed toes, knees close)
pose('head_turn_L20_tilt10', {'head': {'rot': mul(q('head', Z, 20)['rot'], q('head', Y, 10)['rot'])}, 'neck': q('neck', Z, 5)})
pose('head_turn_R20_tilt-10', {'head': {'rot': mul(q('head', Z, -20)['rot'], q('head', Y, -10)['rot'])}, 'neck': q('neck', Z, -5)})
pose('head_nod_up15_down', {'head': q('head', toward(Z, NY), 15), 'neck': q('neck', toward(Z, NY), 5)})
pose('hair_r2_limits', {**{f'hair_front.{s}.1': q(f'hair_front.{s}.1', toward(NZ, Y), 14) for s in 'LCR'},
                        'hair_side.L.1': q('hair_side.L.1', toward(NZ, NX), 22), 'hair_side.R.1': q('hair_side.R.1', toward(NZ, X), 22),
                        'hair_side.L.2': q('hair_side.L.2', toward(NZ, Y), 15), 'hair_side.R.2': q('hair_side.R.2', toward(NZ, Y), 15),
                        'hair_back.1': q('hair_back.1', toward(NZ, NY), 28), 'hair_back.2': q('hair_back.2', toward(NZ, NY), 15),
                        'bun': q('bun', toward(NY, Z), 16), 'bow.L.1': q('bow.L.1', toward(NX, Z), 24), 'bow.R.1': q('bow.R.1', toward(X, Z), 24),
                        'head': q('head', Z, 12)})
pose('contrapposto', {'pelvis': q('pelvis', Y, 6), 'chest': q('chest', Y, -7), 'thigh.R': {'rot': mul(q('thigh.R', FWD, 12)['rot'], q('thigh.R', toward(NZ, NX), 6)['rot'])},
                      'shin.R': q('shin.R', FWD, -22), 'foot.R': q('foot.R', FWD, 12), 'thigh.L': q('thigh.L', toward(NZ, X), 4), 'head': q('head', Y, 5)}, (-0.012, 0, -0.008))
pose('hip_sway', {'pelvis': {'rot': mul(q('pelvis', Z, 10)['rot'], q('pelvis', Y, -6)['rot'])}, 'spine': q('spine', Z, -6), 'chest': q('chest', Y, 5),
                  'thigh.L': q('thigh.L', FWD, 20), 'shin.L': q('shin.L', FWD, -25), 'thigh.R': q('thigh.R', FWD, -12)}, (0.012, 0, -0.012))
pose('pointed_toes', {'thigh.L': q('thigh.L', FWD, 35), 'shin.L': q('shin.L', FWD, -45), 'foot.L': q('foot.L', FWD, -50), 'toe.L': q('toe.L', FWD, -20),
                      'foot.R': q('foot.R', FWD, -25)}, (0, 0, 0.02))
pose('knees_close_soft', {'thigh.L': {'rot': mul(q('thigh.L', toward(NZ, X), 7)['rot'], q('thigh.L', FWD, 14)['rot'])}, 'thigh.R': {'rot': mul(q('thigh.R', toward(NZ, NX), 7)['rot'], q('thigh.R', FWD, 14)['rot'])},
                          'shin.L': q('shin.L', FWD, -24), 'shin.R': q('shin.R', FWD, -24), 'foot.L': q('foot.L', FWD, 10), 'foot.R': q('foot.R', FWD, 10)}, (0, 0, -0.02))
for i, f in enumerate(P): f['t'] = i
json.dump({'action': 'stress', 'fps': 2, 'loop': False, 'frames': P, 'timing_ms': [700] * len(P), 'notes': 'R deformation QA poses'},
          open(os.path.join(H, 'qa', 'stress.json'), 'w'), indent=0)
print(len(P), [f['key'] for f in P])
