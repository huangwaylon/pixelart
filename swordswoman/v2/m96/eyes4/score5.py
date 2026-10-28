# score5.py "cc=ch ..." : per-view face_ssim with joint5 edits (SE far inner h included); cells given as 'CR=ch' tokens
import sys
src = open('eyes4/joint6.py').read().split('combos = []')[0]; ns = {}; exec(src, ns)
for spec in sys.argv[1:]:
    cells = {(int(t[0]), int(t[1])): t[3] for t in spec.split()}
    print(spec, {v: round(ns['score'](v, cells), 4) for v in ('S', 'SE', 'E')})
