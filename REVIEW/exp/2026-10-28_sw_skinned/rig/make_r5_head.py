"""make_r5_head.py -> rig/qa/r5_head.json : round-5 head/hair QA poses (rest, head tilt +-15 deg, nod, bangs/side/back/bun/bow at M's spring limits)"""
import json, os, math
H = os.path.dirname(os.path.abspath(__file__)); src = open(os.path.join(H, 'make_stress.py')).read(); src = src[:src.index('P = []')]
ns = {'__file__': os.path.join(H, 'make_stress.py')}; exec(src, ns); q, toward, X, Y, Z, NX, NY, NZ = (ns[k] for k in ('q', 'toward', 'X', 'Y', 'Z', 'NX', 'NY', 'NZ'))
F = []
def pose(k, b, face='neutral'): F.append({'t': len(F), 'key': k, 'root': {'loc': [0, 0, 0]}, 'bones': b, 'face': face, 'blink': 0.0, 'mouth': 'closed'})
pose('rest', {})
pose('tilt_+15', {'head': q('head', Y, 15)}, 'smile')
pose('tilt_-15', {'head': q('head', Y, -15)}, 'smile')
pose('nod_down_10', {'head': q('head', toward(Z, Y), 10)})
pose('turn_+20', {'head': q('head', Z, 20)}, 'determined')
pose('bangs_fwd_14', {f'hair_front.{s}.1': q(f'hair_front.{s}.1', toward(NZ, Y), 14) for s in 'LCR'})
pose('bangs_back_14+side_22', {**{f'hair_front.{s}.1': q(f'hair_front.{s}.1', toward(NZ, NY), 14) for s in 'LCR'},
                               'hair_side.L.1': q('hair_side.L.1', toward(NZ, NX), 22), 'hair_side.R.1': q('hair_side.R.1', toward(NZ, X), 22)})
pose('back_28+bun_16+bow_24', {'hair_back.1': q('hair_back.1', toward(NZ, NY), 28), 'hair_back.2': q('hair_back.2', toward(NZ, NY), 15),
                               'bun': q('bun', toward(NY, Z), 16), 'bow.L.1': q('bow.L.1', toward(NX, Z), 24), 'bow.R.1': q('bow.R.1', toward(X, Z), 24)}, 'joyful')
pose('tilt_+15+swing', {'head': q('head', Y, 15), 'hair_side.L.1': q('hair_side.L.1', toward(NZ, NX), 18), 'hair_back.1': q('hair_back.1', toward(NZ, X), 20),
                        **{f'hair_front.{s}.1': q(f'hair_front.{s}.1', toward(NZ, X), 10) for s in 'LCR'}}, 'surprised')
pose('blink', {}, 'neutral'); F[-1]['blink'] = 1.0
json.dump({'action': 'r5_head', 'fps': 4, 'loop': False, 'frames': F, 'timing_ms': [400] * len(F)}, open(os.path.join(H, 'qa', 'r5_head.json'), 'w'), indent=0)
print(len(F))
