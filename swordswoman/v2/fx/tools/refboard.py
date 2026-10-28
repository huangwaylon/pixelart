import sys,glob,os
from PIL import Image
d=sys.argv[1]; out=sys.argv[2]; s=3
fs=sorted(glob.glob(d+'/*.png')); ims=[]
for f in fs:
    im=Image.open(f).convert('RGBA'); ims.append((os.path.basename(f),im))
W=1000; x=y=0; rowh=0; pos=[]
for n,im in ims:
    w,h=im.width*s,im.height*s
    if h>300: im=im.crop((0,0,im.width,100)); w,h=im.width*s,im.height*s
    if x+w>W: x=0; y+=rowh+6; rowh=0
    pos.append((n,im,x,y)); x+=w+6; rowh=max(rowh,h)
B=Image.new('RGB',(W,y+rowh),(110,110,110))
for n,im,x,y in pos: B.paste(im.resize((im.width*s,im.height*s),Image.NEAREST),(x,y),im.resize((im.width*s,im.height*s),Image.NEAREST))
B.save(out); print(B.size)
