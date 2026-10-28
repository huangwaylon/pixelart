"""tlock.py CLIP M[,M] : temporal-lock fix -> out/<clip>/<m>_tl/: frame t+1 copies frame t's char on every render-static cell
(8x8 hi-res block unchanged: same matid px, mean |dlum| < .01), and on cells whose 3x3 render neighbourhood is static too (so context-driven
churn at static cells is removed). Frame 0 is the anchor (no wrap)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hx, run, temporal as T
clip = sys.argv[1]; view = clip.split('_')[1]; sh = run.align(view); n = len(json.load(open(hx.EXP + f'big/{clip}/{clip}.json'))['frames'])
M, _ = T.static_masks(clip, n, sh)
for m in sys.argv[2].split(','):
    od = hx.EXP + f'out/{clip}/{m}_tl'; os.makedirs(od, exist_ok=True)
    G = [hx.read_grid(hx.EXP + f'out/{clip}/{m}/f{i:02d}.txt') for i in range(n)]; out = [G[0]]
    for i in range(1, n):
        g = G[i].copy(); s = M[i - 1]; g[s] = out[-1][s]; out.append(g)
    for i, g in enumerate(out): hx.save(g, od + f'/f{i:02d}', view)
    print(m, 'locked cells', [int(M[i].sum()) for i in range(n - 1)])
