"""make_test_wave.py -> render/test_wave.json : tiny pipeline-proof motion (R): right-arm wave + head turn, 12 frames, loop."""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rig'))
import importlib.util
spec = importlib.util.spec_from_file_location('ms', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rig', 'make_stress.py'))
src = open(spec.origin).read(); src = src[:src.index('P = []')]; ns = {'__file__': spec.origin}; exec(src, ns)
q, toward, X, Y, Z, NZ = ns['q'], ns['toward'], ns['X'], ns['Y'], ns['Z'], ns['NZ']
F = []
for i in range(12):
    ph = 2 * math.pi * i / 12; w = math.sin(ph)
    F.append({'t': i, 'root': {'loc': [0, 0, 0]}, 'bones': {
        'upper_arm.R': q('upper_arm.R', toward(NZ, X), 100), 'forearm.R': q('forearm.R', toward(NZ, Y), 35 + 30 * w),
        'hand.R': q('hand.R', toward(NZ, Y), 15 * w), 'head': q('head', Z, 25 * math.sin(ph / 2) ** 2 * (1 if i < 12 else -1)),
        'neck': q('neck', Z, 10 * math.sin(ph / 2) ** 2), 'hair_side.L.1': q('hair_side.L.1', X, 8 * w), 'hair_side.R.1': q('hair_side.R.1', X, 8 * w)}})
json.dump({'action': 'test_wave', 'fps': 12, 'loop': True, 'frames': F, 'timing_ms': [83] * 12, 'notes': 'R pipeline test'},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_wave.json'), 'w'))
print('ok')
