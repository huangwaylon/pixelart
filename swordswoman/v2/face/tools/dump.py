# dump.py img x0 y0 x1 y1 : print region as chars: K black, W white, s skin, S skin shadow, b blue/iris-ish, c other dark, . transparent, letters for others
import sys, colorsys
from PIL import Image
im=Image.open(sys.argv[1]).convert('RGBA'); x0,y0,x1,y1=map(int,sys.argv[2:6])
pal={}; 
def cls(p):
    r,g,b,a=p
    if a<128: return '.'
    if r<40 and g<40 and b<40: return 'K'
    if r>230 and g>230 and b>230: return 'W'
    h,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255)
    if (h<0.12 or h>0.95) and l>0.75: return 's'
    if (h<0.1 or h>0.95) and l>0.55 and s>0.3: return 'S'
    return None
leg={}
for y in range(y0,y1):
    row=''
    for x in range(x0,x1):
        p=im.getpixel((x,y)); c=cls(p)
        if c is None:
            key=p[:3]
            if key not in leg: leg[key]='abcdefghijmnopqrtuvwxyz0123456789ABCDEFGHIJLMNOPQRTUVXYZ'[len(leg)]
            c=leg[key]
        row+=c
    print(f'{y:3d} '+row)
print(' '.join(f'{v}=#{k[0]:02x}{k[1]:02x}{k[2]:02x}' for k,v in leg.items()))
