"""dump.py IMG x0,y0,x1,y1 : print region as pixgrid STD chars ('.' clear, '?' unknown)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
from PIL import Image
import pixgrid as PG, hylib as H
pal = H.palette()
inv = {}
for ch, nm in PG.STD.items():
    try: inv[tuple(pal.rgba(pal.resolve(nm))[:3])] = ch
    except Exception: pass
a = np.array(Image.open(sys.argv[1]).convert("RGBA"))
x0, y0, x1, y1 = [int(v) for v in sys.argv[2].split(",")]
print("    " + "".join(str((x//10)%10) for x in range(x0, x1)))
print("    " + "".join(str(x%10) for x in range(x0, x1)))
for y in range(y0, y1):
    print(f"{y:3d} " + "".join("." if a[y, x, 3] == 0 else inv.get(tuple(a[y, x, :3]), "?") for x in range(x0, x1)))
