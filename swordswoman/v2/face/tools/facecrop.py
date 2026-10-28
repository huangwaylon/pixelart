# facecrop.py img [w h] -> prints crop box around the topmost skin cluster (face)
import sys, colorsys
from PIL import Image
im=Image.open(sys.argv[1]).convert('RGBA'); W=int(sys.argv[2]) if len(sys.argv)>2 else 22; H=int(sys.argv[3]) if len(sys.argv)>3 else 18
pts=[]
for y in range(im.height):
    for x in range(im.width):
        r,g,b,a=im.getpixel((x,y))
        if a<128: continue
        h,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255)
        if (h<0.11) and 0.55<l<0.93 and s>0.35 and r>g>b: pts.append((x,y))
if not pts: print('0,0,%d,%d'%(W,H)); sys.exit()
ymin=min(p[1] for p in pts); top=[p for p in pts if p[1]<ymin+10]
cx=sum(p[0] for p in top)//len(top)
x0=max(0,cx-W//2); y0=max(0,ymin-5)
print(f'{x0},{y0},{x0+W},{y0+H}')
