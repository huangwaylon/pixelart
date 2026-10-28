"""pal.py: palette (pk_palette.json; n/k repurposed since the sword is gone) + char-map render helpers."""
import json
from PIL import Image
P=json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/pk_palette.json'))['colors']
PAL={k:v[0] for k,v in P.items()}
PAL['n']='#78b8f0'   # repurposed blade slot -> iris glow (bottom of the lower-iris gradient)
PAL['k']='#f8a0a0'   # repurposed katana-guard slot -> blush (soft pink, e #f87068 reads as a wound/tongue on skin)
def rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))+(255,)
def to_img(rows,z=1,bg=None):
    w=max(len(r) for r in rows); h=len(rows)
    im=Image.new('RGBA',(w,h),bg or (0,0,0,0))
    for y,r in enumerate(rows):
        for x,c in enumerate(r):
            if c in PAL: im.putpixel((x,y),rgb(PAL[c]))
    return im.resize((w*z,h*z),Image.NEAREST) if z>1 else im
