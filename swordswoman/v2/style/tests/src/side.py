import sys
from PIL import Image
ims=[Image.open(p).convert('RGB') for p in sys.argv[2:]]
H=max(i.height for i in ims); W=sum(i.width for i in ims)
o=Image.new('RGB',(W,H),(128,128,128)); x=0
for i in ims: o.paste(i,(x,0)); x+=i.width
o.save(sys.argv[1])
