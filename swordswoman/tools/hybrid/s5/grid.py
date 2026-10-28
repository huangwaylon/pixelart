"""grid.py OUT.png ZOOM names-csv rowspec... ; rowspec = label=pattern with {n} e.g. e1=snap/{n}_1x_e1.png"""
import sys, os
from PIL import Image, ImageDraw
from common import OUT
out, z, names = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(",")
rows = [r.split("=", 1) for r in sys.argv[4:]]
C = (24, 30, 112, 120); w, h = (C[2]-C[0])*z, (C[3]-C[1])*z
sh = Image.new("RGB", (60 + len(names)*(w+2), len(rows)*(h+14)), (36, 32, 44)); d = ImageDraw.Draw(sh)
for ri, (lab, pat) in enumerate(rows):
    d.text((2, ri*(h+14)+h//2), lab, fill=(230, 230, 230))
    for ci, n in enumerate(names):
        p = os.path.join(OUT, pat.format(n=n)); x, y = 60+ci*(w+2), ri*(h+14)
        if ri == 0: d.text((x+2, y), n, fill=(200, 200, 200))
        if not os.path.exists(p): continue
        im = Image.open(p).convert("RGBA")
        bg = Image.new("RGBA", (128, 128), (36, 32, 44, 255)); bg.alpha_composite(im)
        sh.paste(bg.crop(C).resize((w, h), Image.NEAREST), (x, y+12))
sh.save(out)
