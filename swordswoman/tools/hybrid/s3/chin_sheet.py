import sys, glob, os
from PIL import Image, ImageDraw
R='hybrid/S3_editchain/r1/hires'
names=sys.argv[1:]
tiles=[]
for n in names:
    im=Image.open(f'{R}/{n}.png').convert('RGB'); s=560/im.height
    im=im.resize((int(im.width*s),560)); d=ImageDraw.Draw(im)
    for y in range(0,560,20):
        Y=int(y/s); d.line([(0,y),(18 if y%100 else 40,y)],fill=(0,120,255)); 
        if y%40==0: d.text((20,y-5),str(Y),fill=(0,0,255))
    d.text((60,5),n,fill=(0,0,0)); tiles.append(im)
W=Image.new('RGB',(sum(t.width for t in tiles),560),'white');x=0
for t in tiles: W.paste(t,(x,0)); x+=t.width
W.save('/tmp/chin.png'); print(W.size)
