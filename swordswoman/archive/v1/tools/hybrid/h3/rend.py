"""render cels / frames: rend.py OUT_DIR name [name...]  (name = cel module -> turn png + x8 zoom)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from common import save, zoom, crop_box, strip
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
ims = []
for n in sys.argv[2:]:
    a, info = kit.render(dict(base=n))
    save(a, f'{out}/{n}.png'); ims.append(a[30:110, 34:94])
strip(ims, z=8, labels=sys.argv[2:], grid=False).save(f'{out}/_view.png')
