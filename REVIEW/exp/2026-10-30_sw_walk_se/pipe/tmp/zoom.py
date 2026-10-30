import sys
from PIL import Image
fs=sys.argv[2:]; out=sys.argv[1]
ims=[Image.open(f).convert('RGBA').crop((36,30,96,122)) for f in fs]
W=Image.new('RGBA',(len(ims)*62,92),(110,110,110,255))
for i,im in enumerate(ims): W.alpha_composite(im,(i*62,0))
W.resize((W.width*5,W.height*5),Image.NEAREST).save(out)
