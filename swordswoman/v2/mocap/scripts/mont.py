# mont.py OUTDIR VIEW ACT,ACT.. DEST : stack ones4 (row 2 = matid) strips, fit 800px
import sys; from PIL import Image
o,v,acts,dest=sys.argv[1:5]; ims=[]
for a in acts.split(','):
    im=Image.open(f"{o}/{a}_{v}/ones4.png"); h=im.height//2; ims.append(im.crop((0,h,im.width,im.height)))
W=max(i.width for i in ims); H=sum(i.height for i in ims); c=Image.new('RGB',(W,H),(110,110,110)); y=0
for i in ims: c.paste(i,(0,y)); y+=i.height
c.thumbnail((800,800)); c.save(dest); print(c.size)
