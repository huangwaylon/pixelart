import sys, json, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/motion/scripts')
import mbuild
mbuild.MOT = sys.argv[1]
p = mbuild.build('walk'); a = json.load(open(p)); b = json.load(open('/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/motion/walk.json'))
mx = 0
for fa, fb in zip(a['frames'], b['frames']):
    for n in fb['bones']:
        d = np.abs(np.array(fa['bones'][n]['rot']) - np.array(fb['bones'][n]['rot'])).max(); mx = max(mx, d)
        if d > 1e-3: print(n, d)
print('maxdiff', mx, a['timing_ms'], [f['face'] for f in a['frames']])
