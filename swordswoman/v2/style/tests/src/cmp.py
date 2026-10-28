import sys
from PIL import Image
a=Image.open(sys.argv[1]).convert('RGB'); refs=[Image.open(p).convert('RGB') for p in sys.argv[3:]]
H=a.height; rs=[r.resize((int(r.width*H/r.height*0.6),int(H*0.6)),Image.NEAREST) for r in refs]
W=a.width+sum(r.width for r in rs); out=Image.new('RGB',(min(W,1000),H),(128,128,128)); x=0
for im in [a]+rs: out.paste(im,(x,0)); x+=im.width
out.save(sys.argv[2])
