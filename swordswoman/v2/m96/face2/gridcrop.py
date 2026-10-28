import sys
from PIL import Image, ImageDraw
f,x0,y0,x1,y1,s,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
im=Image.open(f).convert('RGB').crop((x0,y0,x1,y1)); im=im.resize((im.width*s,im.height*s),Image.LANCZOS)
d=ImageDraw.Draw(im)
for y in range((y0//10+1)*10,y1,10):
    c=(0,160,255) if y%50 else (255,0,255); d.line([(0,(y-y0)*s),(8 if y%50 else 20,(y-y0)*s)],fill=c,width=1)
    if y%50==0: d.text((22,(y-y0)*s-6),str(y),fill=c)
for x in range((x0//10+1)*10,x1,10):
    c=(0,160,255) if x%50 else (255,0,255); d.line([((x-x0)*s,0),((x-x0)*s,8 if x%50 else 20)],fill=c,width=1)
    if x%50==0: d.text(((x-x0)*s+2,22),str(x),fill=c)
im.save(out); print(im.size)
