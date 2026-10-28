import sys
from PIL import Image
ims=[Image.open(f) for f in sys.argv[2:]]
W=max(i.width for i in ims); H=sum(i.height for i in ims); O=Image.new('RGB',(W,H)); y=0
for i in ims: O.paste(i,(0,y)); y+=i.height
O.thumbnail((1000,1000)); O.save(sys.argv[1]); print(O.size)
