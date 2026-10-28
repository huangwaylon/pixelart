"""Print a region of a frame as palette codes (#=outline, s0..s2, h0..h2, r0..r3, l1 l2, d1, t0..t2, e0 e1, p0 p1, v0, .=clear).
Usage: .venv/bin/python tools/pixel/asciidump.py DIR x0 y0 x1 y1 [fNN] [base|clean]   (idle anim; run from project root)"""
import json,sys
from PIL import Image
P=json.load(open("docs/palette.json"))
names={}
names[P["outline"].lower()]="#"
code={"skin":"s","hair":"h","red":"r","leather":"l","dark":"d","steel":"t","eye":"e","pink":"p","purple":"v"}
for k,v in P["ramps"].items():
    for i,c in enumerate(v):
        c=c.lower()
        if c not in names: names[c]=code[k]+str(i)
d,x0,y0,x1,y1=sys.argv[1],*map(int,sys.argv[2:6])
f=sys.argv[6] if len(sys.argv)>6 else "f00"
src=sys.argv[7] if len(sys.argv)>7 else "base"
im=Image.open(f"pixel/{src}/idle/{d}/{f}.png").convert("RGBA")
print("    "+"".join(f"{x%100:>3}" for x in range(x0,x1)))
for y in range(y0,y1):
    row=[]
    for x in range(x0,x1):
        r,g,b,a=im.getpixel((x,y))
        row.append(" ." if a==0 else names.get(f"#{r:02x}{g:02x}{b:02x}","??").rjust(2))
    print(f"{y:>3} "+" ".join(row))
