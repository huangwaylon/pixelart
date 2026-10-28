import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plib, passes as P
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
BACK = ('turn_N', 'turn_NW', 'turn_NE')
for f in sorted(os.listdir(src)):
    if not plib.H.is_sprite_name(f):
        continue
    g = plib.load(os.path.join(src, f)); log = []
    P.blade_clean(g, log); P.despeckle(g, log); P.red_mode(g, log)
    P.hair_shade(g, log, ymax=82, tJ=0.45, tH=0.52)
    P.lint_clean(g, log)
    if not f.startswith(BACK):
        P.corset_dress(g, log)
    plib.save(g, os.path.join(out, f))
    print(f, len(log))
