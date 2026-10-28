"""strip.py out.png img1 img2 ... : side-by-side at equal height 700 for viewing."""
import sys
from PIL import Image
ims=[Image.open(p).convert('RGB') for p in sys.argv[2:]]
h=700; ims=[i.resize((int(i.width*h/i.height),h)) for i in ims]
S=Image.new('RGB',(sum(i.width for i in ims),h),'white'); x=0
for i in ims: S.paste(i,(x,0)); x+=i.width
S.save(sys.argv[1])
