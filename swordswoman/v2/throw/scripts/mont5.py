# mont5.py RUNDIR OUT.png [ACT] : 5 views x frames montage of ones4 top rows (<=800 px wide)
import sys
from PIL import Image
d, out = sys.argv[1], sys.argv[2]; act = sys.argv[3] if len(sys.argv) > 3 else "throw"; rows = []
for v in ["S", "SE", "E", "NE", "N"]:
    im = Image.open(f"{d}/{act}_{v}/ones4.png"); im = im.crop((0, 0, im.width, im.height // 2)); k = 800 / im.width
    rows.append(im.resize((800, int(im.height * k)), Image.NEAREST))
C = Image.new("RGB", (800, sum(r.height for r in rows)), (110, 110, 110)); y = 0
for r in rows: C.paste(r, (0, y)); y += r.height
C.save(out); print(C.size)
