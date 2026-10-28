"""Per-direction tone budgets (pixel_cleanup_guide.md R4) for one frame.
Usage: .venv/bin/python tools/pixel/tonestats.py [--anim idle] [--src clean|base] [--frame f00]"""
import argparse, json
from collections import Counter
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument("--anim", default="idle"); ap.add_argument("--src", default="clean"); ap.add_argument("--frame", default="f00")
a = ap.parse_args()
P = json.load(open("docs/palette.json"))
code = {"skin": "s", "hair": "h", "red": "r", "leather": "l", "dark": "d", "steel": "t", "eye": "e", "pink": "p", "purple": "v"}
inv = {P["outline"].lower(): "#"}
for k, v in P["ramps"].items():
    for i, c in enumerate(v): inv.setdefault(c.lower(), code[k] + str(i))
def pct(c, keys):
    n = sum(c[k] for k in keys) or 1
    return "/".join(f"{100*c[k]//n}" for k in keys)
print("dir  hair h0/h1/h2   red r0/r1/r2/r3   pink p0/p1   v0  colours   targets: h1>=50 h0<=35 h2 5-12 | r2>=45 r1<=40 r0<=5 r3 5-12 | p1>=60 | v0<=3")
for d in "S SE E NE N NW W SW".split():
    im = Image.open(f"pixel/{a.src}/{a.anim}/{d}/{a.frame}.png").convert("RGBA")
    c = Counter(inv.get("#%02x%02x%02x" % p[:3], "?") for p in im.getdata() if p[3])
    print(f"{d:<4} {pct(c,['h0','h1','h2']):>14}   {pct(c,['r0','r1','r2','r3']):>15}   {pct(c,['p0','p1']):>9}   {c['v0']:>2}  {len(c):>3}")
