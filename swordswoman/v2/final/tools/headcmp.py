"""headcmp.py V a.txt [b.txt ...] -> work/headcmp_V.png : illustration head (10x) | each master head (10x)"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools'); import ds,fid,numpy as np
from PIL import Image
v=sys.argv[1]; fs=sys.argv[2:]
x,m=ds.illus(v); H,W=m.shape; h=48; w=round(W*h/H); ox=(64-w)//2; top=14; s=10
big=Image.new('RGB',(640,640),'white'); big.paste(Image.fromarray(x.astype(np.uint8)).resize((w*s,h*s),Image.LANCZOS),(ox*s,top*s))
box=(16*s,12*s,48*s,35*s); c=Image.new('RGB',(320*(1+len(fs)),230),(150,150,160)); c.paste(big.crop(box),(0,0))
for i,f in enumerate(fs):
    im=ds.render(fid.load(f),s).crop(box); c.paste(im,(320*(i+1),0),im)
c.save(ds.F+f'work/headcmp_{v}.png')
