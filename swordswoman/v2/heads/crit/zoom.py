import sys, glob
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]
S=12; W=sum(i.width*S+10 for i in ims)+sum(i.width*2+6 for i in ims); H=max(i.height*S for i in ims)+10
o=Image.new('RGB',(W,H),(60,60,60)); x=0
for i in ims:
    o.paste(i.resize((i.width*S,i.height*S),Image.NEAREST),(x,0)); x+=i.width*S+10
for i in ims:
    o.paste(i,(x,0)); o.paste(i.resize((i.width*2,i.height*2),Image.NEAREST),(x,i.height+4)); x+=i.width*2+6
o.save(sys.argv[1])
