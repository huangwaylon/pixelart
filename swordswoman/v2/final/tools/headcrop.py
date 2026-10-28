"""headcrop.py V: work/head_V.png = illustration rows 12-34 x cols 16-48 of the 64-cell at 10x with a 1px master grid (labels every 4 = master coords)"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools')
import ds, numpy as np
from PIL import Image, ImageDraw
for v in sys.argv[1:]:
    x,m=ds.illus(v); H,W=m.shape; h=48; w=round(W*h/H); ox=(64-w)//2; top=61-h+1
    s=10; big=Image.new('RGB',(64*s,64*s),'white'); big.paste(Image.fromarray(x.astype(np.uint8)).resize((w*s,h*s),Image.LANCZOS),(ox*s,top*s))
    r0,r1,c0,c1=12,35,16,48; im=big.crop((c0*s,r0*s,c1*s,r1*s)); d=ImageDraw.Draw(im)
    for c in range(c0,c1+1):
        d.line([((c-c0)*s,0),((c-c0)*s,im.size[1] if c%4==0 else 4)],fill=(120,170,255))
        if c%4==0: d.text(((c-c0)*s+1,1),str(c),fill=(0,0,255))
    for r in range(r0,r1+1):
        d.line([(0,(r-r0)*s),(im.size[0] if r%4==0 else 4,(r-r0)*s)],fill=(120,170,255))
        if r%4==0: d.text((1,(r-r0)*s+1),str(r),fill=(0,0,255))
    im.save(ds.F+f'work/head_{v}.png'); print(v,im.size)
