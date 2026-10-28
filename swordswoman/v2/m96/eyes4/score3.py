# score3.py KEY : per-view face_ssim for a joint.py cell key (n0 g1 c1 g2 g3 g4 c4 e4)
import sys; sys.argv += []
import importlib.util
spec = importlib.util.spec_from_file_location('j', 'eyes4/joint2.py')
src = open('eyes4/joint2.py').read().split('combos = []')[0]; ns = {}; exec(src, ns)
K = [(0, 1), (0, 3), (0, 4), (1, 1), (4, 1), (4, 2)]
for key in sys.argv[1:]:
    cells = dict(zip(K, key)); print(key, {v: round(ns['score'](v, cells), 4) for v in ('S', 'SE', 'E')})
