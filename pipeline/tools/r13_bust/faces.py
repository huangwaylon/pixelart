import sys
from PIL import Image
from pipeline import pixgrid
names=sys.argv[2:]; out=sys.argv[1]
ims=[]
for n in names:
    img,_=pixgrid.load(f'art/hand/S4/bust/{n}.pix')
    ims.append(pixgrid.to_image(img[18:58,18:72],6,'#DFEAF6'))
W=Image.new('RGBA',(sum(i.width+6 for i in ims),ims[0].height),(36,22,40,255))
x=0
for i in ims: W.paste(i,(x,0)); x+=i.width+6
W.save(out)
